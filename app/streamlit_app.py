from __future__ import annotations

import html

import streamlit as st

from app.core.function_caller import run_agent
from app.utils.config import APP_MODE, DEFAULT_MODEL, SUPPORTED_LANGUAGES
from app.utils.local_db import get_recent_visits, get_stats, init_db, log_visit


st.set_page_config(page_title="MediVoice", page_icon="M", layout="wide")


def _ensure_state() -> None:
    st.session_state.setdefault("history", [])
    st.session_state.setdefault("messages", [])
    st.session_state.setdefault("selected_language", "English")
    st.session_state.setdefault("last_result", None)


def _inject_styles() -> None:
    st.markdown(
        """
        <style>
        .stApp {
            background:
                radial-gradient(circle at top left, rgba(41, 98, 255, 0.12), transparent 32%),
                radial-gradient(circle at top right, rgba(15, 118, 110, 0.18), transparent 28%),
                linear-gradient(180deg, #f5f7f4 0%, #eef2ee 100%);
        }
        .medivoice-shell {
            padding: 0.4rem 0 1.2rem 0;
        }
        .hero-card,
        .panel-card,
        .message-card {
            background: rgba(255, 255, 255, 0.86);
            border: 1px solid rgba(15, 23, 42, 0.08);
            border-radius: 22px;
            box-shadow: 0 20px 60px rgba(15, 23, 42, 0.08);
            backdrop-filter: blur(8px);
        }
        .hero-card {
            padding: 1.5rem;
            margin-bottom: 1rem;
        }
        .hero-kicker {
            display: inline-block;
            padding: 0.28rem 0.72rem;
            border-radius: 999px;
            background: #dff4ea;
            color: #0f766e;
            font-size: 0.78rem;
            font-weight: 700;
            letter-spacing: 0.04em;
            text-transform: uppercase;
        }
        .hero-title {
            margin: 0.8rem 0 0.35rem 0;
            font-size: 2.15rem;
            font-weight: 800;
            color: #172033;
            line-height: 1.1;
        }
        .hero-copy {
            color: #425466;
            font-size: 1rem;
            max-width: 48rem;
            line-height: 1.6;
        }
        .hero-grid {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 0.8rem;
            margin-top: 1rem;
        }
        .hero-stat {
            background: linear-gradient(180deg, #fcfffd 0%, #f2f8f5 100%);
            border: 1px solid #d9e5de;
            border-radius: 18px;
            padding: 0.9rem 1rem;
        }
        .hero-stat-label {
            color: #5f6c7b;
            font-size: 0.78rem;
            text-transform: uppercase;
            letter-spacing: 0.04em;
        }
        .hero-stat-value {
            color: #172033;
            font-size: 1.18rem;
            font-weight: 800;
            margin-top: 0.15rem;
        }
        .section-label {
            color: #5f6c7b;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            font-size: 0.76rem;
            font-weight: 700;
            margin-bottom: 0.35rem;
        }
        .severity-banner {
            padding: 0.95rem 1rem;
            border-radius: 18px;
            font-weight: 700;
            margin-bottom: 0.8rem;
        }
        .severity-emergency {
            background: #fff1f1;
            color: #9f1239;
            border: 1px solid #fecdd3;
        }
        .severity-refer {
            background: #fff9eb;
            color: #92400e;
            border: 1px solid #fde68a;
        }
        .severity-home {
            background: #edfdf4;
            color: #166534;
            border: 1px solid #bbf7d0;
        }
        .message-card {
            padding: 0.95rem 1rem;
            margin-bottom: 0.75rem;
        }
        .message-user {
            border-left: 4px solid #2563eb;
        }
        .message-assistant {
            border-left: 4px solid #0f766e;
        }
        .message-role {
            font-size: 0.76rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: #5f6c7b;
            margin-bottom: 0.3rem;
            font-weight: 700;
        }
        .panel-card {
            padding: 1rem;
            margin-bottom: 1rem;
        }
        .helper-copy {
            color: #556270;
            font-size: 0.92rem;
            line-height: 1.55;
        }
        @media (max-width: 900px) {
            .hero-grid {
                grid-template-columns: 1fr;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _get_severity(result: dict | None) -> str | None:
    if not result:
        return None
    tool_result = result.get("tool_result")
    if isinstance(tool_result, dict) and tool_result.get("level"):
        return str(tool_result["level"]).upper()
    response = str(result.get("response", ""))
    for prefix in ("EMERGENCY", "REFER TO CLINIC", "HOME CARE"):
        if response.upper().startswith(prefix):
            return prefix
    return None


def _severity_banner(result: dict | None) -> None:
    severity = _get_severity(result)
    if not severity:
        return

    styles = {
        "EMERGENCY": ("severity-emergency", "Emergency case detected. Escalate to hospital care immediately."),
        "REFER TO CLINIC": ("severity-refer", "Clinic review recommended today based on current symptom pattern."),
        "HOME CARE": ("severity-home", "Home-care guidance is reasonable for now. Monitor for worsening signs."),
        "REFER": ("severity-refer", "Clinic review recommended today based on current symptom pattern."),
    }
    css_class, label = styles.get(severity, ("severity-home", severity.title()))
    st.markdown(
        f"<div class='severity-banner {css_class}'>{label}</div>",
        unsafe_allow_html=True,
    )


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
    st.markdown("<div class='medivoice-shell'>", unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class="hero-card">
          <div class="hero-kicker">Offline clinical support</div>
          <div class="hero-title">MediVoice laptop demo for frontline triage workflows</div>
          <div class="hero-copy">
            Guided symptom capture, referral lookup, dosage support, and local visit logging in one
            operator-friendly surface. This companion UI is tuned for demos, reviews, and field simulation.
          </div>
          <div class="hero-grid">
            <div class="hero-stat">
              <div class="hero-stat-label">Mode</div>
              <div class="hero-stat-value">{APP_MODE}</div>
            </div>
            <div class="hero-stat">
              <div class="hero-stat-label">Primary model</div>
              <div class="hero-stat-value">{DEFAULT_MODEL}</div>
            </div>
            <div class="hero-stat">
              <div class="hero-stat-label">Languages ready</div>
              <div class="hero-stat-value">{len(SUPPORTED_LANGUAGES)}</div>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.info(
        "Use this surface for laptop demos and operator walkthroughs. For phone-first review use the PWA, and for terminal-only use run `python -m app.main`."
    )


def _render_messages() -> None:
    for item in st.session_state["messages"]:
        role = item["role"]
        role_label = "Field worker input" if role == "user" else "MediVoice response"
        role_class = "message-user" if role == "user" else "message-assistant"
        st.markdown(
            f"""
            <div class="message-card {role_class}">
              <div class="message-role">{role_label}</div>
              <div>{html.escape(str(item["content"]))}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if role == "assistant" and item.get("explanation"):
            with st.expander("Why this answer?", expanded=False):
                st.json(item["explanation"])


def _extract_action_and_severity(response: str) -> tuple[str, str]:
    response_upper = response.upper()
    if response_upper.startswith("EMERGENCY"):
        return "FORAN HOSPITAL", "EMERGENCY"
    if response_upper.startswith("REFER TO CLINIC") or response_upper.startswith("REFER"):
        return "CLINIC REFER KAREIN", "REFER"
    return "GHAR PE DEKHBHAL", "HOME CARE"


def _handle_user_message(message: str) -> None:
    st.session_state["messages"].append({"role": "user", "content": message})
    result = run_agent(message, st.session_state["history"])
    st.session_state["history"] = result["history"]
    st.session_state["last_result"] = result
    st.session_state["messages"].append(
        {
            "role": "assistant",
            "content": result["response"],
            "explanation": result.get("explanation"),
        }
    )
    action, severity = _extract_action_and_severity(result["response"])
    log_visit(
        symptoms=message,
        severity=severity,
        action=action,
        language=st.session_state.get("selected_language", "unknown"),
        tool_used=result.get("tool_used"),
        response=result["response"],
    )


def _show_quick_actions() -> None:
    st.markdown("<div class='section-label'>Quick prompts</div>", unsafe_allow_html=True)
    prompt_columns = st.columns(3)
    quick_prompts = [
        "Bachche ko 3 din se bukhar hai aur woh kuch nahi kha raha.",
        "What is the paracetamol dosage for a 15kg child?",
        "Nearest clinic for a patient in Punjab please.",
    ]
    for column, prompt in zip(prompt_columns, quick_prompts):
        if column.button(prompt, use_container_width=True):
            _handle_user_message(prompt)
            st.rerun()


def _show_ops_panels() -> None:
    stats = get_stats()
    recent = get_recent_visits(3)
    left, right = st.columns((1.2, 1))

    with left:
        st.markdown("<div class='panel-card'>", unsafe_allow_html=True)
        st.markdown("<div class='section-label'>Session snapshot</div>", unsafe_allow_html=True)
        metrics = st.columns(3)
        metrics[0].metric("Visits", stats["total_visits"])
        metrics[1].metric("Emergency", stats["emergencies"])
        metrics[2].metric("Referrals", stats["referrals"])
        st.caption(f"Home care cases: {stats['home_care']}")
        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown("<div class='panel-card'>", unsafe_allow_html=True)
        st.markdown("<div class='section-label'>Deployment note</div>", unsafe_allow_html=True)
        st.markdown(
            "<div class='helper-copy'>"
            "Demo mode is useful for reviews and judging, but true offline behavior requires Ollama and the model to be present on the same device or local network."
            "</div>",
            unsafe_allow_html=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='panel-card'>", unsafe_allow_html=True)
    st.markdown("<div class='section-label'>Recent local activity</div>", unsafe_allow_html=True)
    if recent:
        for row in recent:
            st.write(
                f"{row['timestamp']} | {row['language']} | {row['severity']} | {row['symptoms']}"
            )
    else:
        st.write("No visits logged yet.")
    st.markdown("</div>", unsafe_allow_html=True)


def main() -> None:
    init_db()
    _ensure_state()
    _inject_styles()
    _show_sidebar()
    _show_intro()
    _severity_banner(st.session_state.get("last_result"))

    main_left, main_right = st.columns((1.6, 1), gap="large")

    with main_left:
        _show_quick_actions()
        _render_messages()
        if prompt := st.chat_input("Describe patient symptoms, ask for dosage, or request a referral..."):
            _handle_user_message(prompt)
            st.rerun()

    with main_right:
        st.markdown("<div class='panel-card'>", unsafe_allow_html=True)
        st.markdown("<div class='section-label'>Operator guide</div>", unsafe_allow_html=True)
        st.markdown(
            "<div class='helper-copy'>"
            "Keep messages short and concrete. Mention duration, breathing issues, bleeding, feeding problems, weight in kg for dosage, or location for referral lookup."
            "</div>",
            unsafe_allow_html=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)
        _show_ops_panels()

    st.markdown("</div>", unsafe_allow_html=True)


if __name__ == "__main__":
    main()
