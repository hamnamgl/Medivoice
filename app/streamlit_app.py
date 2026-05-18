from __future__ import annotations

import streamlit as st

from app.core.function_caller import run_agent
from app.utils.config import APP_MODE, DEFAULT_MODEL, SUPPORTED_LANGUAGES
from app.utils.local_db import get_recent_visits, get_stats, init_db


st.set_page_config(page_title="MediVoice", page_icon="🩺", layout="wide")


def _ensure_state() -> None:
    st.session_state.setdefault("history", [])
    st.session_state.setdefault("messages", [])
    st.session_state.setdefault("selected_language", "English")


def _show_sidebar() -> None:
    st.sidebar.title("MediVoice")
    st.sidebar.caption("Offline-first CHW support")
    st.sidebar.write(f"Mode: `{APP_MODE}`")
    st.sidebar.write(f"Default model: `{DEFAULT_MODEL}`")
    st.sidebar.selectbox(
        "Consultation language",
        SUPPORTED_LANGUAGES,
        key="selected_language",
    )

    stats = get_stats()
    st.sidebar.subheader("Local stats")
    st.sidebar.metric("Total visits", stats["total_visits"])
    st.sidebar.metric("Emergency", stats["emergencies"])
    st.sidebar.metric("Referrals", stats["referrals"])

    with st.sidebar.expander("Recent visits", expanded=False):
        for row in get_recent_visits(5):
            st.write(
                f"- {row['timestamp']} | {row['language']} | "
                f"{row['severity']} | {row['symptoms']}"
            )


def _show_intro() -> None:
    st.title("MediVoice")
    st.write(
        "A local AI assistant for community health workers with guided triage, "
        "offline referral lookup, and dosage support."
    )
    st.info(
        "Use this Streamlit companion UI for laptop demos. For phone demos, use the PWA. "
        "For offline CLI operation, run `python -m app.main`."
    )


def _render_messages() -> None:
    for item in st.session_state["messages"]:
        role = item["role"]
        with st.chat_message("assistant" if role == "assistant" else "user"):
            st.write(item["content"])
            if role == "assistant" and item.get("explanation"):
                with st.expander("Why this answer?", expanded=False):
                    st.json(item["explanation"])


def _handle_user_message(message: str) -> None:
    st.session_state["messages"].append({"role": "user", "content": message})
    result = run_agent(message, st.session_state["history"])
    st.session_state["history"] = result["history"]
    st.session_state["messages"].append(
        {
            "role": "assistant",
            "content": result["response"],
            "explanation": result.get("explanation"),
        }
    )


def main() -> None:
    init_db()
    _ensure_state()
    _show_sidebar()
    _show_intro()
    _render_messages()

    if prompt := st.chat_input("Describe patient symptoms..."):
        _handle_user_message(prompt)
        st.rerun()


if __name__ == "__main__":
    main()
