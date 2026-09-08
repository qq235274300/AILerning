"""正式 API 的离线回归：真实 Graph/ToolNode，模型与工具 I/O 使用替身。"""
import json
import socket
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage
from langgraph.checkpoint.memory import InMemorySaver
import main
from Agent.graph import nodes, service, workflow
from Agent.graph.crash import nodes as crash_nodes
from Agent.tools import local_tools
from Agent.schemas import DraftAnswer, RequestAnalysis, PatchSuggestion, ReviewResult


class AgentApiTests(unittest.TestCase):
    def setUp(self):
        self.addCleanup(patch.stopall)
        original_connect = socket.socket.connect

        def local_connect(sock, address):
            # Windows 的 asyncio socketpair 需要回环连接，外部网络仍被禁止。
            if isinstance(address, tuple) and address[0] in {"127.0.0.1", "::1"}:
                return original_connect(sock, address)
            raise AssertionError("External network forbidden")

        patch("socket.socket.connect", new=local_connect).start()
        self.planner = patch.object(nodes, "analyze_request", return_value=RequestAnalysis(
            task_type="general", needs_file_context=False,
            needs_logs_context=False, needs_rag_context=False,
        )).start()
        patch.object(nodes, "generate_suggestion", return_value=DraftAnswer(answer="answer")).start()
        self.tool_model = patch.object(workflow, "tool_model_node", side_effect=[
            {"messages": [AIMessage(content="", tool_calls=[{
                "name": "read_file", "args": {"path": "test.py"}, "id": "read-1"
            }])]},
            {"messages": [AIMessage(content="上下文收集完成")]},
        ]).start()
        self.read = patch.object(local_tools, "project_read_file", return_value={
            "path": "test.py", "content": "x = 0"
        }).start()
        patch.object(nodes, "propose_patch", return_value=PatchSuggestion(
            file_path="test.py", issue_location="1", issue_summary="test", reason="test",
            old_code="x = 0", new_code="x = 1", patch_diff="-x = 0\n+x = 1", risk="test",
        )).start()
        patch.object(nodes, "review_answer", return_value=ReviewResult(
            passed=True, final_answer="reviewed", issues=[],
        )).start()
        patch.object(workflow, "checkpointer", InMemorySaver()).start()
        patch.object(service, "agent_graph", workflow.build_agent_graph()).start()
        self.client = TestClient(main.app)
        self.addCleanup(self.client.close)

    def events(self, response):
        self.assertEqual(response.status_code, 200)
        return [json.loads(line) for line in response.text.splitlines()]

    def test_sync_stream_aliases_and_memory(self):
        for url in ("/agent", "/agent/graph"):
            response = self.client.post(url, json={"question": "hello", "thread_id": "A"})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["final_answer"], "answer")
        for url in ("/agent/stream", "/agent/graph/stream"):
            events = self.events(self.client.post(url, json={"question": "hello", "thread_id": "A"}))
            self.assertEqual(events[-1]["event"], "final")
        snapshot = service.agent_graph.get_state(service.build_graph_config("A"))
        self.assertEqual(len(snapshot.values["messages"]), 8)
        self.tool_model.assert_not_called()
        self.assertEqual(self.client.post("/agent", json={"question": "hello"}).status_code, 422)

    def test_real_tool_loop_and_approval(self):
        self.planner.return_value = RequestAnalysis(
            task_type="code_analysis", needs_file_context=True,
            needs_logs_context=False, needs_rag_context=False, needs_review=True,
        )
        events = self.events(self.client.post("/agent/stream", json={
            "question": "analyze test.py", "thread_id": "patch"
        }))
        self.assertEqual(events[-1]["event"], "approval_required")
        self.assertIn("tools_done", [item["event"] for item in events])
        self.read.assert_called_once_with("test.py")
        snapshot = service.agent_graph.get_state(service.build_graph_config("patch"))
        self.assertEqual(snapshot.values["context"].files[0]["content"], "x = 0")
        events = self.events(self.client.post("/agent/resume", json={
            "thread_id": "patch", "decision": "approve"
        }))
        self.assertEqual(events[-1]["data"]["final_answer"], "reviewed")
        events = self.events(self.client.post("/agent/graph/resume", json={
            "thread_id": "patch", "decision": "approve"
        }))
        self.assertEqual(events[-1]["event"], "resume_error")

    def test_crash_endpoint_uses_subgraph(self):
        with patch.object(crash_nodes, "read_log", return_value={"error": "not found"}), \
             patch.object(crash_nodes, "extract_error_summary") as extract:
            response = self.client.post("/crash", json={"path": "missing.log"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["summary"], "not found")
        extract.assert_not_called()
        self.planner.assert_not_called()


if __name__ == "__main__":
    unittest.main()
