"""
PyDocsPal Streamlit UI - Day 10

A professional chat interface for the Python Documentation Assistant with:
- RAG and Agent modes
- Python compatibility badges
- Citations display
- User feedback system
- Human approval flow for agent mode
"""

import os
import sqlite3
import uuid
from datetime import datetime
from typing import Any, Optional

import requests
import streamlit as st

# Configuration
API_URL = os.getenv("PYDOCSPAL_API_URL", "http://localhost:8000")
FEEDBACK_DB = "data/feedback.db"

# Supported Python versions
PYTHON_VERSIONS = ["3.8", "3.9", "3.10", "3.11", "3.12", "3.13", "3.14", "3.15"]


def init_feedback_db():
    """Initialize SQLite feedback database if it doesn't exist."""
    os.makedirs(os.path.dirname(FEEDBACK_DB), exist_ok=True)
    conn = sqlite3.connect(FEEDBACK_DB)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT NOT NULL,
            answer TEXT NOT NULL,
            feedback INTEGER NOT NULL,
            timestamp TEXT NOT NULL,
            python_version TEXT,
            mode TEXT,
            answer_hash TEXT UNIQUE
        )
    """)
    conn.commit()
    conn.close()


def save_feedback(question: str, answer: str, feedback: int, python_version: str, mode: str):
    """Save user feedback to SQLite database."""
    # Create hash to prevent duplicate submissions
    import hashlib
    answer_hash = hashlib.md5(f"{question}|{answer}".encode()).hexdigest()

    conn = sqlite3.connect(FEEDBACK_DB)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO feedback (question, answer, feedback, timestamp, python_version, mode, answer_hash)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (question, answer, feedback, datetime.now().isoformat(), python_version, mode, answer_hash))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        # Duplicate feedback submission
        return False
    finally:
        conn.close()


def check_backend_health() -> bool:
    """Check if backend is available."""
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        return response.status_code == 200
    except Exception:
        return False


def call_ask_endpoint(question: str, top_k: int = 5, python_version: str = "3.12") -> dict[str, Any]:
    """Call the /ask RAG endpoint."""
    try:
        response = requests.post(
            f"{API_URL}/ask",
            json={"question": question, "top_k": top_k, "python_version": python_version},
            timeout=60
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        raise RuntimeError(f"Backend request failed: {str(e)}")


def call_agent_endpoint(
    message: Optional[str] = None,
    thread_id: Optional[str] = None,
    action: Optional[str] = None,
    approved: Optional[bool] = None
) -> dict[str, Any]:
    """Call the /agent endpoint."""
    try:
        payload = {}
        if message:
            payload["message"] = message
        if thread_id:
            payload["thread_id"] = thread_id
        if action:
            payload["action"] = action
        if approved is not None:
            payload["approved"] = approved

        response = requests.post(
            f"{API_URL}/agent",
            json=payload,
            timeout=60
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        raise RuntimeError(f"Backend request failed: {str(e)}")


def extract_compatibility_info(tool_calls: list[dict], python_version: str) -> dict[str, Any]:
    """Extract Python compatibility information from tool calls."""
    compat_info = {
        "has_version_check": False,
        "checks": [],
        "warnings": []
    }

    for tc in tool_calls:
        if tc.get("tool") == "stdlib_version_check":
            result = tc.get("result", {})
            if isinstance(result, dict) and not result.get("error"):
                compat_info["has_version_check"] = True
                symbol = result.get("symbol", "unknown")
                status = result.get("status", "unknown")
                available = result.get("available", False)
                introduced_in = result.get("introduced_in")
                deprecated_in = result.get("deprecated_in")
                removed_in = result.get("removed_in")
                evidence = result.get("evidence", "")
                source_file = result.get("source_file", "")

                check_info = {
                    "symbol": symbol,
                    "status": status,
                    "available": available,
                    "introduced_in": introduced_in,
                    "deprecated_in": deprecated_in,
                    "removed_in": removed_in,
                    "evidence": evidence,
                    "source_file": source_file
                }
                compat_info["checks"].append(check_info)

                # Generate warnings for deprecated/removed APIs
                if status == "deprecated" and deprecated_in:
                    warning = f"⚠️ `{symbol}` - Deprecated since Python {deprecated_in}"
                    if removed_in:
                        warning += f", scheduled for removal in Python {removed_in}"
                    compat_info["warnings"].append(warning)
                elif status == "removed" and removed_in:
                    compat_info["warnings"].append(
                        f"❌ `{symbol}` - Removed in Python {removed_in}"
                    )

    return compat_info


def display_compatibility_badge(compat_info: Optional[dict], python_version: str):
    """Display Python compatibility badge and warnings."""
    if not compat_info or not compat_info.get("has_version_check"):
        st.info("💡 **Compatibility:** Unable to determine - no version checks performed")
        return

    # Find the minimum working version
    min_version = None
    all_available = True

    for check in compat_info["checks"]:
        if not check["available"]:
            all_available = False
        if check["introduced_in"]:
            if min_version is None or check["introduced_in"] > min_version:
                min_version = check["introduced_in"]

    # Display badge
    if all_available and min_version:
        st.success(f"✅ **Works from Python {min_version}**")
    elif all_available and not min_version:
        st.success(f"✅ **Works in Python {python_version}**")
    elif not all_available:
        st.error(f"❌ **Not available in Python {python_version}**")
    else:
        st.warning("⚠️ **Compatibility unknown**")

    # Display warnings
    for warning in compat_info["warnings"]:
        st.warning(warning)

    # Display detailed compatibility info in expander
    if compat_info["checks"]:
        with st.expander("🔍 Detailed Compatibility Information"):
            for check in compat_info["checks"]:
                st.markdown(f"**Symbol:** `{check['symbol']}`")
                st.markdown(f"**Status:** {check['status']}")
                if check["introduced_in"]:
                    st.markdown(f"**Introduced in:** Python {check['introduced_in']}")
                if check["deprecated_in"]:
                    st.markdown(f"**Deprecated in:** Python {check['deprecated_in']}")
                if check["removed_in"]:
                    st.markdown(f"**Removed in:** Python {check['removed_in']}")
                if check["evidence"]:
                    st.markdown(f"**Evidence:** {check['evidence']}")
                if check["source_file"]:
                    st.markdown(f"**Source:** `{check['source_file']}`")
                st.markdown("---")


def display_citations(citations: list[dict]):
    """Display citations in expandable sections."""
    if not citations:
        st.caption("ℹ️ No supporting citations returned.")
        return

    st.markdown("**📚 Sources:**")
    for idx, citation in enumerate(citations, 1):
        source = citation.get("source", "unknown")
        title = citation.get("title", "unknown")
        section = citation.get("section", "unknown")

        # Format citation label
        label = f"{idx}. {title}"
        if section and section != "unknown":
            label += f" - {section}"

        with st.expander(label):
            st.markdown(f"**Source:** `{source}`")
            if title and title != "unknown":
                st.markdown(f"**Title:** {title}")
            if section and section != "unknown":
                st.markdown(f"**Section:** {section}")


def display_feedback_buttons(question: str, answer: str, python_version: str, mode: str, key_suffix: str):
    """Display thumbs up/down feedback buttons."""
    col1, col2, col3 = st.columns([1, 1, 8])

    with col1:
        if st.button("👍", key=f"thumbs_up_{key_suffix}"):
            success = save_feedback(question, answer, 1, python_version, mode)
            if success:
                st.success("✓", icon="✓")
            else:
                st.info("Already rated")

    with col2:
        if st.button("👎", key=f"thumbs_down_{key_suffix}"):
            success = save_feedback(question, answer, -1, python_version, mode)
            if success:
                st.success("✓", icon="✓")
            else:
                st.info("Already rated")


def main():
    """Main Streamlit application."""
    st.set_page_config(
        page_title="PyDocsPal",
        page_icon="🐍",
        layout="wide"
    )

    # Initialize feedback database
    init_feedback_db()

    # Header
    st.title("🐍 PyDocsPal")
    st.markdown("**Your Python Documentation Assistant**")

    # Sidebar configuration
    with st.sidebar:
        st.header("⚙️ Configuration")

        # Backend URL
        st.text_input("Backend URL", value=API_URL, disabled=True, key="backend_url")

        # Check backend health
        if check_backend_health():
            st.success("✅ Backend connected")
        else:
            st.error("❌ Backend unavailable")
            st.stop()

        st.markdown("---")

        # Mode selection
        mode = st.radio(
            "Mode",
            ["RAG", "Agent"],
            help="RAG: Direct question answering. Agent: Multi-step reasoning with tool use."
        )

        # Python version selector
        python_version = st.selectbox(
            "Python Version",
            PYTHON_VERSIONS,
            index=PYTHON_VERSIONS.index("3.12"),
            help="Target Python version for compatibility checks"
        )

        st.markdown("---")
        st.caption("Build with 💖 by Aman")

    # Initialize session state
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "thread_id" not in st.session_state:
        st.session_state.thread_id = str(uuid.uuid4())
    if "pending_approval" not in st.session_state:
        st.session_state.pending_approval = None

    # Display chat history
    for idx, msg in enumerate(st.session_state.messages):
        role = msg["role"]
        content = msg["content"]

        with st.chat_message(role):
            st.markdown(content)

            # Display citations if available
            if "citations" in msg and msg["citations"]:
                display_citations(msg["citations"])

            # Display compatibility badge if available
            if "compat_info" in msg and msg["compat_info"]:
                display_compatibility_badge(msg["compat_info"], msg.get("python_version", python_version))

            # Display feedback buttons for assistant messages
            if role == "assistant" and "question" in msg:
                display_feedback_buttons(
                    msg["question"],
                    content,
                    msg.get("python_version", python_version),
                    msg.get("mode", mode),
                    f"history_{idx}"
                )

    # Handle pending approval
    if st.session_state.pending_approval:
        st.warning("⏸️ **Agent is waiting for your approval**")

        approval_data = st.session_state.pending_approval

        with st.container():
            st.markdown("**Proposed Response:**")
            st.info(approval_data["proposed_response"])

            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Approve", key="approve_btn", type="primary"):
                    with st.spinner("Resuming agent..."):
                        try:
                            result = call_agent_endpoint(
                                thread_id=approval_data["thread_id"],
                                approved=True
                            )

                            # Extract compatibility info
                            tool_calls = result.get("tool_calls", [])
                            compat_info = extract_compatibility_info(tool_calls, python_version)

                            # Add approved response to chat
                            response_text = result.get("response", result.get("proposed_response", ""))
                            st.session_state.messages.append({
                                "role": "assistant",
                                "content": response_text,
                                "citations": result.get("citations", []),
                                "compat_info": compat_info,
                                "python_version": python_version,
                                "mode": "Agent",
                                "question": approval_data.get("question", "")
                            })

                            st.session_state.pending_approval = None
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {str(e)}")

            with col2:
                if st.button("❌ Reject", key="reject_btn"):
                    with st.spinner("Rejecting..."):
                        try:
                            result = call_agent_endpoint(
                                thread_id=approval_data["thread_id"],
                                approved=False
                            )

                            st.session_state.messages.append({
                                "role": "assistant",
                                "content": "❌ Execution was rejected by the user.",
                                "citations": [],
                                "compat_info": None,
                                "python_version": python_version,
                                "mode": "Agent",
                                "question": approval_data.get("question", "")
                            })

                            st.session_state.pending_approval = None
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {str(e)}")

    # Chat input
    if prompt := st.chat_input("Ask a question about Python documentation...", disabled=bool(st.session_state.pending_approval)):
        # Add user message to chat
        st.session_state.messages.append({
            "role": "user",
            "content": prompt
        })

        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)

        # Get assistant response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    if mode == "RAG":
                        # RAG mode
                        result = call_ask_endpoint(prompt, top_k=5, python_version=python_version)
                        answer = result.get("answer", "")
                        citations = result.get("citations", [])

                        # Extract compatibility info returned by /ask endpoint
                        compat_info = result.get("compatibility")

                        # Display answer
                        st.markdown(answer)

                        # Display citations
                        display_citations(citations)

                        # Display compatibility badge
                        display_compatibility_badge(compat_info, python_version)

                        # Add to session state
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": answer,
                            "citations": citations,
                            "compat_info": compat_info,
                            "python_version": python_version,
                            "mode": "RAG",
                            "question": prompt
                        })

                        # Display feedback buttons
                        display_feedback_buttons(prompt, answer, python_version, "RAG", "current")

                    else:
                        # Agent mode
                        result = call_agent_endpoint(
                            message=prompt,
                            thread_id=st.session_state.thread_id
                        )

                        if result.get("approval_required"):
                            # Store pending approval
                            st.session_state.pending_approval = {
                                "thread_id": result["thread_id"],
                                "proposed_response": result.get("proposed_response", ""),
                                "tool_calls": result.get("tool_calls", []),
                                "citations": result.get("citations", []),
                                "question": prompt
                            }
                            st.rerun()
                        else:
                            # Extract compatibility info
                            tool_calls = result.get("tool_calls", [])
                            compat_info = extract_compatibility_info(tool_calls, python_version)

                            # Display response
                            response_text = result.get("response", result.get("proposed_response", ""))
                            st.markdown(response_text)

                            # Display citations
                            citations = result.get("citations", [])
                            display_citations(citations)

                            # Display compatibility badge
                            display_compatibility_badge(compat_info, python_version)

                            # Add to session state
                            st.session_state.messages.append({
                                "role": "assistant",
                                "content": response_text,
                                "citations": citations,
                                "compat_info": compat_info,
                                "python_version": python_version,
                                "mode": "Agent",
                                "question": prompt
                            })

                            # Display feedback buttons
                            display_feedback_buttons(prompt, response_text, python_version, "Agent", "current")

                except Exception as e:
                    error_msg = f"❌ Error: {str(e)}"
                    st.error(error_msg)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": error_msg,
                        "citations": [],
                        "compat_info": None,
                        "python_version": python_version,
                        "mode": mode,
                        "question": prompt
                    })


if __name__ == "__main__":
    main()
