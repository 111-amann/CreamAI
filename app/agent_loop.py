"""
app/agent_loop.py - Handwritten Agent Loop for PyDocsPal.

Provides a multi-step agent loop capable of:
1. Tool selection (stdlib_version_check, rag_search).
2. Tool execution in safe Python runtime with argument validation.
3. Inspecting intermediate results and executing subsequent tools if needed.
4. Synthesizing final grounded responses with citations.
5. Strict guardrails: no arbitrary code execution, max iteration limits,
   distinguishing documented facts from unknown info.
"""

import json
import re
from typing import Any, Callable, Optional

from app.hybrid_search import hybrid_search
from app.llm import generate_response
from app.tools import stdlib_version_check


SYSTEM_AGENT_PROMPT = """You are PyDocsPal Agent, an intelligent assistant for Python documentation and standard library compatibility.

CRITICAL: Do NOT use function calling or tool calling features. You must respond ONLY with a plain JSON object.

You have access to two tools via JSON instruction format:

1. `stdlib_version_check`:
   Deterministic check of whether a standard library symbol/API is available, introduced, deprecated, or removed in a specified Python version.
   Arguments:
     - `symbol` (string, required): e.g. "pathlib.Path.mkdir", "functools.cache", "os.path.isreserved".
     - `python_version` (string, required): e.g. "3.8", "3.11", "3.13", "3.15".

2. `rag_search`:
   Retrieves relevant documentation chunks, usage explanations, and signatures from the official Python documentation.
   Arguments:
     - `query` (string, required): search query or topic keywords.
     - `top_k` (integer, optional): number of chunks to retrieve (default 5).

INSTRUCTIONS:
- Analyze the user question carefully.
- If the question asks about version availability, introduction, removal, or deprecation, request execution of `stdlib_version_check`.
- If the question asks for explanations, signatures, code examples, or details, request execution of `rag_search`.
- If the question requires both (e.g. "Explain X and check if available in 3.8"), you may request one tool, inspect the result, and then request the other tool.
- When you have gathered sufficient information, or if no further tool calls are needed, return `action: "final_response"`.
- Never invent version numbers, API signatures, or tool outputs. Base your final response strictly on the tool results provided.
- If the tool indicates an API was not yet available, deprecated, removed, or unknown, state that accurately.

RESPONSE FORMAT:
You MUST respond with ONLY a plain JSON object in your message content. Do NOT use function/tool calling features. Do NOT include markdown code block formatting.

Option A - Request a tool execution:
{
  "action": "call_tool",
  "tool": "stdlib_version_check",
  "args": {"symbol": "pathlib.Path.mkdir", "python_version": "3.8"},
  "reasoning": "brief explanation of why this tool is needed"
}

OR

{
  "action": "call_tool",
  "tool": "rag_search",
  "args": {"query": "example query", "top_k": 5},
  "reasoning": "brief explanation"
}

Option B - Provide final response:
{
  "action": "final_response",
  "answer": "Complete, grounded answer based on tool results.",
  "status": "completed"
}
"""

SYNTHESIS_SYSTEM_PROMPT = """You are PyDocsPal Agent.

CRITICAL: Do NOT use function calling or tool calling features. You must respond ONLY with a plain JSON object in your message content.

Formulate a final, grounded, and concise answer to the user's question using ONLY the provided tool results.
Do not invent facts, version numbers, or documentation details.
If the tool results show the information is unknown or not documented, state that clearly.

Respond with ONLY a plain JSON object (no markdown, no code blocks, no function calls):
{
  "action": "final_response",
  "answer": "Your grounded final answer.",
  "status": "completed"
}
"""


def execute_rag_search(query: str, top_k: int = 5) -> dict[str, Any]:
    """Execute hybrid search against the official Python documentation."""
    clean_query = query.strip()
    if not clean_query:
        return {"error": "Query cannot be empty."}

    chunks = hybrid_search(clean_query, limit=top_k)
    formatted_chunks = []
    citations = []

    for idx, c in enumerate(chunks, start=1):
        meta = c.get("metadata", {})
        source = meta.get("source", "unknown")
        title = meta.get("title", "unknown")
        section = meta.get("section", "unknown")
        text = c.get("text", "").strip()

        formatted_chunks.append({
            "index": idx,
            "source": source,
            "title": title,
            "section": section,
            "text": text[:600],
        })

        citations.append({
            "source": source,
            "title": title,
            "section": section,
            "page": meta.get("page", "unknown"),
        })

    return {
        "query": clean_query,
        "results_count": len(chunks),
        "chunks": formatted_chunks,
        "citations": citations,
    }


def execute_stdlib_version_check(symbol: str, python_version: str) -> dict[str, Any]:
    """Execute deterministic standard library version check."""
    clean_symbol = str(symbol).strip()
    clean_ver = str(python_version).strip()
    if not clean_symbol:
        return {"error": "Symbol cannot be empty."}
    if not clean_ver:
        return {"error": "Python version cannot be empty."}

    return stdlib_version_check(clean_symbol, clean_ver)


# Safe Tool Registry
TOOL_REGISTRY: dict[str, dict[str, Any]] = {
    "stdlib_version_check": {
        "func": execute_stdlib_version_check,
        "required_args": ["symbol", "python_version"],
        "description": "Checks availability, introduction, deprecation, or removal in standard library.",
    },
    "rag_search": {
        "func": execute_rag_search,
        "required_args": ["query"],
        "description": "Searches official Python documentation for explanations and signatures.",
    },
}


def parse_llm_json(raw_text: str) -> dict[str, Any]:
    """Parse JSON response from LLM, stripping markdown code blocks if present."""
    text = raw_text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.I)
        text = re.sub(r"\s*```$", "", text)
    text = text.strip()

    # Find outermost JSON object
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        text = match.group(0)

    return json.loads(text)


def run_agent_loop(
    question: str,
    max_iterations: int = 4,
    rag_top_k: int = 5,
    custom_llm_generator: Optional[Callable[[str, str], str]] = None,
) -> dict[str, Any]:
    """
    Execute handwritten agent loop:
    1. Evaluates question and tool history.
    2. Dispatches tools safely in Python.
    3. Prevents infinite loops via max_iterations.
    4. Gathers citations and synthesizes final answer.
    """
    clean_question = question.strip()
    if not clean_question:
        raise ValueError("Question cannot be empty.")

    llm_func = custom_llm_generator or generate_response
    tool_history: list[dict[str, Any]] = []
    gathered_citations: list[dict[str, Any]] = []

    for iteration in range(1, max_iterations + 1):
        # Format tool history for prompt
        history_str = "No tools have been called yet."
        if tool_history:
            history_blocks = []
            for item in tool_history:
                history_blocks.append(
                    f"Tool: {item['tool']}\n"
                    f"Arguments: {json.dumps(item['args'])}\n"
                    f"Result: {json.dumps(item['result'], indent=2)}"
                )
            history_str = "\n\n---\n\n".join(history_blocks)

        user_prompt = (
            f"User Question: {clean_question}\n\n"
            f"Current Iteration: {iteration} of {max_iterations}\n\n"
            f"Tool Execution History:\n{history_str}\n\n"
            f"Decide your next action (call_tool or final_response):"
        )

        try:
            raw_output = llm_func(SYSTEM_AGENT_PROMPT, user_prompt)
            data = parse_llm_json(raw_output)
        except RuntimeError:
            # LLM provider errors should propagate
            raise
        except Exception as exc:
            # If LLM generation or JSON parsing fails
            tool_history.append({
                "tool": "system",
                "args": {},
                "result": f"Generation / Parsing error: {type(exc).__name__}: {exc}",
            })
            break

        action = str(data.get("action", "")).strip().lower()

        if action == "call_tool":
            tool_name = str(data.get("tool", "")).strip()
            args = data.get("args", {})
            if not isinstance(args, dict):
                args = {}

            # 1. Validate tool name
            if tool_name not in TOOL_REGISTRY:
                tool_history.append({
                    "tool": tool_name,
                    "args": args,
                    "result": f"Error: Tool '{tool_name}' not found. Available tools: {list(TOOL_REGISTRY.keys())}",
                })
                continue

            tool_spec = TOOL_REGISTRY[tool_name]
            required_args = tool_spec["required_args"]
            missing = [arg for arg in required_args if arg not in args or not str(args[arg]).strip()]

            # 2. Validate arguments
            if missing:
                tool_history.append({
                    "tool": tool_name,
                    "args": args,
                    "result": f"Error: Missing required arguments: {missing}. Required: {required_args}",
                })
                continue

            # 3. Execute tool
            tool_func = tool_spec["func"]
            try:
                if tool_name == "rag_search" and "top_k" not in args:
                    args["top_k"] = rag_top_k
                result = tool_func(**args)
            except Exception as exc:
                result = {"error": f"Tool execution failed: {type(exc).__name__}: {exc}"}

            tool_history.append({
                "tool": tool_name,
                "args": args,
                "result": result,
            })

            # Collect citations
            if tool_name == "rag_search" and isinstance(result, dict) and "citations" in result:
                for cit in result["citations"]:
                    if cit not in gathered_citations:
                        gathered_citations.append(cit)
            elif tool_name == "stdlib_version_check" and isinstance(result, dict) and result.get("source_file"):
                cit = {
                    "source": result["source_file"],
                    "title": f"Python {result.get('python_version')} Stdlib Compatibility",
                    "section": result.get("symbol", "unknown"),
                    "page": "version_check",
                }
                if cit not in gathered_citations:
                    gathered_citations.append(cit)

            # Continue to next iteration to let agent inspect result
            continue

        elif action == "final_response":
            answer = str(data.get("answer", "")).strip()
            resp_status = str(data.get("status", "completed")).strip().lower()
            return {
                "question": clean_question,
                "answer": answer,
                "status": resp_status,
                "tool_calls": tool_history,
                "citations": gathered_citations,
                "iterations": iteration,
            }

        else:
            tool_history.append({
                "tool": "system",
                "args": {},
                "result": f"Unknown action '{action}'. Must be 'call_tool' or 'final_response'.",
            })

    # If loop ended without explicit final_response (e.g. hit max iterations or parse issue)
    # Perform final synthesis call
    synth_prompt = (
        f"User Question: {clean_question}\n\n"
        f"Tool Results:\n{json.dumps(tool_history, indent=2)}\n\n"
        f"Formulate the final grounded answer:"
    )

    try:
        raw_synth = llm_func(SYNTHESIS_SYSTEM_PROMPT, synth_prompt)
        synth_data = parse_llm_json(raw_synth)
        final_answer = str(synth_data.get("answer", "")).strip()
        final_status = str(synth_data.get("status", "completed")).strip().lower()
    except RuntimeError:
        # LLM provider errors should propagate
        raise
    except Exception as exc:
        final_answer = (
            "Agent reached maximum iterations. Tool execution results: "
            + "; ".join(f"{item['tool']}: {item['result']}" for item in tool_history if item['tool'] != 'system')
        )
        final_status = "completed" if tool_history else "error"

    return {
        "question": clean_question,
        "answer": final_answer,
        "status": final_status,
        "tool_calls": tool_history,
        "citations": gathered_citations,
        "iterations": len(tool_history),
    }

