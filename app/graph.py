"""
app/graph.py - LangGraph Agent Workflow with Memory and Human Approval.

Workflow:
START -> agent -> (conditional: tools -> agent | approval) -> approval (interrupt) -> finalize -> END

Features:
- Pure LangGraph StateGraph implementation with MemorySaver checkpointer.
- Deterministic stdlib_version_check and hybrid RAG tools.
- Multi-step tool loop with conditional routing.
- Isolated conversation memory per thread_id.
- Meaningful human approval step via LangGraph interrupt() and Command(resume=...).
"""

import json
from typing import Annotated, Any, Callable, Optional, TypedDict

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.types import Command, interrupt

from app.agent_loop import (
    SYNTHESIS_SYSTEM_PROMPT,
    SYSTEM_AGENT_PROMPT,
    TOOL_REGISTRY,
    parse_llm_json,
)
from app.llm import generate_response


class AgentGraphState(TypedDict):
    """Typed state for the LangGraph agent."""
    question: str
    messages: Annotated[list[BaseMessage], add_messages]
    tool_calls: list[dict[str, Any]]
    pending_tool: Optional[dict[str, Any]]
    iterations: int
    proposed_response: Optional[str]
    approval_status: str  # "pending", "approved", "rejected"
    final_response: Optional[str]
    citations: list[dict[str, Any]]
    error: Optional[str]


def agent_node(state: AgentGraphState, config: RunnableConfig) -> dict[str, Any]:
    """
    Agent reasoning node:
    Evaluates current question, messages, and previous tool results.
    Decides whether to invoke a tool or propose a final response.
    """
    question = state.get("question", "")
    tool_calls = state.get("tool_calls", [])
    iterations = state.get("iterations", 0) + 1

    # Retrieve custom LLM generator if injected in config
    configurable = (config or {}).get("configurable", {})
    llm_func = configurable.get("llm_generator") or generate_response
    max_iterations = configurable.get("max_iterations", 4)

    # Format tool execution history
    history_str = "No tools have been called yet."
    if tool_calls:
        history_blocks = []
        for item in tool_calls:
            history_blocks.append(
                f"Tool: {item['tool']}\n"
                f"Arguments: {json.dumps(item.get('args', {}))}\n"
                f"Result: {json.dumps(item.get('result', {}), indent=2)}"
            )
        history_str = "\n\n---\n\n".join(history_blocks)

    user_prompt = (
        f"User Question: {question}\n\n"
        f"Current Iteration: {iterations} of {max_iterations}\n\n"
        f"Tool Execution History:\n{history_str}\n\n"
        f"Decide your next action (call_tool or final_response):"
    )

    # If already at max iterations, force proposal
    if iterations >= max_iterations:
        synth_prompt = (
            f"User Question: {question}\n\n"
            f"Tool Execution History:\n{history_str}\n\n"
            f"Synthesize the proposed final grounded response:"
        )
        try:
            raw_synth = llm_func(SYNTHESIS_SYSTEM_PROMPT, synth_prompt)
            data = parse_llm_json(raw_synth)
            answer = str(data.get("answer", "")).strip()
        except RuntimeError:
            # LLM provider errors should propagate
            raise
        except Exception:
            answer = (
                "Maximum iterations reached. Available tool results: "
                + "; ".join(f"{t['tool']}: {t.get('result')}" for t in tool_calls)
            )
        return {
            "iterations": iterations,
            "pending_tool": None,
            "proposed_response": answer,
            "messages": [AIMessage(content=answer)],
        }

    try:
        raw_output = llm_func(SYSTEM_AGENT_PROMPT, user_prompt)
        data = parse_llm_json(raw_output)
    except Exception as exc:
        # Propagate LLM and JSON parsing errors to prevent masking failures as successful approval prompts
        raise RuntimeError(f"Agent reasoning error: {type(exc).__name__}: {exc}") from exc

    action = str(data.get("action", "")).strip().lower()

    if action == "call_tool":
        tool_name = str(data.get("tool", "")).strip()
        args = data.get("args", {})
        return {
            "iterations": iterations,
            "pending_tool": {"tool": tool_name, "args": args},
        }
    else:
        answer = str(data.get("answer", "")).strip()
        return {
            "iterations": iterations,
            "pending_tool": None,
            "proposed_response": answer,
            "messages": [AIMessage(content=answer)],
        }


def tool_execution_node(state: AgentGraphState, config: RunnableConfig) -> dict[str, Any]:
    """
    Executes the pending tool call in safe Python runtime,
    collects output and citations, and updates state.
    """
    pending = state.get("pending_tool")
    tool_calls = list(state.get("tool_calls", []))
    citations = list(state.get("citations", []))

    if not pending:
        return {"tool_calls": tool_calls, "pending_tool": None}

    tool_name = pending.get("tool", "")
    args = pending.get("args", {})

    if tool_name not in TOOL_REGISTRY:
        result = f"Error: Tool '{tool_name}' not recognized."
    else:
        spec = TOOL_REGISTRY[tool_name]
        required = spec["required_args"]
        missing = [arg for arg in required if arg not in args or not str(args[arg]).strip()]
        if missing:
            result = f"Error: Missing required arguments: {missing}."
        else:
            try:
                func = spec["func"]
                result = func(**args)
            except Exception as exc:
                result = f"Tool execution failed: {type(exc).__name__}: {exc}"

    tool_calls.append({
        "tool": tool_name,
        "args": args,
        "result": result,
    })

    # Collect citations
    if tool_name == "rag_search" and isinstance(result, dict) and "citations" in result:
        for c in result["citations"]:
            if c not in citations:
                citations.append(c)
    elif tool_name == "stdlib_version_check" and isinstance(result, dict) and result.get("source_file"):
        cit = {
            "source": result["source_file"],
            "title": f"Python {result.get('python_version')} Stdlib Compatibility",
            "section": result.get("symbol", "unknown"),
            "page": "version_check",
        }
        if cit not in citations:
            citations.append(cit)

    return {
        "tool_calls": tool_calls,
        "citations": citations,
        "pending_tool": None,
    }


def approval_node(state: AgentGraphState) -> dict[str, Any]:
    """
    Human approval node:
    Pauses execution via interrupt(), presenting the proposed response and tool results.
    Resumes with the human decision.
    """
    proposed = state.get("proposed_response") or "No response proposed."
    interrupt_payload = {
        "action": "human_approval_required",
        "proposed_response": proposed,
        "tool_calls": state.get("tool_calls", []),
        "citations": state.get("citations", []),
    }

    # Pause graph execution and wait for resume command
    decision = interrupt(interrupt_payload)

    is_approved = False
    if isinstance(decision, dict):
        is_approved = bool(decision.get("approved", False))
    elif isinstance(decision, bool):
        is_approved = decision
    elif isinstance(decision, str):
        is_approved = decision.strip().lower() in ("approve", "approved", "yes", "true")

    if is_approved:
        return {"approval_status": "approved"}
    else:
        return {"approval_status": "rejected"}


def finalize_node(state: AgentGraphState) -> dict[str, Any]:
    """
    Final response node:
    If approved, produces final response.
    If rejected, returns explicit rejection notification without presenting proposed answer as approved.
    """
    approval_status = state.get("approval_status", "rejected")
    proposed = state.get("proposed_response", "")

    if approval_status == "approved":
        final_answer = proposed
    else:
        final_answer = "Execution was rejected by the user. The proposed response was not approved."

    return {
        "final_response": final_answer,
        "messages": [AIMessage(content=final_answer)],
    }


def route_agent_decision(state: AgentGraphState) -> str:
    """Conditional edge from agent: call tool or proceed to approval."""
    if state.get("pending_tool") is not None:
        return "tools"
    return "approval"


def build_agent_graph(checkpointer: Optional[MemorySaver] = None):
    """Construct and compile the LangGraph workflow."""
    builder = StateGraph(AgentGraphState)

    builder.add_node("agent", agent_node)
    builder.add_node("tools", tool_execution_node)
    builder.add_node("approval", approval_node)
    builder.add_node("finalize", finalize_node)

    builder.add_edge(START, "agent")
    builder.add_conditional_edges(
        "agent",
        route_agent_decision,
        {
            "tools": "tools",
            "approval": "approval",
        },
    )
    builder.add_edge("tools", "agent")
    builder.add_edge("approval", "finalize")
    builder.add_edge("finalize", END)

    cp = checkpointer if checkpointer is not None else MemorySaver()
    return builder.compile(checkpointer=cp)


# Global persistent checkpointer for the application runtime
# Keeps memory isolated across threads during process lifetime
global_checkpointer = MemorySaver()
agent_graph = build_agent_graph(checkpointer=global_checkpointer)


def run_langgraph_agent(
    message: str,
    thread_id: str,
    graph=None,
    llm_generator: Optional[Callable[[str, str], str]] = None,
) -> dict[str, Any]:
    """
    Initiate or continue a conversation thread on the LangGraph agent.
    Returns status: 'approval_required' (paused), 'completed', or 'error'.
    """
    active_graph = graph or agent_graph
    config = {
        "configurable": {
            "thread_id": thread_id,
            "llm_generator": llm_generator,
        }
    }

    # Inspect current thread state
    current_state = active_graph.get_state(config)
    if current_state.next and "approval" in current_state.next:
        raise ValueError(
            f"Thread '{thread_id}' is currently awaiting approval. "
            "Please approve or reject the pending action before submitting a new message."
        )

    initial_state = {
        "question": message,
        "messages": [HumanMessage(content=message)],
        "iterations": 0,
        "tool_calls": [],
        "citations": [],
        "approval_status": "pending",
        "error": None,
    }

    # Invoke graph turn
    active_graph.invoke(initial_state, config=config)

    # Check updated state
    updated_state = active_graph.get_state(config)
    state_values = updated_state.values

    # If paused at approval node
    if updated_state.next and "approval" in updated_state.next:
        return {
            "thread_id": thread_id,
            "status": "approval_required",
            "approval_required": True,
            "proposed_response": state_values.get("proposed_response"),
            "response": None,
            "tool_calls": state_values.get("tool_calls", []),
            "citations": state_values.get("citations", []),
            "error": state_values.get("error"),
        }

    # Completed without interruption
    return {
        "thread_id": thread_id,
        "status": "completed",
        "approval_required": False,
        "proposed_response": state_values.get("proposed_response"),
        "response": state_values.get("final_response"),
        "tool_calls": state_values.get("tool_calls", []),
        "citations": state_values.get("citations", []),
        "error": state_values.get("error"),
    }


def resume_langgraph_agent(
    thread_id: str,
    approved: bool,
    graph=None,
) -> dict[str, Any]:
    """
    Resume an interrupted LangGraph agent at the approval step with human decision.
    """
    active_graph = graph or agent_graph
    config = {"configurable": {"thread_id": thread_id}}

    current_state = active_graph.get_state(config)
    if not current_state.next or "approval" not in current_state.next:
        raise ValueError(f"Thread '{thread_id}' is not currently awaiting approval.")

    # Resume graph execution with the decision
    active_graph.invoke(Command(resume={"approved": approved}), config=config)

    updated_state = active_graph.get_state(config)
    state_values = updated_state.values
    status = "completed" if approved else "rejected"

    return {
        "thread_id": thread_id,
        "status": status,
        "approval_required": False,
        "proposed_response": state_values.get("proposed_response"),
        "response": state_values.get("final_response"),
        "tool_calls": state_values.get("tool_calls", []),
        "citations": state_values.get("citations", []),
        "error": state_values.get("error"),
    }

