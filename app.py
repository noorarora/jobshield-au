from __future__ import annotations

import html

import streamlit as st

from hybrid_engine import analyse_hybrid
from ml_model import load_metrics, model_available

st.set_page_config(
    page_title="JobShield AU — Job Scam Detector",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

metrics = load_metrics() or {}


def load_suspicious_sample() -> None:
    st.session_state["input_text"] = (
        "Hi there! We have a remote data entry position with weekly pay of $3,000–$5,000. "
        "No experience is needed and no interview is required. To get started, please make a "
        "small verification payment of $150 in USDT. Contact our recruiter on WhatsApp for the next steps."
    )
    st.session_state["company_domain"] = "example.com"
    st.session_state["recruiter_email"] = "jobs.team.hr@gmail.com"


SIGNAL_COPY = {
    "Upfront payment requested": "The message asks the applicant to pay a fee before employment begins.",
    "Cryptocurrency mentioned": "Cryptocurrency appears in the recruitment or payment process.",
    "Money transfer requested": "The message requests a bank, wire or direct money transfer.",
    "Sensitive identity request": "Sensitive identity or financial information is requested.",
    "Moved to private messaging app": "The conversation is being pushed to WhatsApp, Telegram or Signal.",
    "Urgency / pressure language": "The wording creates pressure to act quickly instead of verifying the role.",
    "Unrealistic income claim": "The pay or earning claim appears unusually high for the effort described.",
    "No formal hiring process": "The message suggests hiring without a normal interview or selection process.",
    "Generic recruiter language": "The recruiter message uses broad, non-personalised language.",
    "Recruiter uses a free email provider": "A free consumer email account is being used for recruitment communication.",
}


st.markdown(
    """
<style>
:root {
    --bg: #F8FAFC;
    --surface: #FFFFFF;
    --surface-soft: #F1F5F9;
    --text: #0F172A;
    --text-2: #334155;
    --muted: #64748B;
    --border: #E2E8F0;
    --border-strong: #CBD5E1;
    --blue: #2563EB;
    --blue-hover: #1D4ED8;
    --blue-soft: #EFF6FF;
    --green: #059669;
    --green-soft: #ECFDF5;
    --amber: #D97706;
    --amber-soft: #FFFBEB;
    --red: #DC2626;
    --red-dark: #B91C1C;
    --red-soft: #FEF2F2;
}

html, body, [class*="css"] {
    font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}
.stApp {
    background: var(--bg);
    color: var(--text);
}
[data-testid="stHeader"], [data-testid="stToolbar"], [data-testid="stDecoration"] {display:none !important;}
[data-testid="stAppViewContainer"] {background:var(--bg) !important;}
[data-stale="true"] {opacity:1 !important;}
.block-container {max-width: 1180px; padding-top: 1.35rem; padding-bottom: 3rem;}

/* Hide Streamlit chrome noise while keeping the app usable */
#MainMenu {visibility:hidden;}
footer {visibility:hidden;}
[data-testid="stStatusWidget"] {display:none !important;}

/* Navigation */
.topbar {
    display:flex; align-items:center; justify-content:space-between;
    padding:.55rem 0 1rem; border-bottom:1px solid var(--border); margin-bottom:1.4rem;
}
.brand {display:flex; align-items:center; gap:.7rem;}
.logo-shield {width:38px; height:42px; display:grid; place-items:center;}
.brand-name {font-size:1.05rem; font-weight:800; letter-spacing:-.02em; color:var(--text);}
.au-badge {font-size:.64rem; font-weight:800; letter-spacing:.08em; padding:.2rem .4rem; border-radius:6px; background:var(--blue-soft); color:var(--blue); border:1px solid #DBEAFE;}
.status-pill {display:flex; align-items:center; gap:.42rem; font-size:.74rem; font-weight:650; color:var(--text-2); background:var(--surface); border:1px solid var(--border); padding:.42rem .65rem; border-radius:999px;}
.status-dot {width:7px; height:7px; border-radius:50%; background:var(--green);}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    gap: 1.35rem; background: transparent; border-bottom:1px solid var(--border);
    padding:0; border-radius:0; margin:0 0 1.7rem;
}
.stTabs [data-baseweb="tab"] {
    height: 3rem; padding:0 .15rem; color:var(--muted); font-weight:650; font-size:.9rem;
}
.stTabs [aria-selected="true"] {color:var(--text) !important;}
.stTabs [data-baseweb="tab-highlight"] {background:var(--blue); height:2px;}

/* Hero */
.hero {padding:1.3rem 0 1.55rem;}
.eyebrow {font-size:.72rem; font-weight:750; color:var(--blue); letter-spacing:.08em; text-transform:uppercase; margin-bottom:.7rem;}
.hero h1 {font-size:clamp(2.2rem,4.2vw,3.55rem); line-height:1.02; letter-spacing:-.055em; margin:0; color:var(--text); font-weight:800; max-width:780px;}
.hero h1 span {color:var(--blue);}
.hero p {font-size:1rem; color:var(--muted); line-height:1.65; max-width:720px; margin:.85rem 0 .75rem;}
.cred-line {display:flex; align-items:center; gap:.55rem; color:var(--muted); font-size:.78rem; margin-top:.85rem;}
.cred-check {display:grid; place-items:center; width:20px; height:20px; border-radius:50%; background:var(--green-soft); color:var(--green); font-weight:800; font-size:.7rem;}

/* General cards */
.card {background:var(--surface); border:1px solid var(--border); border-radius:14px; box-shadow:0 1px 2px rgba(15,23,42,.035);}
.card-pad {padding:1.25rem;}
.section-label {font-size:.7rem; color:var(--blue); font-weight:750; letter-spacing:.07em; text-transform:uppercase; margin-bottom:.35rem;}
.section-title {font-size:1.1rem; color:var(--text); font-weight:750; letter-spacing:-.02em; margin:0 0 .35rem;}
.section-copy {font-size:.84rem; color:var(--muted); line-height:1.55; margin-bottom:.8rem;}
.helper {font-size:.72rem; color:var(--muted); line-height:1.45;}

/* Inputs + buttons */
.stTextArea textarea, .stTextInput input {
    background:#FFFFFF !important; color:var(--text) !important;
    border:1px solid var(--border-strong) !important; border-radius:9px !important;
    box-shadow:none !important;
}
.stTextArea textarea::placeholder, .stTextInput input::placeholder {color:#94A3B8 !important; opacity:1 !important;}
[data-testid="stTextInput"] label, [data-testid="stTextInput"] label p,
[data-testid="stTextArea"] label, [data-testid="stTextArea"] label p {color:var(--text-2) !important;}
.stTextArea textarea:focus, .stTextInput input:focus {
    border-color:var(--blue) !important; box-shadow:0 0 0 3px rgba(37,99,235,.10) !important;
}
.stTextArea textarea {min-height:255px !important;}
.stButton > button {
    min-height:2.75rem; border-radius:9px; font-weight:700; font-size:.88rem;
    border:1px solid var(--border-strong); background:#FFFFFF; color:var(--text-2); box-shadow:none;
}
.stButton > button:hover {border-color:#94A3B8; color:var(--text); background:#F8FAFC;}
.stButton > button[kind="primary"] {
    background:var(--blue); color:#FFFFFF; border:1px solid var(--blue); box-shadow:0 1px 2px rgba(37,99,235,.18);
}
.stButton > button[kind="primary"]:hover {background:var(--blue-hover); border-color:var(--blue-hover); color:#FFFFFF;}
[data-testid="stExpander"] {background:var(--surface); border:1px solid var(--border); border-radius:12px; box-shadow:none;}

/* Verification status */
.engine-row {display:flex; align-items:flex-start; gap:.6rem; background:var(--green-soft); border:1px solid #D1FAE5; border-radius:10px; padding:.8rem .85rem; margin-top:.7rem;}
.engine-icon {width:26px; height:26px; border-radius:8px; display:grid; place-items:center; background:#D1FAE5; color:var(--green); font-size:.76rem; font-weight:800; flex:0 0 26px;}
.engine-title {font-size:.8rem; font-weight:750; color:#065F46;}
.engine-copy {font-size:.72rem; color:#047857; line-height:1.4; margin-top:.08rem;}

/* Results */
.result-head {display:flex; align-items:center; justify-content:space-between; margin:2rem 0 .8rem;}
.result-head h2 {font-size:1.5rem; margin:0; letter-spacing:-.03em; color:var(--text);}
.result-head .small {font-size:.75rem; color:var(--muted);}
.result-grid {display:grid; grid-template-columns:270px 1fr; gap:.85rem; align-items:stretch;}
.score-card {padding:1.25rem; display:flex; flex-direction:column; justify-content:space-between; min-height:255px;}
.score-top {font-size:.75rem; font-weight:700; color:var(--muted);}
.score-number {font-size:4.15rem; line-height:.95; font-weight:800; letter-spacing:-.07em; color:var(--text); margin:.65rem 0 .25rem;}
.score-number span {font-size:1rem; color:#94A3B8; letter-spacing:0; font-weight:650;}
.risk-pill {display:inline-flex; align-items:center; width:fit-content; padding:.34rem .55rem; border-radius:999px; font-size:.7rem; font-weight:800; letter-spacing:.05em; text-transform:uppercase;}
.risk-pill.high {background:var(--red-soft); color:var(--red-dark); border:1px solid #FECACA;}
.risk-pill.medium {background:var(--amber-soft); color:#B45309; border:1px solid #FDE68A;}
.risk-pill.low {background:var(--green-soft); color:#047857; border:1px solid #A7F3D0;}
.score-copy {font-size:.78rem; color:var(--muted); line-height:1.5; margin-top:.75rem;}
.score-bar {height:7px; width:100%; background:#E2E8F0; border-radius:999px; overflow:hidden; margin-top:1rem;}
.score-fill {height:100%; border-radius:999px;}
.score-fill.high {background:var(--red);}
.score-fill.medium {background:var(--amber);}
.score-fill.low {background:var(--green);}

.signals-card {padding:1.1rem 1.15rem;}
.signals-title-row {display:flex; align-items:center; justify-content:space-between; margin-bottom:.65rem;}
.signals-title {font-size:.95rem; font-weight:750; color:var(--text);}
.flag-count {font-size:.68rem; font-weight:750; color:var(--muted); background:var(--surface-soft); border:1px solid var(--border); padding:.25rem .42rem; border-radius:999px;}
.signal-list {display:flex; flex-direction:column; gap:.45rem;}
.signal-item {display:grid; grid-template-columns:9px 1fr auto; gap:.7rem; align-items:start; padding:.75rem .7rem; border:1px solid var(--border); border-radius:10px; background:#FFFFFF;}
.signal-dot {width:8px; height:8px; border-radius:50%; margin-top:.33rem;}
.signal-dot.high {background:var(--red);}
.signal-dot.medium {background:var(--amber);}
.signal-main {font-size:.81rem; font-weight:720; color:var(--text-2);}
.signal-sub {font-size:.71rem; color:var(--muted); line-height:1.4; margin-top:.12rem;}
.severity {font-size:.63rem; font-weight:800; letter-spacing:.05em; padding:.22rem .38rem; border-radius:6px; text-transform:uppercase;}
.severity.high {background:var(--red-soft); color:var(--red-dark);}
.severity.medium {background:var(--amber-soft); color:#B45309;}

/* Explainability */
.explain-grid {display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:.7rem; margin-top:.8rem;}
.explain-card {background:var(--surface); border:1px solid var(--border); border-radius:12px; padding:.95rem;}
.explain-kicker {font-size:.66rem; font-weight:750; color:var(--muted); text-transform:uppercase; letter-spacing:.05em;}
.explain-title {font-size:.86rem; font-weight:750; color:var(--text); margin:.25rem 0 .2rem;}
.explain-copy {font-size:.72rem; color:var(--muted); line-height:1.45;}
.term-list {display:flex; flex-wrap:wrap; gap:.35rem; margin-top:.55rem;}
.term-chip {font-size:.68rem; font-weight:650; color:#1E40AF; background:var(--blue-soft); border:1px solid #DBEAFE; border-radius:7px; padding:.28rem .42rem;}

/* Recommendation */
.reco {margin-top:.8rem; background:var(--surface); border:1px solid var(--border); border-radius:12px; padding:1rem;}
.reco.high {border-left:4px solid var(--red);}
.reco.medium {border-left:4px solid var(--amber);}
.reco.low {border-left:4px solid var(--green);}
.reco-title {font-size:.9rem; font-weight:780; color:var(--text); margin-bottom:.28rem;}
.reco-copy {font-size:.78rem; color:var(--text-2); line-height:1.5;}
.reco-actions {display:flex; flex-wrap:wrap; gap:.45rem; margin-top:.65rem;}
.reco-action {font-size:.7rem; color:var(--muted); background:var(--surface-soft); border:1px solid var(--border); border-radius:8px; padding:.38rem .5rem;}

/* Advanced analysis metrics */
.mini-metrics {display:grid; grid-template-columns:repeat(3,1fr); gap:.65rem; margin:.65rem 0;}
.mini-metric {background:var(--surface-soft); border:1px solid var(--border); border-radius:10px; padding:.75rem;}
.mm-v {font-size:1.1rem; font-weight:800; color:var(--text);}
.mm-k {font-size:.68rem; color:var(--muted); margin-top:.15rem;}

/* Model Insights */
.page-title {font-size:1.75rem; font-weight:800; color:var(--text); letter-spacing:-.035em; margin:.15rem 0 .35rem;}
.page-sub {font-size:.88rem; color:var(--muted); line-height:1.55; max-width:760px; margin-bottom:1.1rem;}
.metric-grid {display:grid; grid-template-columns:repeat(4,1fr); gap:.7rem;}
.metric-card {background:var(--surface); border:1px solid var(--border); border-radius:12px; padding:1rem;}
.metric-v {font-size:1.55rem; font-weight:800; color:var(--text); letter-spacing:-.035em;}
.metric-k {font-size:.72rem; color:var(--muted); margin-top:.15rem;}
.insight-grid {display:grid; grid-template-columns:1.08fr .92fr; gap:.8rem; margin-top:.8rem;}
.insight-card {background:var(--surface); border:1px solid var(--border); border-radius:12px; padding:1rem;}
.insight-card h3 {font-size:.92rem; margin:0 0 .2rem; color:var(--text);}
.insight-card p {font-size:.72rem; color:var(--muted); margin:.1rem 0 .7rem; line-height:1.45;}
.dataset-grid {display:grid; grid-template-columns:repeat(3,1fr); gap:.55rem;}
.dataset-stat {background:var(--surface-soft); border:1px solid var(--border); border-radius:9px; padding:.7rem;}
.dataset-stat strong {display:block; font-size:1.15rem; color:var(--text);}
.dataset-stat span {font-size:.66rem; color:var(--muted);}
.matrix {display:grid; grid-template-columns:88px 1fr 1fr; gap:5px; margin-top:.8rem;}
.matrix .m-label {display:flex; align-items:center; justify-content:center; min-height:50px; font-size:.64rem; color:var(--muted); text-align:center;}
.matrix .cell {display:flex; flex-direction:column; align-items:center; justify-content:center; min-height:70px; border-radius:8px; border:1px solid var(--border);}
.matrix .cell.good {background:#EFF6FF; color:#1E3A8A;}
.matrix .cell.bad {background:#FFF7ED; color:#9A3412;}
.matrix .cell strong {font-size:1.08rem;}
.matrix .cell span {font-size:.61rem; opacity:.75; margin-top:.1rem;}
.pipeline {display:flex; align-items:center; gap:.35rem; flex-wrap:wrap; margin-top:.8rem;}
.pipe-step {background:#FFFFFF; border:1px solid var(--border); border-radius:9px; padding:.55rem .65rem; font-size:.69rem; font-weight:700; color:var(--text-2);}
.pipe-arrow {color:#94A3B8; font-weight:700;}

/* About */
.about-grid {display:grid; grid-template-columns:repeat(2,1fr); gap:.75rem;}
.about-card {background:var(--surface); border:1px solid var(--border); border-radius:12px; padding:1rem;}
.about-card h3 {font-size:.9rem; color:var(--text); margin:0 0 .3rem;}
.about-card p {font-size:.76rem; color:var(--muted); line-height:1.55; margin:0;}
.tech-row {display:flex; flex-wrap:wrap; gap:.4rem; margin-top:.7rem;}
.tech {font-size:.69rem; font-weight:650; background:var(--surface-soft); border:1px solid var(--border); color:var(--text-2); padding:.35rem .48rem; border-radius:7px;}
.disclaimer {margin-top:1rem; color:var(--muted); font-size:.69rem; line-height:1.5; padding-top:.8rem; border-top:1px solid var(--border);}

@media (max-width: 900px) {
    .result-grid, .insight-grid {grid-template-columns:1fr;}
    .metric-grid {grid-template-columns:repeat(2,1fr);}
    .explain-grid, .about-grid {grid-template-columns:1fr;}
    .topbar {align-items:flex-start; gap:.8rem;}
}
@media (max-width: 620px) {
    .metric-grid, .mini-metrics, .dataset-grid {grid-template-columns:1fr;}
    .hero h1 {font-size:2.2rem;}
    .status-pill {display:none;}
}
</style>
""",
    unsafe_allow_html=True,
)


# Product header
st.markdown(
    """
<div class="topbar">
  <div class="brand">
    <div class="logo-shield" aria-hidden="true">
      <svg viewBox="0 0 40 44" width="38" height="42" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M20 2.5L35 8v10.2c0 10.1-6 18.7-15 23.3C11 36.9 5 28.3 5 18.2V8l15-5.5Z" fill="#EFF6FF" stroke="#2563EB" stroke-width="2.2"/>
        <path d="m13.5 21 4.3 4.2 8.7-9" stroke="#2563EB" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
    </div>
    <div class="brand-name">JobShield</div>
    <div class="au-badge">AU</div>
  </div>
  <div class="status-pill"><span class="status-dot"></span>Hybrid engine ready</div>
</div>
""",
    unsafe_allow_html=True,
)

analyse_tab, model_tab, about_tab = st.tabs(["Analyse", "Model Insights", "About"])

with analyse_tab:
    st.markdown(
        """
<div class="hero">
  <div class="eyebrow">Job-scam screening</div>
  <h1>Know before you <span>apply.</span></h1>
  <p>Analyse job advertisements and recruiter messages for suspicious recruitment patterns before sharing money, identity documents or personal information.</p>
  <div class="cred-line"><span class="cred-check">✓</span> Baseline trained from a 17,880-row labelled dataset; exact duplicates were removed before splitting.</div>
</div>
""",
        unsafe_allow_html=True,
    )

    input_col, verify_col = st.columns([1.6, 1], gap="large")

    with input_col:
        st.markdown(
            '<div class="section-label">01 · Screen content</div>'
            '<div class="section-title">Job or recruiter message</div>'
            '<div class="section-copy">Paste a job advertisement, recruiter email, SMS or messaging conversation.</div>',
            unsafe_allow_html=True,
        )
        text = st.text_area(
            "Job or recruiter message",
            key="input_text",
            label_visibility="collapsed",
            placeholder="Paste the job advertisement or recruiter message here…",
            height=275,
        )
        action_left, action_right = st.columns([2.4, 1])
        with action_left:
            analyse_clicked = st.button("Analyse for risk →", type="primary", use_container_width=True)
        with action_right:
            st.button("Load example", on_click=load_suspicious_sample, use_container_width=True)

    with verify_col:
        st.markdown(
            '<div class="section-label">02 · Add context</div>'
            '<div class="section-title">Verification context</div>'
            '<div class="section-copy">Optional details help identify contact and domain mismatches.</div>',
            unsafe_allow_html=True,
        )
        claimed_domain = st.text_input(
            "Official company domain",
            key="company_domain",
            placeholder="company.com",
            help="Use the employer's official website domain, without https://.",
        )
        recruiter_email = st.text_input(
            "Recruiter email",
            key="recruiter_email",
            placeholder="recruiter@company.com",
            help="Optional. This email is analysed together with the pasted message.",
        )
        st.markdown(
            """
<div class="engine-row">
  <div class="engine-icon">✓</div>
  <div>
    <div class="engine-title">Hybrid detection engine ready</div>
    <div class="engine-copy">NLP classifier + explainable rule checks are available locally.</div>
  </div>
</div>
""",
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="helper" style="margin-top:.7rem;">JobShield does not need an account and does not send your pasted text to an external LLM.</div>',
            unsafe_allow_html=True,
        )

    if analyse_clicked:
        if not text.strip() and not recruiter_email.strip():
            st.warning("Paste a job advertisement or recruiter message before analysing it.")
        else:
            analysis_text = text.strip()
            if recruiter_email.strip():
                analysis_text += f"\nRecruiter email: {recruiter_email.strip()}"
            try:
                st.session_state["last_result"] = analyse_hybrid(analysis_text, claimed_domain.strip())
                st.session_state["last_analysis_text"] = analysis_text
                st.session_state.pop("analysis_error", None)
            except Exception as exc:
                st.session_state["analysis_error"] = f"{type(exc).__name__}: {exc}"

    if st.session_state.get("analysis_error"):
        st.error("The analysis engine hit an unexpected local error. Refresh the app and try again.")

    result = st.session_state.get("last_result")
    if result:
        score = int(result.get("hybrid_score", result.get("score", 0)))
        level = result.get("hybrid_level", result.get("level", "Low"))
        level_class = level.lower()
        ml = result.get("ml", {})
        rule_score = int(result.get("rule_score", result.get("score", 0)))
        ml_prob = float(ml.get("probability") or 0.0)
        threshold = float(ml.get("threshold") or metrics.get("selected_threshold", 0.5) or 0.5)
        signals = result.get("signals", [])

        if level == "High":
            summary = "Multiple strong indicators commonly associated with fraudulent recruitment were detected."
        elif level == "Medium":
            summary = "Some suspicious recruitment patterns were detected. Verify the role before sharing sensitive information."
        else:
            summary = "No major high-risk indicators were detected by the current screening engine. Continue normal verification."

        signal_html = []
        for severity, label in signals:
            sev = "high" if severity == "high" else "medium"
            detail = SIGNAL_COPY.get(label, "This signal contributed to the screening result.")
            if label.startswith("Domain mismatch detected"):
                detail = "A contact or link domain does not match the official company domain you supplied."
            signal_html.append(
                f'<div class="signal-item"><span class="signal-dot {sev}"></span><div><div class="signal-main">{html.escape(label)}</div><div class="signal-sub">{html.escape(detail)}</div></div><span class="severity {sev}">{sev}</span></div>'
            )
        if not signal_html:
            signal_html.append(
                '<div class="signal-item"><span class="signal-dot low" style="background:#059669"></span><div><div class="signal-main">No major rule-based red flags detected</div><div class="signal-sub">This does not guarantee legitimacy; continue normal employer and recruiter verification.</div></div><span class="severity" style="background:#ECFDF5;color:#047857">low</span></div>'
            )

        st.markdown(
            f"""
<div class="result-head">
  <div><h2>Analysis result</h2><div class="small">Decision support — not a fraud verdict</div></div>
</div>
<div class="result-grid">
  <div class="card score-card">
    <div>
      <div class="score-top">Screening score</div>
      <div class="score-number">{score}<span> / 100</span></div>
      <span class="risk-pill {level_class}">{html.escape(level)} risk</span>
      <div class="score-copy">{html.escape(summary)}</div>
    </div>
    <div class="score-bar"><div class="score-fill {level_class}" style="width:{score}%"></div></div>
  </div>
  <div class="card signals-card">
    <div class="signals-title-row"><div class="signals-title">Detected risk signals</div><div class="flag-count">{len(signals)} flags</div></div>
    <div class="signal-list">{''.join(signal_html)}</div>
  </div>
</div>
""",
            unsafe_allow_html=True,
        )

        # Explainability section
        st.markdown(
            '<div class="section-title" style="margin-top:1.25rem;">Why JobShield flagged this</div>'
            '<div class="section-copy">The result combines explicit fraud signals with patterns learned by the NLP classifier.</div>',
            unsafe_allow_html=True,
        )

        explain_cards = []
        for severity, label in signals[:3]:
            detail = SIGNAL_COPY.get(label, "This rule contributed to the screening score.")
            if label.startswith("Domain mismatch detected"):
                detail = "A detected domain differs from the official domain supplied for verification."
            explain_cards.append(
                f'<div class="explain-card"><div class="explain-kicker">Rule signal</div><div class="explain-title">{html.escape(label)}</div><div class="explain-copy">{html.escape(detail)}</div></div>'
            )

        terms = ml.get("top_terms") or []
        if terms:
            chips = "".join(f'<span class="term-chip">{html.escape(str(t["term"]))}</span>' for t in terms[:6])
            explain_cards.append(
                f'<div class="explain-card"><div class="explain-kicker">NLP explanation</div><div class="explain-title">Influential text features</div><div class="explain-copy">Positive TF-IDF × model-coefficient contributions for this prediction.</div><div class="term-list">{chips}</div></div>'
            )

        if explain_cards:
            st.markdown(f'<div class="explain-grid">{"".join(explain_cards)}</div>', unsafe_allow_html=True)

        if level == "High":
            reco_title = "Do not send money or identity documents."
            reco_copy = "Verify the vacancy through the employer's official careers website before continuing communication."
        elif level == "Medium":
            reco_title = "Verify the recruiter and vacancy before continuing."
            reco_copy = "Use contact details found independently on the employer's official website and avoid sharing sensitive information until verified."
        else:
            reco_title = "Continue with normal verification."
            reco_copy = "A low score does not prove a role is genuine. Confirm the employer, vacancy and recruiter before sharing sensitive information."

        st.markdown(
            f"""
<div class="reco {level_class}">
  <div class="reco-title">Recommended action · {html.escape(reco_title)}</div>
  <div class="reco-copy">{html.escape(reco_copy)}</div>
  <div class="reco-actions">
    <span class="reco-action">Check official company website</span>
    <span class="reco-action">Verify recruiter email</span>
    <span class="reco-action">Avoid upfront payments</span>
    <span class="reco-action">Report suspicious activity</span>
  </div>
</div>
""",
            unsafe_allow_html=True,
        )

        with st.expander("Advanced analysis"):
            ml_display = f"{ml_prob:.0%}" if ml.get("available") else "Unavailable"
            st.markdown(
                f"""
<div class="mini-metrics">
  <div class="mini-metric"><div class="mm-v">{ml_display}</div><div class="mm-k">ML scam probability</div></div>
  <div class="mini-metric"><div class="mm-v">{rule_score}%</div><div class="mm-k">Rule-based risk</div></div>
  <div class="mini-metric"><div class="mm-v">{score}%</div><div class="mm-k">Combined screening score</div></div>
</div>
""",
                unsafe_allow_html=True,
            )
            st.caption(f"ML decision threshold: {threshold:.2f} · Fusion: {result.get('fusion', 'rules only')}")
            st.write("Emails detected:", result.get("emails") or "None")
            st.write("URLs detected:", result.get("urls") or "None")
            if ml.get("available"):
                st.write("ML model:", ml.get("model_name", "TF-IDF + Logistic Regression"))

with model_tab:
    st.markdown('<div class="eyebrow">Held-out evaluation</div><div class="page-title">Model performance</div><div class="page-sub">Evaluation on unseen job postings after exact duplicate combined texts were removed before train/validation/test splitting.</div>', unsafe_allow_html=True)

    if not metrics:
        st.info("No model metrics found. Run the training script first.")
    else:
        test = metrics.get("test", metrics)
        st.markdown(
            f"""
<div class="metric-grid">
  <div class="metric-card"><div class="metric-v">{test.get('f1_fraud',0):.1%}</div><div class="metric-k">Fraud F1</div></div>
  <div class="metric-card"><div class="metric-v">{test.get('precision_fraud',0):.1%}</div><div class="metric-k">Precision</div></div>
  <div class="metric-card"><div class="metric-v">{test.get('recall_fraud',0):.1%}</div><div class="metric-k">Recall</div></div>
  <div class="metric-card"><div class="metric-v">{test.get('roc_auc',0):.4f}</div><div class="metric-k">ROC-AUC</div></div>
</div>
""",
            unsafe_allow_html=True,
        )

        split = metrics.get("split", {})
        dist = metrics.get("raw_class_distribution", {})
        cm = test.get("confusion_matrix", [[0, 0], [0, 0]])
        tn, fp = cm[0]
        fn, tp = cm[1]

        st.markdown(
            f"""
<div class="insight-grid">
  <div class="insight-card">
    <h3>Dataset</h3>
    <p>Historical labelled job-posting data used to train and evaluate the screening model.</p>
    <div class="dataset-grid">
      <div class="dataset-stat"><strong>{metrics.get('raw_rows',0):,}</strong><span>labelled postings</span></div>
      <div class="dataset-stat"><strong>{dist.get('fraudulent',0):,}</strong><span>fraudulent postings</span></div>
      <div class="dataset-stat"><strong>{dist.get('legitimate',0):,}</strong><span>legitimate postings</span></div>
    </div>
    <div class="helper" style="margin-top:.65rem;">{metrics.get('exact_duplicate_rows_removed',0):,} exact duplicate combined job texts were removed before splitting to reduce leakage.</div>
  </div>
  <div class="insight-card">
    <h3>Confusion matrix · held-out test</h3>
    <p>{split.get('test_rows','-')} examples were kept untouched during model fitting and threshold selection.</p>
    <div class="matrix">
      <div></div><div class="m-label">Predicted<br>legitimate</div><div class="m-label">Predicted<br>fraud</div>
      <div class="m-label">Actual<br>legitimate</div><div class="cell good"><strong>{tn:,}</strong><span>true negatives</span></div><div class="cell bad"><strong>{fp:,}</strong><span>false positives</span></div>
      <div class="m-label">Actual<br>fraud</div><div class="cell bad"><strong>{fn:,}</strong><span>false negatives</span></div><div class="cell good"><strong>{tp:,}</strong><span>true positives</span></div>
    </div>
  </div>
</div>
""",
            unsafe_allow_html=True,
        )

        st.markdown(
            f"""
<div class="insight-grid">
  <div class="insight-card">
    <h3>Evaluation design</h3>
    <p>Threshold selection is separated from final reporting.</p>
    <div class="dataset-grid">
      <div class="dataset-stat"><strong>{split.get('train_rows','-')}</strong><span>training rows</span></div>
      <div class="dataset-stat"><strong>{split.get('validation_rows','-')}</strong><span>validation rows</span></div>
      <div class="dataset-stat"><strong>{split.get('test_rows','-')}</strong><span>test rows</span></div>
    </div>
    <div class="helper" style="margin-top:.65rem;">Decision threshold: <strong>{metrics.get('selected_threshold',0.5):.2f}</strong> · PR-AUC: <strong>{test.get('pr_auc',0):.4f}</strong> · Accuracy: <strong>{test.get('accuracy',0):.2%}</strong></div>
  </div>
  <div class="insight-card">
    <h3>Model architecture</h3>
    <p>A deliberately interpretable baseline that can expose influential text features.</p>
    <div class="pipeline">
      <span class="pipe-step">Job posting</span><span class="pipe-arrow">→</span>
      <span class="pipe-step">Text preprocessing</span><span class="pipe-arrow">→</span>
      <span class="pipe-step">TF-IDF 1–2 grams</span><span class="pipe-arrow">→</span>
      <span class="pipe-step">Logistic Regression</span><span class="pipe-arrow">→</span>
      <span class="pipe-step">Fraud probability</span><span class="pipe-arrow">→</span>
      <span class="pipe-step">Rule fusion</span>
    </div>
  </div>
</div>
""",
            unsafe_allow_html=True,
        )
        st.caption(metrics.get("warning", "Metrics are dataset-specific and do not guarantee real-world performance."))

with about_tab:
    st.markdown('<div class="eyebrow">Product rationale</div><div class="page-title">Transparent screening, not a black-box verdict</div><div class="page-sub">JobShield AU is an experimental decision-support tool designed to surface suspicious recruitment patterns and explain why they were flagged.</div>', unsafe_allow_html=True)
    st.markdown(
        """
<div class="about-grid">
  <div class="about-card"><h3>What it analyses</h3><p>Job advertisements, recruiter emails, SMS or messaging text, payment requests, communication-channel pressure, sensitive identity requests and optional company-domain mismatches.</p></div>
  <div class="about-card"><h3>Why a hybrid engine?</h3><p>Rules catch explicit high-signal behaviours while the NLP classifier captures broader wording patterns that hand-written rules may miss.</p></div>
  <div class="about-card"><h3>Why explainability matters</h3><p>The interface keeps rule signals, local NLP features and separate ML/rule scores visible so the user can understand the result rather than accept a single unexplained label.</p></div>
  <div class="about-card"><h3>Current limitations</h3><p>The historical dataset may not reflect new scam tactics or Australian-specific wording. JobShield does not yet perform live company-register, URL-reputation or recruiter-identity checks.</p></div>
</div>
<div class="tech-row">
  <span class="tech">Python</span><span class="tech">scikit-learn</span><span class="tech">TF-IDF</span><span class="tech">Logistic Regression</span><span class="tech">Streamlit</span><span class="tech">Pandas</span><span class="tech">Joblib</span>
</div>
<div class="disclaimer"><strong>Important:</strong> JobShield provides decision support only. A risk score does not prove that a recruiter or job advertisement is fraudulent. Always verify the employer and vacancy independently.</div>
""",
        unsafe_allow_html=True,
    )
