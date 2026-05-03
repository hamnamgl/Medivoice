import streamlit as st


def render_home() -> None:
    st.subheader("Welcome")
    st.write(
        "Medivoice helps community health workers capture patient concerns, "
        "run basic protocol-guided triage, and document referrals even when "
        "internet access is unreliable."
    )
    st.info(
        "This starter scaffold is ready for offline-first workflows, local model "
        "integration, and multilingual data collection."
    )
