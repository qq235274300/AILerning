"""使用真实 Graph 和 Checkpointer，替换所有模型节点，禁止网络连接。"""
import json
import unittest
from unittest.mock import patch

from langchain_core.messages import AIMessage
from langgraph.checkpoint.memory import InMemorySaver
from Agent.graph import nodes, service, workflow
from Agent.schemas import DraftAnswer, PatchSuggestion, RequestAnalysis, ReviewResult
from models import PatchApprovalRequest


class ApprovalTests(unittest.TestCase):
    def setUp(self):
        self.addCleanup(patch.stopall)
        patch("socket.socket.connect", side_effect=AssertionError("Network forbidden")).start()
        analysis = RequestAnalysis(
            task_type="code_analysis", needs_file_context=True,
            needs_logs_context=False, needs_rag_context=False, needs_review=True,
        )
        patch.object(nodes, "analyze_request", return_value=analysis).start()
        patch.object(nodes, "generate_suggestion", return_value=DraftAnswer(answer="draft")).start()
        self.patcher = patch.object(nodes, "propose_patch", return_value=PatchSuggestion(
            file_path="example.py", issue_location="line 1", issue_summary="test",
            reason="test", old_code="x = 0", new_code="x = 1",
            patch_diff="-x = 0\n+x = 1", risk="test", needs_human_confirm=True,
        )).start()
        self.reviewer = patch.object(nodes, "review_answer", return_value=ReviewResult(
            passed=True, issues=[], final_answer="reviewed"
        )).start()
        patch.object(workflow, "tool_model_node", lambda state: {
            "messages": [AIMessage(content="上下文收集完成")]
        }).start()
        patch.object(workflow, "checkpointer", InMemorySaver()).start()
        patch.object(service, "agent_graph", workflow.build_agent_graph()).start()

    def events(self, stream):
        return [json.loads(line) for line in stream]

    def test_approve_and_duplicate_resume(self):
        events = self.events(service.run_agent_graph_stream("test", "A"))
        self.assertEqual(events[-1]["event"], "approval_required")
        self.assertFalse(any(e["event"] == "final" for e in events))
        self.reviewer.assert_not_called()
        # 新问题不能覆盖待审批任务。
        blocked = self.events(service.run_agent_graph_stream("overwrite", "A"))
        self.assertEqual(blocked[0]["event"], "approval_required")
        result = self.events(service.resume_agent_graph_stream("A", "approve", "ok"))
        self.assertEqual(result[-1]["data"]["approval_status"], "approved")
        self.assertEqual(result[-1]["data"]["final_answer"], "reviewed")
        self.patcher.assert_called_once()
        self.reviewer.assert_called_once()
        duplicate = self.events(service.resume_agent_graph_stream("A", "approve"))
        self.assertEqual([e["event"] for e in duplicate], ["resume_error"])

    def test_sync_pause_reject_and_wrong_thread(self):
        result = service.run_agent_graph("test", "B")
        self.assertEqual(result["status"], "approval_required")
        self.assertTrue(result["interrupts"])
        wrong = self.events(service.resume_agent_graph_stream("unknown", "reject"))
        self.assertEqual(wrong[0]["event"], "resume_error")
        result = self.events(service.resume_agent_graph_stream("B", "reject", "no"))
        self.assertEqual(result[-1]["data"]["approval_status"], "rejected")
        self.assertIn("拒绝", result[-1]["data"]["final_answer"])
        self.reviewer.assert_not_called()

    def test_request_contract(self):
        self.assertEqual(PatchApprovalRequest(thread_id="A", decision="approve").decision, "approve")


if __name__ == "__main__":
    unittest.main()
