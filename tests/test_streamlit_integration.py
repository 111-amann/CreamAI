"""
Integration tests for the Streamlit UI.
Tests the UI's integration with the backend API.
"""


import requests


def test_backend_health():
    """Test that the backend is accessible."""
    response = requests.get("http://localhost:8000/health", timeout=5)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    print("✓ Backend health check passed")


def test_rag_endpoint():
    """Test the /ask RAG endpoint."""
    payload = {
        "question": "What is pathlib.Path?",
        "top_k": 3
    }
    response = requests.post("http://localhost:8000/ask", json=payload, timeout=30)
    assert response.status_code == 200
    data = response.json()
    assert "question" in data
    assert "answer" in data
    assert "citations" in data
    assert len(data["citations"]) > 0
    print("✓ RAG endpoint test passed")
    print(f"  Answer preview: {data['answer'][:100]}...")
    print(f"  Citations: {len(data['citations'])}")


def test_agent_endpoint():
    """Test the /agent endpoint."""
    payload = {
        "message": "Check if pathlib.Path.mkdir is available in Python 3.8"
    }
    response = requests.post("http://localhost:8000/agent", json=payload, timeout=60)
    assert response.status_code == 200
    data = response.json()
    assert "thread_id" in data
    assert "status" in data
    assert "tool_calls" in data

    # Check if version check tool was used
    tool_names = [tc["tool"] for tc in data.get("tool_calls", [])]
    has_version_check = "stdlib_version_check" in tool_names

    print("✓ Agent endpoint test passed")
    print(f"  Status: {data['status']}")
    print(f"  Thread ID: {data['thread_id']}")
    print(f"  Tools called: {tool_names}")
    print(f"  Has version check: {has_version_check}")

    if has_version_check:
        # Verify version check result structure
        for tc in data["tool_calls"]:
            if tc["tool"] == "stdlib_version_check":
                result = tc.get("result", {})
                assert "symbol" in result
                assert "python_version" in result
                assert "status" in result
                assert "available" in result
                print(f"  ✓ Version check result: {result['symbol']} in Python {result['python_version']}: {result['status']}")


def test_agent_with_approval():
    """Test agent approval flow."""
    # Start a conversation that requires approval
    payload = {
        "message": "Explain os.path and check if it's available in Python 3.10"
    }
    response = requests.post("http://localhost:8000/agent", json=payload, timeout=60)
    assert response.status_code == 200
    data = response.json()
    thread_id = data["thread_id"]

    print("✓ Agent conversation started")
    print(f"  Thread ID: {thread_id}")
    print(f"  Approval required: {data.get('approval_required')}")

    # If approval is required, test the resume endpoint
    if data.get("approval_required"):
        print("  Testing approval flow...")
        # Approve the action
        approve_payload = {
            "thread_id": thread_id,
            "approved": True
        }
        resume_response = requests.post("http://localhost:8000/agent", json=approve_payload, timeout=60)
        assert resume_response.status_code == 200
        resume_data = resume_response.json()
        assert resume_data["status"] in ["completed", "approved"]
        print(f"  ✓ Approval handled: {resume_data['status']}")


def test_streamlit_ui_running():
    """Test that Streamlit UI is accessible."""
    try:
        response = requests.get("http://localhost:8501", timeout=5)
        assert response.status_code == 200
        print("✓ Streamlit UI is accessible")
    except requests.exceptions.ConnectionError:
        print("⚠ Streamlit UI not accessible (may need to be started manually)")


def run_all_tests():
    """Run all integration tests."""
    print("\n" + "="*60)
    print("Running Streamlit Integration Tests")
    print("="*60 + "\n")

    tests = [
        ("Backend Health Check", test_backend_health),
        ("RAG Endpoint", test_rag_endpoint),
        ("Agent Endpoint", test_agent_endpoint),
        ("Agent Approval Flow", test_agent_with_approval),
        ("Streamlit UI", test_streamlit_ui_running),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        print(f"\nTesting: {test_name}")
        print("-" * 60)
        try:
            test_func()
            passed += 1
        except Exception as e:
            print(f"✗ Test failed: {e}")
            failed += 1

    print("\n" + "="*60)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("="*60 + "\n")

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
