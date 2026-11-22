"""Test to reproduce Groq BadRequestError issue."""

import json

import requests


def test_agent_groq_error():
    """Reproduce the Groq error with the exact question from the screenshot."""
    url = "http://localhost:8000/agent"
    payload = {
        "message": "Is pathlib.Path.mkdir available in Python 3.8?"
    }

    print("\n" + "="*60)
    print("Testing Agent Endpoint with Groq")
    print("="*60)
    print(f"URL: {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    print("-"*60)

    try:
        response = requests.post(url, json=payload, timeout=60)
    except Exception as e:
        print(f"✗ Request failed: {e}")
        return False

    print(f"Status Code: {response.status_code}")
    print("-"*60)

    if response.status_code != 200:
        print(f"✗ HTTP Error: {response.status_code}")
        print(f"Response: {response.text}")
        return False

    data = response.json()
    print(f"Response Body:\n{json.dumps(data, indent=2)}")
    print("="*60)

    # Check for errors in response even if HTTP 200
    error_indicators = [
        "BadRequestError",
        "NotFoundError",
        "model_not_found",
        "json_validate_failed",
        "Error code: 400",
        "Error code: 404",
        "Agent reasoning error:",
    ]

    # Check proposed_response field
    proposed = str(data.get("proposed_response", ""))
    for indicator in error_indicators:
        if indicator in proposed:
            print(f"\n✗ BUG DETECTED: '{indicator}' found in proposed_response!")
            print(f"Proposed Response: {proposed[:200]}...")
            return False

    # Check error field
    error_field = str(data.get("error", ""))
    if error_field and error_field != "None":
        for indicator in error_indicators:
            if indicator in error_field:
                print(f"\n✗ BUG DETECTED: '{indicator}' found in error field!")
                print(f"Error: {error_field[:200]}...")
                return False

    # Check that we got a valid agent response
    if data.get("approval_required"):
        print("\n✓ Agent requires approval (normal flow)")
        print(f"  Thread ID: {data.get('thread_id')}")
        print(f"  Status: {data.get('status')}")
        print(f"  Proposed: {proposed[:100]}...")
    elif data.get("response"):
        print("\n✓ Agent completed successfully")
        print(f"  Response: {data.get('response')[:100]}...")
    else:
        print("\n⚠ Warning: No clear response or approval")

    print("\n✓ No Groq/LLM errors detected in response")
    return True

if __name__ == "__main__":
    success = test_agent_groq_error()
    exit(0 if success else 1)
