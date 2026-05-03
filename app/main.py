from __future__ import annotations

import streamlit as st

from app.ui.consultation import render_consultation
from app.ui.home import render_home
from app.ui.results import render_results
from app.ui.settings import render_settings
from app.utils.config import APP_TITLE, SUPPORTED_LANGUAGES


def bootstrap_state() -> None:
    st.session_state.setdefault("language", "English")
    st.session_state.setdefault("patient_name", "")
    st.session_state.setdefault("chief_complaint", "")
    st.session_state.setdefault("symptoms", [])
    st.session_state.setdefault("triage_result", None)
    st.session_state.setdefault("notes", "")


def main() -> None:
    st.set_page_config(page_title=APP_TITLE, page_icon=":stethoscope:", layout="wide")
    bootstrap_state()

    st.title(APP_TITLE)
    st.caption("Offline-first AI health assistant for community care workflows")

    with st.sidebar:
        st.subheader("Session")
        st.selectbox("Language", SUPPORTED_LANGUAGES, key="language")
        st.text_input("Patient name", key="patient_name")
        st.text_area("Clinical notes", key="notes", height=120)

    tabs = st.tabs(["Home", "Consultation", "Results", "Settings"])
    with tabs[0]:
        render_home()
    with tabs[1]:
        render_consultation()
    with tabs[2]:
        render_results()
    with tabs[3]:
        render_settings()


if __name__ == "__main__":
    main()
