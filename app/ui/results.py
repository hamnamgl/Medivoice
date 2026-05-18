import streamlit as st


def render_results() -> None:
    st.subheader("Assessment Results")
    result = st.session_state.get("triage_result")
    detected_language = st.session_state.get("detected_language", "Unknown")

    if not result:
        st.warning("No consultation has been analyzed yet.")
        return

    st.write(f"Detected language: **{detected_language}**")
    st.metric("Priority", result["priority"])
    st.write(result["summary"])
    st.write("Recommended actions:")
    for action in result["actions"]:
        st.write(f"- {action}")
    if result.get("explanation"):
        with st.expander("Why this answer?", expanded=False):
            st.json(result["explanation"])
