import streamlit as st

from app.core.function_caller import run_agent


def render_consultation() -> None:
    st.subheader("Consultation")
    complaint = st.text_area(
        "Describe the patient's problem",
        value=st.session_state.get("chief_complaint", ""),
        height=150,
    )

    if st.button("Analyze consultation"):
        st.session_state["chief_complaint"] = complaint
        result = run_agent(complaint, st.session_state.get("agent_history", []))
        st.session_state["agent_history"] = result["history"]
        st.session_state["detected_language"] = result.get("explanation", {}).get("language", "Auto")
        st.session_state["triage_result"] = {
            "priority": result["response"].split(":", 1)[0],
            "summary": result["response"],
            "actions": [result.get("tool_used") or "guided_triage"],
            "explanation": result.get("explanation"),
        }
        st.success("Consultation analyzed.")
