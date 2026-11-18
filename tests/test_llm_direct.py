"""Test LLM generation directly to see what's being returned."""

from app.llm import generate_response
from app.agent_loop import SYSTEM_AGENT_PROMPT

def test_llm_direct():
    """Test what the LLM is actually returning."""
    
    user_prompt = """User Question: Is pathlib.Path.mkdir available in Python 3.8?

Current Iteration: 1 of 4

Tool Execution History:
No tools have been called yet.

Decide your next action (call_tool or final_response):"""
    
    print("\n" + "="*60)
    print("Testing Direct LLM Call")
    print("="*60)
    print(f"\nSystem Prompt Length: {len(SYSTEM_AGENT_PROMPT)} chars")
    print(f"User Prompt Length: {len(user_prompt)} chars")
    print("-"*60)
    
    try:
        response = generate_response(SYSTEM_AGENT_PROMPT, user_prompt)
        print(f"\nLLM Response:\n{response}")
        print("-"*60)
        
        # Try to parse as JSON
        import json
        try:
            data = json.loads(response)
            print(f"\n✓ Valid JSON!")
            print(f"Action: {data.get('action')}")
            print(f"Keys: {list(data.keys())}")
        except json.JSONDecodeError as e:
            print(f"\n✗ Invalid JSON: {e}")
            print(f"Response type: {type(response)}")
            print(f"Response length: {len(response)}")
            
    except Exception as e:
        print(f"\n✗ LLM Error: {type(e).__name__}: {e}")
    
    print("="*60)

if __name__ == "__main__":
    test_llm_direct()
