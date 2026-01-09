import streamlit as st
from logic.data_loader import load_turns, load_topics, load_repairs
from ui.overview import render_overview
from ui.diagnostics import render_diagnostics
from ui.insights import render_positive_insights
from ui.upload_lab_fixed import render_upload_lab

st.set_page_config(
    page_title="RetailMind",
    layout="wide"
)

# ---- Load data once ----
if "turns_df" not in st.session_state:
    st.session_state.turns_df = load_turns()

if "topics_df" not in st.session_state:
    st.session_state.topics_df = load_topics()

if "repairs_df" not in st.session_state:
    st.session_state.repairs_df = load_repairs()

turns_df = st.session_state.turns_df
topics_df = st.session_state.topics_df
repairs_df = st.session_state.repairs_df

# ---- App state routing ----
if "page" not in st.session_state:
    st.session_state.page = "Overview"

# ---- Custom CSS for navbar ----
st.markdown(
    """
    <style>
    /* Light page background to keep text readable */
    html, body, [data-testid="stAppViewContainer"], [data-testid="stAppViewContainer"] > div {
        background: #f4f6fb !important;
    }

    /* Compact divider lines */
    hr {
        margin: 0.35rem 0 0.65rem;
        border: none;
        border-top: 1px solid #e2e8f0;
    }

    /* Main content wrapper (big box) */
    [data-testid="stAppViewContainer"] .main .block-container {
        background: #ffffff !important;
        border-radius: 18px;
        padding: 1rem 1.5rem 1rem !important;
        box-shadow: 0 12px 30px rgba(15, 23, 42, 0.10);
        border: 1px solid #e2e8f0;
    }

    /* Navbar wrapper identified via the marker element */
    div[data-testid="stVerticalBlock"]:has(.navbar-flag) {
        background: linear-gradient(135deg, #f8fafc 0%, #ffffff 100%);
        border-radius: 16px;
        padding: 0.8rem 1.5rem;
        margin-bottom: 0.8rem;
        border: 2px solid #e2e8f0;
        box-shadow: 0 8px 24px rgba(15, 23, 42, 0.08);
        position: relative;
    }

    .navbar-title {
        color: #0f172a;
        font-size: 2rem;
        font-weight: 900;
        margin: 0;
        line-height: 1;
        letter-spacing: -0.8px;
        display: flex;
        align-items: center;
        gap: 0.6rem;
        background: linear-gradient(135deg, #0f172a 0%, #334155 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    .navbar-subtitle {
        color: #64748b;
        font-size: 0.95rem;
        margin-top: 0.2rem;
        font-weight: 500;
    }

    /* Button styling */
    div[data-testid="stVerticalBlock"]:has(.navbar-flag) [data-testid="stButton"] button {
        border: 2px solid #e2e8f0 !important;
        background: #ffffff !important;
        color: #475569 !important;
        font-weight: 700 !important;
        font-size: 0.98rem !important;
        border-radius: 12px !important;
        padding: 0.6rem 1rem !important;
        transition: all 0.2s ease !important;
        box-shadow: 0 2px 8px rgba(15, 23, 42, 0.06) !important;
    }
    div[data-testid="stVerticalBlock"]:has(.navbar-flag) [data-testid="stButton"] button:hover {
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%) !important;
        color: #ffffff !important;
        border-color: #3b82f6 !important;
        box-shadow: 0 6px 16px rgba(59, 130, 246, 0.3) !important;
        transform: translateY(-2px) !important;
    }
    div[data-testid="stVerticalBlock"]:has(.navbar-flag) [data-testid="stButton"] button:active {
        transform: translateY(0) scale(0.98) !important;
        box-shadow: 0 2px 8px rgba(59, 130, 246, 0.2) !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---- Global font sizing for consistency across pages ----
st.markdown(
    """
    <style>
    /* Unified Page Headers - Applied Globally */
    .page-header {
        font-size: 2rem !important;
        font-weight: 800 !important;
        color: #0f172a !important;
        margin-bottom: 0.5rem !important;
        margin-top: 0 !important;
        letter-spacing: -0.02em !important;
        padding-bottom: 0.3rem !important;
        display: inline-block !important;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
    }
    
    .page-subheader {
        font-size: 1.5rem !important;
        font-weight: 700 !important;
        color: #1e293b !important;
        margin: 1rem 0 0.7rem 0 !important;
        letter-spacing: -0.01em !important;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
    }
    
    /* Section dividers */
    .section-divider {
        margin: 1.2rem 0 !important;
    }
    
    /* Base text */
    .stMarkdown p { font-size: 1.02rem !important; }
    .stCaption { font-size: 1.04rem !important; }

    /* Metrics */
    div[data-testid="stMetricLabel"] { font-size: 1.06rem !important; }
    div[data-testid="stMetricValue"] { font-size: 1.8rem !important; font-weight: 800 !important; }

    /* Buttons */
    [data-testid="stButton"] button { font-size: 0.96rem !important; }

    /* Card text helpers used across pages */
    .topic-title { font-size: 1rem !important; }
    .topic-sub, .diag-detail { font-size: 1.02rem !important; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---- Top navigation (self-contained, only navbar) ----
with st.container():
    st.markdown('<div class="navbar-flag"></div>', unsafe_allow_html=True)
    col_title, col_nav = st.columns([1.8, 4.2], gap="large")

    with col_title:
        st.markdown(
            """
            <div class="navbar-title">RetailMind Dashboard</div>
            """,
            unsafe_allow_html=True,
        )

    with col_nav:
        nav_col1, nav_col2, nav_col3, nav_col4 = st.columns(4, gap="medium")
        
        with nav_col1:
            if st.button("📊 Overview", use_container_width=True, key="btn_overview"):
                st.session_state.page = "Overview"
        
        with nav_col2:
            if st.button("🔍 Diagnostics", use_container_width=True, key="btn_diagnostics"):
                st.session_state.page = "Diagnostics"
                # Reset selected topic to avoid stale/invalid state when switching pages
                st.session_state.selected_topic = None
        
        with nav_col3:
            if st.button("✅ What Works Well", use_container_width=True, key="btn_insights"):
                st.session_state.page = "What Works Well"

        with nav_col4:
            if st.button("🚀 Upload Lab", use_container_width=True, key="btn_upload_lab"):
                st.session_state.page = "Upload Lab"

# ---- Pages ----
if st.session_state.page == "Overview":
    render_overview(turns_df, topics_df)

elif st.session_state.page == "Diagnostics":
    render_diagnostics(turns_df, topics_df, repairs_df)

elif st.session_state.page == "What Works Well":
    render_positive_insights(turns_df, topics_df)

elif st.session_state.page == "Upload Lab":
    render_upload_lab()
