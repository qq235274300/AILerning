"""使用真实父子图，替换付费调用并禁止网络连接。"""
import json
import unittest
from unittest.mock import patch

from langgraph.checkpoint.memory import InMemorySaver
from Agent.crash_analyzer import ErrorSummary
from Agent.graph import nodes, service, workflow
from Agent.graph.crash import nodes as crash_nodes
from Agent.graph.crash.workflow import crash_graph
from Agent.schemas import CrashReport, DraftAnswer, RequestAnalysis


class CrashGraphTests(unittest.TestCase):
    def setUp(self):
        self.addCleanup(patch.stopall)
        patch("socket.socket.connect", side_effect=AssertionError("Network forbidden")).start()
        self.read = patch.object(crash_nodes, "read_log", return_value={
            "content": "Fatal error: access violation"
        }).start()
        self.extract = patch.object(crash_nodes, "extract_error_summary", return_value=ErrorSummary(
            crash_type="access_violation", error_message="access violation",
            keywords=["UObject", "nullptr"],
        )).start()
        self.search = patch.object(crash_nodes, "search_ue_docs", return_value=[]).start()
        self.report = patch.object(crash_nodes, "generate_crash_report", return_value=CrashReport(
            crash_type="access_violation", summary="test crash", error_message="access violation"
        )).start()
        self.planner = patch.object(nodes, "analyze_request", return_value=RequestAnalysis(
            task_type="crash_analysis", needs_file_context=True, needs_logs_context=True,
            needs_rag_context=True, needs_review=True, file_paths=["test.log"],
        )).start()
        self.writer = patch.object(nodes, "generate_suggestion", return_value=DraftAnswer(answer="hello")).start()
        self.patcher = patch.object(nodes, "propose_patch", side_effect=AssertionError("Unexpected patch")).start()
        patch.object(workflow, "checkpointer", InMemorySaver()).start()
        patch.object(service, "agent_graph", workflow.build_agent_graph()).start()

    def test_stream_and_next_turn(self):
        events = [json.loads(line) for line in service.run_agent_graph_stream("crash", "A")]
        self.assertEqual([e["event"] for e in events], [
            "graph_start", "planner_done", "crash_analysis_done", "final_done", "final"
        ])
        self.assertEqual(events[-1]["data"]["crash_report"]["summary"], "test crash")
        self.search.assert_called_once_with("UObject nullptr")
        self.writer.assert_not_called()
        self.patcher.assert_not_called()
        # 同一会话转为普通问题后，报告被清空，但消息历史仍然保留。
        self.planner.return_value = RequestAnalysis(
            task_type="general", needs_file_context=False,
            needs_logs_context=False, needs_rag_context=False,
        )
        result = service.run_agent_graph("hello", "A")
        self.assertIsNone(result["crash_report"])
        self.assertEqual(result["final_answer"], "hello")
        snapshot = service.agent_graph.get_state(service.build_graph_config("A"))
        self.assertEqual(len(snapshot.values["messages"]), 4)

    def test_read_failures_skip_paid_calls(self):
        for result in ({"error": "not found"}, {"content": "  "}):
            with self.subTest(result=result):
                self.read.return_value = result
                output = crash_graph.invoke({"log_path": "missing.log"})
                self.assertEqual(output["report"].crash_type, "unknown")
        self.read.side_effect = ValueError("outside root")
        self.assertEqual(crash_graph.invoke({"log_path": "../outside.log"})["report"].summary, "outside root")
        self.extract.assert_not_called()
        self.search.assert_not_called()
        self.report.assert_not_called()

    def test_ambiguous_paths_skip_subgraph(self):
        for paths in ([], ["a.log", "b.log"], ["a.py"]):
            self.planner.return_value.file_paths = paths
            result = service.run_agent_graph("crash", "B")
            self.assertEqual(result["crash_report"]["crash_type"], "unknown")
        self.read.assert_not_called()

    def test_query_fallback(self):
        self.extract.return_value.keywords = []
        crash_graph.invoke({"log_path": "test.log"})
        self.search.assert_called_once_with("access violation")


if __name__ == "__main__":
    unittest.main()
