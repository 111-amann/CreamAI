"""Final comprehensive verification of all functionality."""
import sys
import time
import requests
import subprocess
import signal

print("=" * 70)
print("FINAL COMPREHENSIVE VERIFICATION")
print("=" * 70)

# Start FastAPI server
print("\n[Starting] FastAPI server...")
server_process = subprocess.Popen(
    [".venv\\Scripts\\python.exe", "-m", "uvicorn", "app.main:app", "--port", "8000"],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
)

time.sleep(5)

BASE_URL = "http://localhost:8000"
all_passed = True

def test(name, func):
    global all_passed
    try:
        print(f"\n[Test] {name}...")
        func()
        print(f"✓ {name} PASSED")
        return True
    except AssertionError as e:
        print(f"✗ {name} FAILED: {e}")
        all_passed = False
        return False
    except Exception as e:
        print(f"✗ {name} ERROR: {type(e).__name__}: {e}")
        all_passed = False
        return False

def test_health():
    r = requests.get(f"{BASE_URL}/health", timeout=10)
    assert r.status_code == 200, f"Status {r.status_code}"
    data = r.json()
    assert data["status"] == "healthy", f"Status not healthy: {data}"

def test_rag_ask():
    r = requests.post(
        f"{BASE_URL}/ask",
        json={"question": "What is pathlib.Path?"},
        timeout=30
    )
    assert r.status_code == 200, f"Status {r.status_code}"
    data = r.json()
    assert "answer" in data, "No answer field"
    assert len(data["answer"]) > 50, f"Answer too short: {data['answer']}"
    assert "pathlib" in data["answer"].lower(), "Answer doesn't mention pathlib"
    print(f"  Answer: {data['answer'][:100]}...")

def test_agent_version_check():
    r = requests.post(
        f"{BASE_URL}/agent",
        json={"message": "Is pathlib.Path.mkdir available in Python 3.8?"},
        timeout=45
    )
    assert r.status_code == 200, f"Status {r.status_code}: {r.text[:200]}"
    data = r.json()
    assert "thread_id" in data, "No thread_id"
    assert "status" in data, "No status"
    assert data.get("approval_required") == True, "Not in approval state"
    
    proposed = data.get("proposed_response", "")
    assert len(proposed) > 50, f"Proposed too short: {proposed}"
    assert "error" not in proposed.lower(), f"Error in proposed: {proposed}"
    assert "3.8" in proposed or "python 3.8" in proposed.lower(), "Doesn't mention version"
    
    print(f"  Status: {data['status']}")
    print(f"  Proposed: {proposed[:100]}...")
    
    # Approve and get final response
    thread_id = data["thread_id"]
    r2 = requests.post(
        f"{BASE_URL}/agent",
        json={"thread_id": thread_id, "approved": True},
        timeout=30
    )
    assert r2.status_code == 200, f"Approval failed: {r2.status_code}"
    data2 = r2.json()
    assert data2.get("response"), "No final response"
    print(f"  Final: {data2['response'][:100]}...")

def test_agent_rejection():
    r = requests.post(
        f"{BASE_URL}/agent",
        json={"message": "What is async/await in Python?"},
        timeout=45
    )
    assert r.status_code == 200, f"Status {r.status_code}"
    data = r.json()
    thread_id = data["thread_id"]
    
    # Reject
    r2 = requests.post(
        f"{BASE_URL}/agent",
        json={"thread_id": thread_id, "approved": False},
        timeout=30
    )
    assert r2.status_code == 200, f"Rejection failed: {r2.status_code}"
    data2 = r2.json()
    assert data2["status"] == "rejected", f"Status not rejected: {data2['status']}"
    print(f"  Rejection handled correctly")

try:
    test("Health Check", test_health)
    test("RAG Ask", test_rag_ask)
    test("Agent Version Check + Approval", test_agent_version_check)
    test("Agent Rejection", test_agent_rejection)
    
    if all_passed:
        print("\n" + "=" * 70)
        print("✓ ALL TESTS PASSED - System fully functional")
        print("=" * 70)
    else:
        print("\n" + "=" * 70)
        print("✗ SOME TESTS FAILED")
        print("=" * 70)
        sys.exit(1)

finally:
    print("\n[Cleanup] Stopping server...")
    try:
        server_process.send_signal(signal.CTRL_BREAK_EVENT)
        server_process.wait(timeout=5)
    except:
        server_process.kill()
    print("Server stopped.")
