import streamlit as st

from app.core.language_detector import detect_language
from app.core.triage_logic import run_basic_triage


def render_consultation() -> None:
    st.subheader("Consultation")
    complaint = st.text_area(
        "Describe the patient's problem",
        value=st.session_state.get("chief_complaint", ""),
        height=150,
    )

    if st.button("Analyze consultation"):
        st.session_state["chief_complaint"] = complaint
        detected = detect_language(complaint)
        st.session_state["detected_language"] = detected
        st.session_state["triage_result"] = run_basic_triage(complaint)
        st.success(f"Consultation analyzed in {detected}.")
