from __future__ import annotations

import html

import streamlit as st

from app.core.function_caller import run_agent
from app.utils.config import APP_MODE, DEFAULT_MODEL, FALLBACK_MODEL, SUPPORTED_INPUTS, SUPPORTED_LANGUAGES
from app.utils.local_db import get_recent_visits, get_stats, init_db, log_visit


st.set_page_config(page_title="MediVoice", page_icon="M", layout="wide")

QUICK_PROMPTS = [
    "Bachche ko 3 din se bukhar hai aur woh kuch nahi kha raha.",
    "What is the paracetamol dosage for a 15kg child?",
    "Where is the nearest hospital in Punjab?",
    "Patient is unconscious and not breathing.",
]

GUIDE_CARDS = [
    (
        "When Ollama is used",
        "Ollama hosts the local model endpoint and serves every consultation response.",
        "Used in both local demo mode and remote tunnel demo mode.",
    ),
    (
        "When Gemma is used",
        "Gemma handles symptom understanding, same-language replies, and guided next-step reasoning.",
        "Primary and fallback model paths are shown below for demo clarity.",
    ),
    (
        "How to use MediVoice",
        "Choose a language, enter symptoms, then ask dosage with weight in kg or referral with a place name.",
        "Short, concrete prompts work best for field workflows.",
    ),
    (
        "Language support",
        ", ".join(SUPPORTED_LANGUAGES),
        f"{len(SUPPORTED_LANGUAGES)} UI language choices are configured in the repo.",
    ),
    (
        "Input support",
        ", ".join(SUPPORTED_INPUTS).title(),
        "This Streamlit surface is chat-first, while the broader app stack also covers voice and image workflows.",
    ),
]


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
                radial-gradient(circle at top left, rgba(33, 65, 61, 0.14), transparent 26%),
                radial-gradient(circle at top right, rgba(196, 108, 47, 0.12), transparent 22%),
                linear-gradient(180deg, #f4f7f3 0%, #ebf0ec 100%);
        }
        .medivoice-shell {
            padding: 0.2rem 0 1.2rem 0;
        }
        .hero-card,
        .panel-card,
        .message-card,
        .guide-card,
        .overview-card {
            background: rgba(255, 255, 255, 0.90);
            border: 1px solid rgba(15, 23, 42, 0.08);
            border-radius: 22px;
            box-shadow: 0 18px 46px rgba(15, 23, 42, 0.08);
            backdrop-filter: blur(8px);
        }
        .hero-card {
            position: relative;
            overflow: hidden;
            padding: 1.5rem;
            margin-bottom: 1rem;
            background: linear-gradient(135deg, rgba(33, 65, 61, 0.96), rgba(42, 81, 96, 0.94));
            color: #f4fbf7;
        }
        .hero-card::after {
            content: "";
            position: absolute;
            width: 320px;
            height: 320px;
            right: -120px;
            top: -140px;
            border-radius: 999px;
            background: radial-gradient(circle, rgba(255,255,255,0.14) 0%, rgba(255,255,255,0) 70%);
        }
        .hero-kicker {
            display: inline-block;
            padding: 0.30rem 0.72rem;
            border-radius: 999px;
            background: rgba(255, 255, 255, 0.12);
            border: 1px solid rgba(255,255,255,0.18);
            color: #e8f8ef;
            font-size: 0.76rem;
            font-weight: 700;
            letter-spacing: 0.04em;
            text-transform: uppercase;
        }
        .hero-title {
            margin: 0.8rem 0 0.35rem 0;
            font-size: 2.25rem;
            font-weight: 800;
            color: #ffffff;
            line-height: 1.06;
            max-width: 52rem;
        }
        .hero-copy {
            color: rgba(245, 251, 247, 0.84);
            font-size: 1rem;
            max-width: 48rem;
            line-height: 1.6;
        }
        .hero-grid,
        .overview-grid,
        .guide-grid {
            display: grid;
            gap: 0.8rem;
            margin-top: 1rem;
        }
        .hero-grid {
            grid-template-columns: repeat(3, minmax(0, 1fr));
        }
        .overview-grid {
            grid-template-columns: 1.2fr 0.8fr 0.8fr 0.8fr;
            margin-bottom: 1rem;
        }
        .guide-grid {
            grid-template-columns: repeat(5, minmax(0, 1fr));
            margin-bottom: 1rem;
        }
        .hero-stat {
            background: rgba(255, 255, 255, 0.08);
            border: 1px solid rgba(255, 255, 255, 0.10);
            border-radius: 18px;
            padding: 0.95rem 1rem;
        }
        .hero-stat-label {
            color: rgba(245, 251, 247, 0.72);
            font-size: 0.76rem;
            text-transform: uppercase;
            letter-spacing: 0.04em;
        }
        .hero-stat-value {
            color: #ffffff;
            font-size: 1.16rem;
            font-weight: 800;
            margin-top: 0.18rem;
        }
        .hero-stat-copy {
            color: rgba(245, 251, 247, 0.68);
            font-size: 0.77rem;
            line-height: 1.48;
            margin-top: 0.4rem;
        }
        .section-label {
            color: #5f6c7b;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            font-size: 0.74rem;
            font-weight: 700;
            margin-bottom: 0.45rem;
        }
        .overview-card,
        .guide-card {
            padding: 1rem;
            min-height: 142px;
        }
        .overview-card h3,
        .guide-card h3 {
            color: #172033;
            font-size: 0.95rem;
            margin-bottom: 0.4rem;
        }
        .overview-card p,
        .guide-card p,
        .helper-copy {
            color: #556270;
            font-size: 0.90rem;
            line-height: 1.56;
        }
        .guide-meta {
            margin-top: 0.65rem;
            font-size: 0.73rem;
            font-weight: 700;
            letter-spacing: 0.04em;
            text-transform: uppercase;
            color: #21413d;
        }
        .overview-badge {
            display: inline-block;
            margin: 0.25rem 0.35rem 0 0;
            padding: 0.35rem 0.62rem;
            border-radius: 999px;
            background: rgba(33, 65, 61, 0.08);
            color: #21413d;
            font-size: 0.74rem;
            font-weight: 700;
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
            padding: 1rem 1rem 0.9rem 1rem;
            margin-bottom: 0.75rem;
        }
        .message-user {
            border-left: 4px solid #2563eb;
        }
        .message-assistant {
            border-left: 4px solid #0f766e;
        }
        .message-role {
            font-size: 0.74rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: #5f6c7b;
            margin-bottom: 0.3rem;
            font-weight: 700;
        }
        .message-hint {
            margin-top: 0.55rem;
            font-size: 0.78rem;
            color: #5f6c7b;
            line-height: 1.45;
        }
        .panel-card {
            padding: 1rem;
            margin-bottom: 1rem;
        }
        .empty-state {
            background: linear-gradient(180deg, rgba(255,255,255,0.88), rgba(247,249,248,0.92));
            border: 1px dashed rgba(33, 65, 61, 0.18);
            border-radius: 22px;
            padding: 1rem;
            color: #556270;
            line-height: 1.6;
            margin-bottom: 0.8rem;
        }
        .empty-state strong {
            display: block;
            color: #172033;
            font-size: 1rem;
            margin-bottom: 0.35rem;
        }
        @media (max-width: 1100px) {
            .hero-grid,
            .overview-grid,
            .guide-grid {
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
    st.sidebar.write(f"Primary model: `{DEFAULT_MODEL}`")
    st.sidebar.write(f"Fallback model: `{FALLBACK_MODEL}`")
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
    st.sidebar.metric("Home care", stats["home_care"])

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
            operator-friendly surface. This companion UI is tuned for polished demos, reviews, and field simulation.
          </div>
          <div class="hero-grid">
            <div class="hero-stat">
              <div class="hero-stat-label">Mode</div>
              <div class="hero-stat-value">{APP_MODE}</div>
              <div class="hero-stat-copy">Offline-first workflow for operator review and frontline simulation.</div>
            </div>
            <div class="hero-stat">
              <div class="hero-stat-label">Primary model</div>
              <div class="hero-stat-value">{DEFAULT_MODEL}</div>
              <div class="hero-stat-copy">Preferred model path for guided consultation responses.</div>
            </div>
            <div class="hero-stat">
              <div class="hero-stat-label">Fallback model</div>
              <div class="hero-stat-value">{FALLBACK_MODEL}</div>
              <div class="hero-stat-copy">Backup route when the primary model path is not available.</div>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.info(
        "Use this surface for laptop demos and operator walkthroughs. For phone-first review use the PWA, and for terminal-only use run `python -m app.main`."
    )


def _show_overview() -> None:
    st.markdown("<div class='section-label'>At a glance</div>", unsafe_allow_html=True)
    st.markdown(
        """
        <div class="overview-grid">
          <div class="overview-card">
            <h3>Consultation workflow</h3>
            <p>Choose a language, enter symptoms, and let MediVoice guide the conversation toward a home-care, referral, or emergency next step.</p>
            <span class="overview-badge">Same-language replies</span>
            <span class="overview-badge">Short clinical flow</span>
            <span class="overview-badge">Offline-first design</span>
          </div>
          <div class="overview-card">
            <h3>Dosage support</h3>
            <p>Ask a medicine question with weight in kilograms for a direct local dosage response.</p>
          </div>
          <div class="overview-card">
            <h3>Referral support</h3>
            <p>Ask for the nearest clinic or hospital using a place name such as Punjab or Nairobi.</p>
          </div>
          <div class="overview-card">
            <h3>Demo mode</h3>
            <p>Use this Streamlit surface for laptop review while keeping the same underlying app logic.</p>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _show_guide_grid() -> None:
    st.markdown("<div class='section-label'>Platform guide</div>", unsafe_allow_html=True)
    cards = []
    for title, copy, meta in GUIDE_CARDS:
        cards.append(
            f"""
            <div class="guide-card">
              <h3>{html.escape(title)}</h3>
              <p>{html.escape(copy)}</p>
              <div class="guide-meta">{html.escape(meta)}</div>
            </div>
            """
        )
    st.markdown(f"<div class='guide-grid'>{''.join(cards)}</div>", unsafe_allow_html=True)


def _message_hint(content: str) -> str:
    upper = content.upper()
    if upper.startswith("EMERGENCY"):
        return "Escalate immediately and avoid delaying referral to higher care."
    if upper.startswith("REFER TO CLINIC") or upper.startswith("REFER"):
        return "Use this when the patient needs same-day clinic review or a facility handoff."
    if upper.startswith("HOME CARE"):
        return "Home-care advice is for the current symptoms only. Reassess if the patient worsens."
    return ""


def _render_messages() -> None:
    if not st.session_state["messages"]:
        st.markdown(
            """
            <div class="empty-state">
              <strong>Ready for a new consultation</strong>
              Use a short symptom description, try one of the sample prompts below, or ask for dosage with weight in kg.
              Tip: include duration, breathing trouble, feeding issues, bleeding, or a place name for faster routing.
            </div>
            """,
            unsafe_allow_html=True,
        )

    for item in st.session_state["messages"]:
        role = item["role"]
        role_label = "Field worker input" if role == "user" else "MediVoice response"
        role_class = "message-user" if role == "user" else "message-assistant"
        hint = _message_hint(str(item["content"])) if role == "assistant" else ""
        hint_html = f"<div class='message-hint'>{html.escape(hint)}</div>" if hint else ""
        st.markdown(
            f"""
            <div class="message-card {role_class}">
              <div class="message-role">{role_label}</div>
              <div>{html.escape(str(item["content"]))}</div>
              {hint_html}
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
    columns = st.columns(4)
    for column, prompt in zip(columns, QUICK_PROMPTS):
        if column.button(prompt, use_container_width=True):
            _handle_user_message(prompt)
            st.rerun()


def _show_ops_panels() -> None:
    stats = get_stats()
    recent = get_recent_visits(4)

    st.markdown("<div class='panel-card'>", unsafe_allow_html=True)
    st.markdown("<div class='section-label'>Operator guide</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='helper-copy'>"
        "Keep messages short and concrete. Mention duration, breathing issues, bleeding, feeding problems, weight in kg for dosage, or location for referral lookup."
        "</div>",
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='panel-card'>", unsafe_allow_html=True)
    st.markdown("<div class='section-label'>Runtime clarity</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='helper-copy'>"
        f"Ollama serves the local model runtime. {DEFAULT_MODEL} is the primary consultation model and {FALLBACK_MODEL} is the backup path when needed."
        "</div>",
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='panel-card'>", unsafe_allow_html=True)
    st.markdown("<div class='section-label'>Session snapshot</div>", unsafe_allow_html=True)
    metrics = st.columns(3)
    metrics[0].metric("Visits", stats["total_visits"])
    metrics[1].metric("Emergency", stats["emergencies"])
    metrics[2].metric("Referrals", stats["referrals"])
    st.caption(f"Home care cases: {stats['home_care']}")
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
    _show_overview()
    _show_guide_grid()
    _severity_banner(st.session_state.get("last_result"))

    main_left, main_right = st.columns((1.7, 1), gap="large")

    with main_left:
        _show_quick_actions()
        _render_messages()
        if prompt := st.chat_input("Describe patient symptoms, ask for dosage, or request a referral..."):
            _handle_user_message(prompt)
            st.rerun()

    with main_right:
        _show_ops_panels()

    st.markdown("</div>", unsafe_allow_html=True)


if __name__ == "__main__":
    main()
