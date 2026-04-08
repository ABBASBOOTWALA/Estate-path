"""
EstatePath — Estate & End-of-Life Planning Orchestrator
Entry point: streamlit run app.py
"""
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="EstatePath",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Global CSS ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* ── Base app background & text ── */
    .stApp {
        background-color: #0f1923;
        color: #e8edf2;
    }

    /* ── Main content area ── */
    .main .block-container {
        background-color: #0f1923;
        padding-top: 2rem;
    }

    /* ── Headings ── */
    h1, h2, h3, h4 {
        color: #7ec8e3 !important;
        font-weight: 600;
    }

    /* ── Paragraphs, labels, captions ── */
    p, span, label, .stCaption, .stText {
        color: #c9d6df !important;
    }

    /* ── Sidebar ── */
    [data-testid="stSidebar"] {
        background-color: #131f2e !important;
        border-right: 1px solid #1e3048;
    }
    [data-testid="stSidebar"] * {
        color: #c9d6df !important;
    }

    /* ── Primary buttons ── */
    .stButton > button[kind="primary"] {
        background-color: #1a6b8a !important;
        border-color: #1a6b8a !important;
        color: #ffffff !important;
        border-radius: 6px;
    }
    .stButton > button[kind="primary"]:hover {
        background-color: #1e85a8 !important;
        border-color: #1e85a8 !important;
    }

    /* ── Secondary buttons ── */
    .stButton > button[kind="secondary"] {
        background-color: #1e3048 !important;
        border-color: #2c4a6e !important;
        color: #c9d6df !important;
        border-radius: 6px;
    }
    .stButton > button[kind="secondary"]:hover {
        background-color: #264060 !important;
    }

    /* ── Input fields ── */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div > div,
    .stNumberInput > div > div > input {
        background-color: #1a2d40 !important;
        color: #e8edf2 !important;
        border-color: #2c4a6e !important;
        border-radius: 6px;
    }

    /* ── Multiselect ── */
    .stMultiSelect > div > div {
        background-color: #1a2d40 !important;
        border-color: #2c4a6e !important;
        color: #e8edf2 !important;
    }

    /* ── Expander ── */
    [data-testid="stExpander"] {
        background-color: #131f2e !important;
        border: 1px solid #1e3048 !important;
        border-radius: 8px;
    }
    [data-testid="stExpander"] summary {
        color: #7ec8e3 !important;
    }

    /* ── Metric cards ── */
    [data-testid="stMetric"] {
        background-color: #131f2e !important;
        border: 1px solid #1e3048 !important;
        border-radius: 8px;
        padding: 12px;
    }
    [data-testid="stMetricValue"] {
        color: #7ec8e3 !important;
    }
    [data-testid="stMetricLabel"] {
        color: #8fa3b3 !important;
    }

    /* ── Info / warning / success / error boxes ── */
    [data-testid="stAlert"] {
        border-radius: 8px;
    }

    /* ── Progress bar ── */
    [data-testid="stProgress"] > div > div {
        background-color: #1a6b8a !important;
    }

    /* ── Chat messages ── */
    [data-testid="stChatMessage"] {
        background-color: #131f2e !important;
        border: 1px solid #1e3048;
        border-radius: 8px;
        margin-bottom: 8px;
    }

    /* ── Chat input ── */
    [data-testid="stChatInput"] > div {
        background-color: #1a2d40 !important;
        border-color: #2c4a6e !important;
    }
    [data-testid="stChatInput"] textarea {
        color: #e8edf2 !important;
    }

    /* ── Divider ── */
    hr { border-color: #1e3048; }

    /* ── Dataframe / table ── */
    [data-testid="stDataFrame"] {
        background-color: #131f2e !important;
    }

    /* ── Containers with border ── */
    [data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #131f2e !important;
        border-color: #1e3048 !important;
        border-radius: 8px;
    }

    /* ── Radio buttons ── */
    .stRadio > div {
        color: #c9d6df !important;
    }

    /* ── Checkboxes ── */
    .stCheckbox > label {
        color: #c9d6df !important;
    }

    /* Hide default Streamlit elements */
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ── Navigation ─────────────────────────────────────────────────────────────
from core.storage import profile_exists

with st.sidebar:
    st.markdown("## 🌿 EstatePath")
    st.caption("Estate Settlement Guide")
    st.divider()

    pages = {
        "🏠 Home": "home",
        "📋 Intake": "intake",
        "✅ Checklist": "checklist",
        "📄 Documents": "documents",
        "📅 Timeline": "timeline",
        "🏛️ Institutions": "institutions",
        "💬 Ask EstatePath": "chat",
    }

    if "current_page" not in st.session_state:
        st.session_state.current_page = "intake" if not profile_exists() else "home"

    for label, page_key in pages.items():
        is_active = st.session_state.current_page == page_key
        if st.button(label, key=f"nav_{page_key}", use_container_width=True,
                     type="primary" if is_active else "secondary"):
            st.session_state.current_page = page_key
            st.rerun()

    st.divider()

    # Profile status
    if profile_exists():
        from core.storage import load_profile
        from agents.checklist_agent import get_progress_summary
        p = load_profile()
        if p:
            st.caption(f"**Estate of:** {p.full_name}")
            st.caption(f"**State:** {p.state_of_residence}")
            try:
                s = get_progress_summary()
                st.caption(f"**Progress:** {s['completed']}/{s['total']} tasks ({s['pct_complete']}%)")
                st.progress(s["pct_complete"] / 100)
            except Exception:
                pass
    else:
        st.caption("No estate profile yet. Start with **Intake**.")

    st.divider()
    st.caption("EstatePath provides general guidance only, not legal advice. Consult a probate attorney for legal questions.")

# ── Page Routing ───────────────────────────────────────────────────────────
page = st.session_state.current_page

if page == "home":
    from pages.home import show
    show()
elif page == "intake":
    from pages.intake import show
    show()
elif page == "checklist":
    from pages.checklist import show
    show()
elif page == "documents":
    from pages.documents import show
    show()
elif page == "timeline":
    from pages.timeline import show
    show()
elif page == "institutions":
    from pages.institutions import show
    show()
elif page == "chat":
    from pages.chat import show
    show()
