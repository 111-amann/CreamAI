"""
tests/test_day9.py - Comprehensive Test Suite for Day 9:
1. Version Tool (stdlib_version_check)
2. Handwritten Agent Loop (run_agent_loop)
3. LangGraph Workflow (run_langgraph_agent, resume_langgraph_agent)
4. FastAPI Endpoints (/agent, /health, /ask regression)
"""

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

# Set offline environment variables
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from fastapi.testclient import TestClient
from langgraph.checkpoint.memory import MemorySaver

from app.agent_loop import run_agent_loop
from app.graph import (
    agent_graph,
    build_agent_graph,
    resume_langgraph_agent,
    run_langgraph_agent,
)
from app.main import app
from app.tools import StdlibVersionChecker, stdlib_version_check


# =====================================================================
# 1. Version Tool Tests
# =====================================================================

class TestVersionTool(unittest.TestCase):
    def setUp(self):
        self.checker = StdlibVersionChecker()

    def test_exact_symbol_match(self):
        res = self.checker.check("pathlib.Path.mkdir", "3.8")
        self.assertEqual(res["status"], "available")
        self.assertTrue(res["available"])
        self.assertEqual(res["symbol"], "pathlib.Path.mkdir")
        self.assertEqual(res["introduced_in"], "3.4")

    def test_unknown_symbol(self):
        res = self.checker.check("math.quantum_teleportation", "3.15")
        self.assertEqual(res["status"], "unknown")
        self.assertFalse(res["available"])
        self.assertIn("No documentation version records found", res["message"])

    def test_introduced_after_requested_version(self):
        # functools.cache added in 3.9, checking 3.8
        res = self.checker.check("functools.cache", "3.8")
        self.assertEqual(res["status"], "not_yet_available")
        self.assertFalse(res["available"])
        self.assertEqual(res["introduced_in"], "3.9")

    def test_deprecated_by_requested_version(self):
        # pathlib.Path.is_reserved deprecated in 3.13, removed in 3.15
        res = self.checker.check("pathlib.Path.is_reserved", "3.13")
        self.assertEqual(res["status"], "deprecated")
        self.assertTrue(res["available"])
        self.assertEqual(res["deprecated_in"], "3.13")
        self.assertEqual(res["removed_in"], "3.15")

    def test_removed_by_requested_version(self):
        # pathlib.Path.is_reserved removed in 3.15
        res = self.checker.check("pathlib.Path.is_reserved", "3.15")
        self.assertEqual(res["status"], "removed")
        self.assertFalse(res["available"])
        self.assertEqual(res["removed_in"], "3.15")

    def test_removed_after_requested_version(self):
        # pathlib.Path.is_reserved in 3.12 (deprecated in 3.13, removed in 3.15)
        res = self.checker.check("pathlib.Path.is_reserved", "3.12")
        self.assertEqual(res["status"], "available")
        self.assertTrue(res["available"])
        self.assertEqual(res["deprecated_in"], "3.13")
        self.assertEqual(res["removed_in"], "3.15")

    def test_multiple_version_events_and_changes(self):
        # pathlib.Path.mkdir: exist_ok in 3.5, parent_mode in 3.15
        res = self.checker.check("pathlib.Path.mkdir", "3.15")
        self.assertEqual(res["status"], "available")
        self.assertTrue(res["available"])
        self.assertTrue(len(res["relevant_changes"]) > 0)
        self.assertTrue(any("parent_mode" in c for c in res["relevant_changes"]))

    def test_missing_or_malformed_version_data(self):
        res = self.checker.check("functools.cache", "invalid.version.foo")
        self.assertIn(res["status"], ("unknown", "not_yet_available"))


# =====================================================================
# 2. Handwritten Agent Loop Tests
# =====================================================================

class TestHandwrittenAgent(unittest.TestCase):
    def test_compatibility_only_question(self):
        def mock_llm(sys_prompt, usr_prompt):
            if "Current Iteration: 1" in usr_prompt:
                return '{"action": "call_tool", "tool": "stdlib_version_check", "args": {"symbol": "functools.cache", "python_version": "3.8"}}'
            return '{"action": "final_response", "answer": "functools.cache was added in 3.9 and was not available in 3.8.", "status": "completed"}'

        res = run_agent_loop("Is functools.cache in Python 3.8?", custom_llm_generator=mock_llm)
        self.assertEqual(res["status"], "completed")
        self.assertEqual(len(res["tool_calls"]), 1)
        self.assertEqual(res["tool_calls"][0]["tool"], "stdlib_version_check")
        self.assertTrue(len(res["citations"]) > 0)

    def test_rag_only_question(self):
        def mock_llm(sys_prompt, usr_prompt):
            if "Current Iteration: 1" in usr_prompt:
                return '{"action": "call_tool", "tool": "rag_search", "args": {"query": "pathlib Path read_text"}}'
            return '{"action": "final_response", "answer": "Path.read_text decodes and returns file content.", "status": "completed"}'

        with patch("app.agent_loop.hybrid_search", return_value=[
            {"text": "read_text() returns string", "metadata": {"source": "library/pathlib.txt", "title": "Pathlib", "section": "Path.read_text", "page": "1"}}
        ]):
            res = run_agent_loop("How does Path.read_text work?", custom_llm_generator=mock_llm)
            self.assertEqual(res["status"], "completed")
            self.assertEqual(len(res["tool_calls"]), 1)
            self.assertEqual(res["tool_calls"][0]["tool"], "rag_search")
            self.assertEqual(len(res["citations"]), 1)

    def test_question_requiring_both_tools(self):
        def mock_llm(sys_prompt, usr_prompt):
            if "Current Iteration: 1" in usr_prompt:
                return '{"action": "call_tool", "tool": "rag_search", "args": {"query": "functools.cache"}}'
            elif "Current Iteration: 2" in usr_prompt:
                return '{"action": "call_tool", "tool": "stdlib_version_check", "args": {"symbol": "functools.cache", "python_version": "3.8"}}'
            return '{"action": "final_response", "answer": "functools.cache is an unbounded memoization decorator introduced in 3.9, so not available in 3.8.", "status": "completed"}'

        with patch("app.agent_loop.hybrid_search", return_value=[
            {"text": "cache is an unbounded function cache", "metadata": {"source": "library/functools.txt", "title": "Functools", "section": "cache", "page": "1"}}
        ]):
            res = run_agent_loop("Explain functools.cache and check if available in 3.8", custom_llm_generator=mock_llm)
            self.assertEqual(res["status"], "completed")
            self.assertEqual(len(res["tool_calls"]), 2)
            tools_called = [t["tool"] for t in res["tool_calls"]]
            self.assertIn("rag_search", tools_called)
            self.assertIn("stdlib_version_check", tools_called)

    def test_unknown_tool_request(self):
        def mock_llm(sys_prompt, usr_prompt):
            if "Current Iteration: 1" in usr_prompt:
                return '{"action": "call_tool", "tool": "arbitrary_eval_tool", "args": {"code": "print(1)"}}'
            return '{"action": "final_response", "answer": "Recovered from unknown tool.", "status": "completed"}'

        res = run_agent_loop("Run some code", custom_llm_generator=mock_llm)
        self.assertEqual(res["status"], "completed")
        self.assertIn("not found", res["tool_calls"][0]["result"])

    def test_invalid_tool_arguments(self):
        def mock_llm(sys_prompt, usr_prompt):
            if "Current Iteration: 1" in usr_prompt:
                return '{"action": "call_tool", "tool": "stdlib_version_check", "args": {"symbol": "math.sqrt"}}'
            return '{"action": "final_response", "answer": "Recovered from missing arg.", "status": "completed"}'

        res = run_agent_loop("Check math.sqrt", custom_llm_generator=mock_llm)
        self.assertEqual(res["status"], "completed")
        self.assertIn("Missing required arguments", res["tool_calls"][0]["result"])

    def test_maximum_tool_call_limit(self):
        def mock_loop_llm(sys_prompt, usr_prompt):
            return '{"action": "call_tool", "tool": "stdlib_version_check", "args": {"symbol": "math.sqrt", "python_version": "3.8"}}'

        res = run_agent_loop("Infinite loop test", max_iterations=3, custom_llm_generator=mock_loop_llm)
        self.assertLessEqual(len(res["tool_calls"]), 3)


# =====================================================================
# 3. LangGraph Workflow Tests
# =====================================================================

class TestLangGraphAgent(unittest.TestCase):
    def setUp(self):
        self.test_graph = build_agent_graph(checkpointer=MemorySaver())

    def test_routing_and_tool_execution(self):
        def mock_llm(sys_prompt, usr_prompt):
            if "Current Iteration: 1" in usr_prompt:
                return '{"action": "call_tool", "tool": "stdlib_version_check", "args": {"symbol": "os.path.isreserved", "python_version": "3.13"}}'
            return '{"action": "final_response", "answer": "os.path.isreserved was added in Python 3.13."}'

        res = run_langgraph_agent(
            message="Check os.path.isreserved in 3.13",
            thread_id="test-routing",
            graph=self.test_graph,
            llm_generator=mock_llm,
        )
        self.assertEqual(res["status"], "approval_required")
        self.assertTrue(res["approval_required"])
        self.assertEqual(len(res["tool_calls"]), 1)
        self.assertEqual(res["tool_calls"][0]["tool"], "stdlib_version_check")
        self.assertIn("os.path.isreserved", res["proposed_response"])

    def test_conversation_memory_and_thread_isolation(self):
        def mock_llm(sys_prompt, usr_prompt):
            import json
            return json.dumps({"action": "final_response", "answer": "Response for: " + usr_prompt[:30]})

        # Thread A
        run_langgraph_agent("Question from Thread A", thread_id="thread-A", graph=self.test_graph, llm_generator=mock_llm)
        # Thread B
        run_langgraph_agent("Question from Thread B", thread_id="thread-B", graph=self.test_graph, llm_generator=mock_llm)

        state_a = self.test_graph.get_state({"configurable": {"thread_id": "thread-A"}})
        state_b = self.test_graph.get_state({"configurable": {"thread_id": "thread-B"}})

        self.assertEqual(state_a.values["question"], "Question from Thread A")
        self.assertEqual(state_b.values["question"], "Question from Thread B")

    def test_interruption_approval_and_rejection(self):
        def mock_llm(sys_prompt, usr_prompt):
            return '{"action": "final_response", "answer": "Proposed documentation answer."}'

        # Start thread
        t_id = "test-approval-flow"
        start_res = run_langgraph_agent("Explain Counter", thread_id=t_id, graph=self.test_graph, llm_generator=mock_llm)
        self.assertEqual(start_res["status"], "approval_required")
        self.assertTrue(start_res["approval_required"])

        # Test Resume with APPROVAL
        res_approved = resume_langgraph_agent(thread_id=t_id, approved=True, graph=self.test_graph)
        self.assertEqual(res_approved["status"], "completed")
        self.assertFalse(res_approved["approval_required"])
        self.assertEqual(res_approved["response"], "Proposed documentation answer.")

        # Start another thread and test REJECTION
        t_rej = "test-rejection-flow"
        run_langgraph_agent("Delete docs", thread_id=t_rej, graph=self.test_graph, llm_generator=mock_llm)
        res_rejected = resume_langgraph_agent(thread_id=t_rej, approved=False, graph=self.test_graph)
        self.assertEqual(res_rejected["status"], "rejected")
        self.assertFalse(res_rejected["approval_required"])
        self.assertIn("rejected by the user", res_rejected["response"].lower())
        self.assertNotEqual(res_rejected["response"], "Proposed documentation answer.")


# =====================================================================
# 4. FastAPI API Tests
# =====================================================================

class TestAgentAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_health_check(self):
        res = self.client.get("/health")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["status"], "healthy")

    def test_agent_endpoint_start_approval_and_resume(self):
        mock_output = '{"action": "final_response", "answer": "Mocked proposed answer."}'

        with patch("app.graph.generate_response", return_value=mock_output):
            # 1. Start new conversation
            res = self.client.post("/agent", json={"message": "What is pathlib.Path?"})
            self.assertEqual(res.status_code, 200)
            data = res.json()
            self.assertEqual(data["status"], "approval_required")
            self.assertTrue(data["approval_required"])
            self.assertEqual(data["proposed_response"], "Mocked proposed answer.")
            thread_id = data["thread_id"]

            # 2. Resume with approval
            res_approve = self.client.post("/agent", json={"thread_id": thread_id, "approved": True})
            self.assertEqual(res_approve.status_code, 200)
            data_app = res_approve.json()
            self.assertEqual(data_app["status"], "completed")
            self.assertEqual(data_app["response"], "Mocked proposed answer.")

    def test_agent_endpoint_rejection(self):
        mock_output = '{"action": "final_response", "answer": "Proposed dangerous operation."}'

        with patch("app.graph.generate_response", return_value=mock_output):
            res = self.client.post("/agent", json={"message": "Remove file"})
            self.assertEqual(res.status_code, 200)
            thread_id = res.json()["thread_id"]

            # Resume with rejection
            res_rej = self.client.post("/agent", json={"thread_id": thread_id, "approved": False})
            self.assertEqual(res_rej.status_code, 200)
            data_rej = res_rej.json()
            self.assertEqual(data_rej["status"], "rejected")
            self.assertIn("rejected by the user", data_rej["response"].lower())

    def test_agent_endpoint_empty_message_validation(self):
        res = self.client.post("/agent", json={"message": "   "})
        self.assertEqual(res.status_code, 400)
        self.assertIn("empty", res.json()["detail"].lower())

    def test_agent_endpoint_llm_json_parsing_error_returns_500(self):
        # Invalid JSON returned by LLM must return HTTP 500, never an HTTP 200 with error masked in approval
        invalid_json_output = "This is not valid JSON at all and cannot be parsed."

        with patch("app.graph.generate_response", return_value=invalid_json_output):
            res = self.client.post("/agent", json={"message": "What is pathlib.Path?"})
            self.assertEqual(res.status_code, 500)
            data = res.json()
            self.assertIn("failed", data["detail"].lower())

    def test_ask_regression(self):
        # Empty question validation
        res = self.client.post("/ask", json={"question": "   "})
        self.assertEqual(res.status_code, 400)

        # Answered regression with mocks for LLM and retrieval
        mock_rag = '{"status": "answered", "answer": "Mocked RAG response for pathlib.Path.", "citation_indices": [1]}'
        mock_chunks = [
            {
                "text": "Pathlib documentation",
                "metadata": {
                    "source": "library/pathlib.txt",
                    "title": "pathlib",
                    "section": "Path",
                    "page": "1",
                },
            }
        ]
        with patch("app.rag.generate_response", return_value=mock_rag), \
             patch("app.rag.hybrid_search", return_value=mock_chunks):
            res = self.client.post("/ask", json={"question": "What is pathlib.Path?", "top_k": 3})
            self.assertEqual(res.status_code, 200)
            data = res.json()
            self.assertEqual(data["status"], "answered")
            self.assertTrue(len(data["citations"]) > 0)
            self.assertIn("compatibility", data)


if __name__ == "__main__":
    unittest.main()
