import streamlit as st

from app.utils.config import APP_MODE, SUPPORTED_LANGUAGES


def render_settings() -> None:
    st.subheader("Settings")
    st.write(f"Current mode: **{APP_MODE}**")
    st.write("Supported languages:")
    for language in SUPPORTED_LANGUAGES:
        st.write(f"- {language}")
    st.caption("For full phone workflow use the PWA. For terminal workflow use the CLI.")
