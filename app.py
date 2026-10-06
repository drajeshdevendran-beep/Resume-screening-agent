"""
CogniHire — AI Resume Screening Agent
Main Streamlit Application

A recommendation tool for recruiters — not a hiring decision system.
"""
import os
import json
import base64
from collections import Counter
from html import escape

import streamlit as st

# Local modules
import database
import auth
import parser
import llm_client
import report_generator

# ─── Page Configuration ───────────────────────────────────────────────
st.set_page_config(
    page_title="CogniHire — AI Resume Screening",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Custom CSS ──────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    * { font-family: 'Inter', sans-serif; }

    :root {
        --green-950: #12382f;
        --green-800: #17664f;
        --green-700: #21805f;
        --green-100: #e5f4ec;
        --green-50: #f3faf6;
    }

    .stApp {
        background:
            radial-gradient(ellipse at 5% 0%, rgba(95, 171, 126, 0.13), transparent 35%),
            radial-gradient(ellipse at 95% 100%, rgba(169, 211, 179, 0.22), transparent 36%),
            #f5faf6;
    }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #f0f7f2 0%, #e5f1e9 100%);
        border-right: 1px solid #d5e6da;
        width: 280px !important;
        min-width: 280px !important;
        flex: 0 0 280px !important;
    }

    [data-testid="stSidebar"] .block-container { padding-top: 1.2rem; }
    [data-testid="stSidebar"] button[kind="primary"] {
        background: #17664f;
        border-color: #17664f;
        color: #fff;
    }
    [data-testid="stSidebar"] button[kind="secondary"] {
        color: #254b3d;
        border-color: #d0e1d5;
    }

    @keyframes fade-up {
        from { opacity: 0; transform: translateY(12px); }
        to { opacity: 1; transform: translateY(0); }
    }

    @keyframes soft-glow {
        0%, 100% { box-shadow: 0 12px 32px rgba(24, 91, 65, 0.07); }
        50% { box-shadow: 0 16px 38px rgba(24, 91, 65, 0.13); }
    }

    .brand-row {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 0.55rem;
        margin: 0.4rem 0 0.15rem;
        animation: fade-up 0.55s ease both;
    }

    .brand-row h1, .brand-row h2 {
        color: var(--green-950);
        margin: 0;
        font-weight: 750;
        letter-spacing: -0.04em;
    }

    .brand-row h1 { font-size: 1.8rem; }
    .brand-row h2 { font-size: 1.15rem; }
    .brand-row img { width: 38px; height: 38px; object-fit: contain; }

    .brand-caption {
        color: #557467;
        text-align: center;
        font-size: 0.9rem;
        margin: 0.1rem 0 1.5rem;
    }

    .sidebar-brand-nav {
        display: flex;
        align-items: center;
        gap: 0.6rem;
        padding: 0.65rem;
        margin: 0.2rem 0 0.9rem;
        border: 1px solid #d5e6da;
        border-radius: 14px;
        background: rgba(255,255,255,0.7);
    }
    .sidebar-brand-nav img { width: 36px; height: 36px; object-fit: contain; }
    .sidebar-brand-name { color: var(--green-950); line-height: 1.15; }
    .sidebar-brand-name strong { display: block; font-size: 0.98rem; }
    .sidebar-brand-name span { color: #557467; font-size: 0.68rem; }

    .login-card {
        background: rgba(255,255,255,0.86);
        border: 1px solid #deebe1;
        border-radius: 22px;
        padding: 1.5rem 1.7rem;
        box-shadow: 0 18px 50px rgba(24, 91, 65, 0.10);
        animation: fade-up 0.65s ease both, soft-glow 5s ease-in-out 0.7s infinite;
    }

    [data-testid="stForm"] {
        background: rgba(255,255,255,0.9);
        border: 1px solid #deebe1;
        border-radius: 18px;
        padding: 1.25rem;
        box-shadow: 0 14px 40px rgba(24,91,65,0.08);
        animation: fade-up 0.65s ease both;
    }

    .main-header {
        background: linear-gradient(135deg, #17664f 0%, #39926c 100%);
        padding: 2rem;
        border-radius: 16px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .main-header h1 { margin: 0; font-size: 2.2rem; font-weight: 700; }
    .main-header p { margin: 0.5rem 0 0 0; opacity: 0.9; font-size: 1rem; }

    .metric-card {
        background: rgba(255,255,255,0.9);
        border: 1px solid #dce9df;
        border-radius: 16px;
        padding: 1.5rem;
        text-align: center;
        box-shadow: 0 8px 24px rgba(24, 91, 65, 0.06);
        animation: fade-up 0.5s ease both;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        min-width: 0;
    }
    .metric-card:hover { transform: translateY(-4px); box-shadow: 0 14px 30px rgba(24,91,65,0.12); }
    .metric-card h3 { margin: 0; font-size: 2rem; color: var(--green-800); }
    .metric-card p { margin: 0.25rem 0 0 0; color: #6B7280; font-size: 0.85rem; }
    .analytics-metrics {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
        gap: 0.9rem;
        margin-bottom: 1.2rem;
    }
    .analytics-metrics .metric-card { text-align: left; padding: 1.15rem; }
    .analytics-metrics .metric-card h3 { white-space: nowrap; }
    .analytics-label { color: #294b3d !important; font-size: 0.82rem !important; font-weight: 700; }
    .analytics-caption { color: #70877b !important; font-size: 0.75rem !important; }

    .candidate-card {
        background: rgba(255,255,255,0.9);
        border: 1px solid #dce9df;
        border-radius: 12px;
        padding: 1.25rem;
        margin-bottom: 1rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06);
        animation: fade-up 0.45s ease both;
    }
    .score-badge {
        display: inline-block;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .score-high { background: #D1FAE5; color: #17664f; }
    .score-medium { background: #FEF3C7; color: #92400E; }
    .score-low { background: #FEE2E2; color: #991B1B; }

    .disclaimer {
        background: #F3F4F6;
        border-left: 4px solid #9CA3AF;
        padding: 1rem;
        border-radius: 8px;
        font-size: 0.85rem;
        color: #6B7280;
        margin: 1rem 0;
    }

    .stButton>button {
        border-radius: 10px;
        font-weight: 600;
        transition: transform 0.18s ease, box-shadow 0.18s ease;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 7px 18px rgba(24,91,65,0.14);
    }

    .analytics-panel {
        background: rgba(255,255,255,0.9);
        border: 1px solid #dce9df;
        border-radius: 16px;
        padding: 1.3rem 1.4rem;
        min-height: 300px;
        box-shadow: 0 8px 24px rgba(24,91,65,0.05);
        animation: fade-up 0.55s ease both;
    }
    .analytics-panel h4 { color: var(--green-950); margin: 0 0 1rem; }
    .donut-wrap { display: flex; align-items: center; justify-content: center; gap: 1.7rem; }
    .donut-chart {
        width: 190px; height: 190px; border-radius: 50%; position: relative;
        display: grid; place-items: center; flex: 0 0 auto;
        animation: fade-up 0.8s ease both;
    }
    .donut-hole {
        width: 112px; height: 112px; border-radius: 50%; background: #fff;
        display: flex; flex-direction: column; align-items: center; justify-content: center;
    }
    .donut-hole strong { color: var(--green-950); font-size: 1.65rem; }
    .donut-hole span { color: #70877b; font-size: 0.72rem; }
    .chart-legend { display: flex; flex-direction: column; gap: 0.65rem; }
    .legend-item { display: flex; align-items: center; gap: 0.5rem; color: #456356; font-size: 0.85rem; }
    .legend-dot { width: 10px; height: 10px; border-radius: 50%; display: inline-block; }
    .skill-row { display: flex; align-items: center; gap: 0.8rem; margin: 1rem 0; }
    .skill-name { width: 82px; flex: 0 0 82px; color: #294b3d; font-size: 0.78rem; font-weight: 600; }
    .skill-track { flex: 1; min-width: 42px; height: 10px; background: #e7efe9; border-radius: 99px; overflow: hidden; }
    .skill-fill { height: 100%; border-radius: 99px; background: linear-gradient(90deg,#27805e,#78bf8a); }
    .skill-count { min-width: 28px; text-align: right; color: #557467; font-size: 0.8rem; }

    @media (max-width: 1100px) {
        .donut-wrap { flex-direction: column; }
        .donut-chart { width: 150px; height: 150px; }
        .donut-hole { width: 90px; height: 90px; }
        .analytics-panel { min-height: auto; }
    }
</style>
""", unsafe_allow_html=True)


# ─── Initialize ──────────────────────────────────────────────────────
database.init_db()
auth.init_session()


# ─── Login Page ──────────────────────────────────────────────────────
def render_login():
    """Render the login page."""
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        logo_path = os.path.join(os.path.dirname(__file__), "assets", "logo.svg")
        if os.path.exists(logo_path):
            with open(logo_path, "rb") as logo_file:
                logo_src = base64.b64encode(logo_file.read()).decode("ascii")
            st.markdown(
                f'<div class="brand-row"><img src="data:image/svg+xml;base64,{logo_src}" alt="">'
                '<h1>CogniHire</h1></div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<div class="brand-row"><h1>CogniHire</h1></div>',
                unsafe_allow_html=True,
            )
        st.markdown('<p class="brand-caption">AI Resume Screening Agent</p>', unsafe_allow_html=True)
        with st.form("login_form"):
            username = st.text_input("Username", placeholder="Enter username")
            password = st.text_input("Password", type="password", placeholder="Enter password")
            submitted = st.form_submit_button("Sign In", use_container_width=True)

            if submitted:
                if auth.login(username, password):
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error("Invalid username or password.")


# ─── Change Password Page ────────────────────────────────────────────
def render_change_password():
    """Render the change password page."""
    st.markdown("### 🔑 Change Password")

    with st.form("change_pwd_form"):
        current_pwd = st.text_input("Current Password", type="password")
        new_pwd = st.text_input("New Password", type="password")
        confirm_pwd = st.text_input("Confirm New Password", type="password")
        submitted = st.form_submit_button("Update Password", use_container_width=True)

        if submitted:
            if new_pwd != confirm_pwd:
                st.error("New passwords do not match.")
            else:
                success, message = auth.change_password(current_pwd, new_pwd)
                if success:
                    st.success(message)
                else:
                    st.error(message)


# ─── Dashboard Home ──────────────────────────────────────────────────
def render_home():
    """Render the dashboard home page."""
    st.markdown("### 📊 Dashboard Overview")

    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""<div class="metric-card">
            <h3>{database.get_task_count()}</h3>
            <p>Active Tasks</p>
        </div>""", unsafe_allow_html=True)
    with col2:
        st.markdown(f"""<div class="metric-card">
            <h3>{database.get_candidate_count()}</h3>
            <p>Candidates Screened</p>
        </div>""", unsafe_allow_html=True)
    with col3:
        st.markdown(f"""<div class="metric-card">
            <h3>{database.get_avg_score()}</h3>
            <p>Avg Score</p>
        </div>""", unsafe_allow_html=True)
    with col4:
        tasks = database.get_all_tasks()
        strong_hire = 0
        for task in tasks:
            cands = database.get_candidates_by_task(task["id"])
            strong_hire += sum(1 for c in cands if c.get("recommendation") == "Strong Hire")
        st.markdown(f"""<div class="metric-card">
            <h3>{strong_hire}</h3>
            <p>Strong Hires</p>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Recent tasks
    st.markdown("#### Recent Screening Tasks")
    tasks = database.get_all_tasks()
    if tasks:
        for task in tasks[:5]:
            cands = database.get_candidates_by_task(task["id"])
            with st.expander(f"📋 {task['job_title']} — {len(cands)} candidates"):
                st.write(f"**Created:** {task['created_at'][:10]}")
                st.write(f"**By:** {task['created_by']}")
                if cands:
                    st.write("**Top Candidates:**")
                    for c in cands[:3]:
                        st.write(f"- {c['name']} — Score: {c['score']} ({c['recommendation']})")
    else:
        st.info("No screening tasks yet. Create one from the sidebar!")

    # Disclaimer
    st.markdown("""<div class="disclaimer">
        ⚠️ <strong>Disclaimer:</strong> CogniHire provides AI-generated recommendations
        to assist recruiters. These are not hiring decisions. All final decisions
        should involve human judgment and comply with employment laws.
    </div>""", unsafe_allow_html=True)


def render_analytics():
    """Show metrics and charts derived from screened candidate records."""
    candidates = database.get_all_candidates()
    total = len(candidates)
    average = (
        round(sum(float(candidate.get("score") or 0) for candidate in candidates) / total, 1)
        if total else 0
    )
    recommended = sum(
        candidate.get("recommendation") in {"Strong Hire", "Hire"}
        for candidate in candidates
    )
    st.markdown("### 📈 Analytics")
    metrics = [
        ("Average Match Score", f"{average}%", "Across screened resumes"),
        ("Total Resumes", total, "Screened to date"),
        ("Recommended to Hire", recommended, "AI recommendation: Hire"),
    ]
    metric_cards = "".join(
        f"""<div class="metric-card">
            <h3>{value}</h3>
            <p class="analytics-label">{escape(label)}</p>
            <p class="analytics-caption">{escape(caption)}</p>
        </div>"""
        for label, value, caption in metrics
    )
    st.markdown(
        f'<div class="analytics-metrics">{metric_cards}</div>',
        unsafe_allow_html=True,
    )

    score_bands = [
        ("Strong match", sum(float(c.get("score") or 0) >= 80 for c in candidates), "#21805f"),
        ("Good match", sum(65 <= float(c.get("score") or 0) < 80 for c in candidates), "#79ad65"),
        ("Needs review", sum(50 <= float(c.get("score") or 0) < 65 for c in candidates), "#e2ad53"),
        ("Low match", sum(float(c.get("score") or 0) < 50 for c in candidates), "#c97569"),
    ]
    score_total = sum(count for _, count, _ in score_bands)
    chart_parts = []
    legend_items = []
    accumulated = 0.0
    for label, count, color in score_bands:
        portion = (count / score_total * 100) if score_total else 0
        end = accumulated + portion
        chart_parts.append(f"{color} {accumulated:.2f}% {end:.2f}%")
        accumulated = end
        legend_items.append(
            f'<div class="legend-item"><span class="legend-dot" style="background:{color}"></span>'
            f'{escape(label)} <strong>{count}</strong></div>'
        )
    donut_background = (
        f"conic-gradient({', '.join(chart_parts)})"
        if score_total else "conic-gradient(#dce9df 0 100%)"
    )

    skill_counts = Counter()
    skill_labels = {}
    for candidate in candidates:
        raw_skills = str(candidate.get("skills") or "")
        normalized_skills = {
            skill.strip().strip("[]'\"")
            for skill in raw_skills.replace(";", ",").replace("\n", ",").split(",")
            if skill.strip().strip("[]'\"")
        }
        for skill in normalized_skills:
            key = skill.casefold()
            skill_counts[key] += 1
            skill_labels.setdefault(key, skill)
    top_skills = skill_counts.most_common(6)
    max_skill_count = max((count for _, count in top_skills), default=1)

    chart_column, skills_column = st.columns(2)
    with chart_column:
        st.markdown(
            f"""<div class="analytics-panel">
                <h4>Match Score Distribution</h4>
                <div class="donut-wrap">
                    <div class="donut-chart" style="background:{donut_background}">
                        <div class="donut-hole"><strong>{total}</strong><span>resumes</span></div>
                    </div>
                    <div class="chart-legend">{''.join(legend_items)}</div>
                </div>
            </div>""",
            unsafe_allow_html=True,
        )
    with skills_column:
        skill_rows = "".join(
            f"""<div class="skill-row">
                <span class="skill-name">{escape(skill_labels[key])}</span>
                <div class="skill-track"><div class="skill-fill" style="width:{count / max_skill_count * 100:.1f}%"></div></div>
                <span class="skill-count">{count}</span>
            </div>"""
            for key, count in top_skills
        )
        if not skill_rows:
            skill_rows = '<p style="color:#70877b">Skills will appear after resumes are screened.</p>'
        st.markdown(
            f'<div class="analytics-panel"><h4>Top Skills</h4>{skill_rows}</div>',
            unsafe_allow_html=True,
        )
    if not candidates:
        st.info("Analytics will populate after the first resumes have been screened.")


# ─── New Screening Task ──────────────────────────────────────────────
def render_new_task():
    """Render the new screening task page."""
    st.markdown("### 🧪 New Screening Task")

    with st.form("new_task_form"):
        job_title = st.text_input("Job Title", placeholder="e.g. Senior Python Developer")
        job_description = st.text_area(
            "Job Description",
            height=200,
            placeholder="Paste the full job description here..."
        )
        submitted = st.form_submit_button("Create Task", use_container_width=True)

        if submitted:
            if not job_title or not job_description:
                st.error("Please fill in both job title and description.")
            else:
                task_id = database.create_task(
                    job_title, job_description, st.session_state.username
                )
                st.success(f"Task created successfully! Task ID: {task_id}")
                st.session_state["current_task_id"] = task_id
                st.rerun()

    # If we have a current task, show the upload section
    task_id = st.session_state.get("current_task_id")
    if task_id:
        task = database.get_task(task_id)
        if task:
            st.markdown("---")
            st.markdown(f"#### 📤 Upload Resumes for: {task['job_title']}")

            uploaded_files = st.file_uploader(
                "Upload resume files (PDF or DOCX)",
                type=["pdf", "docx", "doc"],
                accept_multiple_files=True
            )

            if uploaded_files:
                if st.button("🔍 Screen Candidates", use_container_width=True):
                    process_resumes(uploaded_files, task_id, task["job_description"])


def process_resumes(uploaded_files, task_id, job_description):
    """Process uploaded resumes through the screening pipeline."""
    progress_bar = st.progress(0)
    status_text = st.empty()

    total = len(uploaded_files)
    for i, uploaded_file in enumerate(uploaded_files):
        status_text.text(f"Processing {uploaded_file.name}... ({i+1}/{total})")
        progress_bar.progress((i + 1) / total)

        # Parse resume
        file_bytes = uploaded_file.read()
        raw_text = parser.parse_resume(file_bytes, uploaded_file.name)

        if not raw_text:
            st.warning(f"Could not extract text from {uploaded_file.name}")
            continue

        raw_text = parser.clean_text(raw_text)

        # Extract candidate details
        candidate = llm_client.extract_candidate_details(raw_text)

        # Score candidate
        score_result = llm_client.score_candidate(candidate, job_description)

        # Save to database
        candidate_data = {
            **candidate,
            "raw_text": raw_text[:2000],  # Store truncated
            "structured_json": json.dumps(candidate),
            "score": score_result["score"],
            "score_breakdown": json.dumps(score_result["breakdown"]),
            "justification": score_result["justification"],
            "recommendation": score_result["recommendation"],
        }
        database.save_candidate(task_id, candidate_data)

    progress_bar.empty()
    status_text.empty()
    st.success(f"Successfully processed {total} resume(s)!")
    st.rerun()


# ─── Candidate Summary ───────────────────────────────────────────────
def render_summary():
    """Render the candidate summary page."""
    st.markdown("### 📋 Candidate Summary")

    # Task selector
    tasks = database.get_all_tasks()
    if not tasks:
        st.info("No screening tasks available. Create one first!")
        return

    task_options = {f"{t['job_title']} (ID: {t['id']})": t["id"] for t in tasks}
    selected_task = st.selectbox("Select a task to view candidates", list(task_options.keys()))
    task_id = task_options[selected_task]

    candidates = database.get_candidates_by_task(task_id)

    if not candidates:
        st.info("No candidates screened for this task yet.")
        return

    # Download reports
    st.markdown("#### 📥 Download Reports")
    col1, col2 = st.columns(2)
    with col1:
        excel_data = report_generator.generate_excel_report(candidates, selected_task)
        st.download_button(
            label="📊 Download Excel Report",
            data=excel_data,
            file_name=f"cognihire_report_{task_id}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
    with col2:
        pdf_data = report_generator.generate_pdf_report(candidates, selected_task)
        st.download_button(
            label="📄 Download PDF Report",
            data=pdf_data,
            file_name=f"cognihire_report_{task_id}.pdf",
            mime="application/pdf",
            use_container_width=True,
        )

    st.markdown("---")
    st.markdown(f"#### 🏆 Ranked Candidates ({len(candidates)} total)")

    for i, c in enumerate(candidates, 1):
        score = c.get("score", 0)
        if score >= 65:
            score_class = "score-high"
        elif score >= 45:
            score_class = "score-medium"
        else:
            score_class = "score-low"

        with st.container():
            st.markdown(f"""<div class="candidate-card">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <div>
                        <strong>#{i} — {c['name']}</strong>
                        <br><small style="color:#6B7280;">{c.get('email', '')} · {c.get('phone', '')}</small>
                    </div>
                    <span class="score-badge {score_class}">{score}/100 — {c['recommendation']}</span>
                </div>
                <p style="margin:0.5rem 0;"><strong>Skills:</strong> {c.get('skills', 'N/A')[:150]}</p>
                <p style="margin:0.25rem 0;"><strong>Experience:</strong> {c.get('experience_years', 0)} years</p>
                <p style="margin:0.25rem 0;"><strong>Education:</strong> {c.get('education', 'N/A')}</p>
                <p style="margin:0.5rem 0; font-size:0.9rem; color:#374151;">
                    <strong>Justification:</strong> {c.get('justification', '')}
                </p>
            </div>""", unsafe_allow_html=True)


# ─── Main App ────────────────────────────────────────────────────────
def select_page(page: str):
    """Store the selected sidebar destination before Streamlit reruns."""
    st.session_state.current_page = page


def main():
    """Main application entry point."""

    if not auth.is_authenticated():
        render_login()
        return

    if "current_page" not in st.session_state:
        st.session_state.current_page = "Dashboard"

    # Sidebar navigation
    with st.sidebar:
        logo_path = os.path.join(os.path.dirname(__file__), "assets", "logo.svg")
        if os.path.exists(logo_path):
            with open(logo_path, "rb") as logo_file:
                sidebar_logo_src = base64.b64encode(logo_file.read()).decode("ascii")
            sidebar_logo = (
                f'<img src="data:image/svg+xml;base64,{sidebar_logo_src}" alt="">'
            )
        else:
            sidebar_logo = ""
        st.markdown(
            '<div class="sidebar-brand-nav">'
            f'{sidebar_logo}<div class="sidebar-brand-name"><strong>CogniHire</strong>'
            '<span>AI Resume Screening</span></div></div>',
            unsafe_allow_html=True,
        )

        navigation = [
            ("Dashboard", "📊"),
            ("New Task", "🧪"),
            ("Candidates", "👥"),
            ("Analytics", "📈"),
            ("Change Password", "🔑"),
        ]
        for label, icon in navigation:
            st.button(
                f"{icon}  {label}",
                key=f"nav_{label.lower().replace(' ', '_')}",
                use_container_width=True,
                type="primary" if st.session_state.current_page == label else "secondary",
                on_click=select_page,
                args=(label,),
            )

        st.markdown("---")
        st.markdown(f"👤 **{st.session_state.username}**")
        if st.button("🚪 Logout", use_container_width=True):
            auth.logout()
            st.rerun()

    page = st.session_state.current_page

    # Render selected page
    if page == "Dashboard":
        render_home()
    elif page == "New Task":
        render_new_task()
    elif page == "Candidates":
        render_summary()
    elif page == "Analytics":
        render_analytics()
    elif page == "Change Password":
        render_change_password()


if __name__ == "__main__":
    main()
