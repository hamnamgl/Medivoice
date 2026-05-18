import streamlit as st


def render_home() -> None:
    st.subheader("Welcome")
    st.write(
        "MediVoice helps community health workers capture patient concerns, "
        "run guided triage, and document referrals even when "
        "internet access is unreliable."
    )
    st.info(
        "This Streamlit layer is a lightweight laptop demo surface over the same "
        "offline-first routing used by the CLI and PWA."
    )
