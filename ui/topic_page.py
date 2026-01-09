import streamlit as st
from ui.conversations import render_conversations
from ui.repairs import render_repair
from logic.aggregations import compute_severity_stats, infer_conversation_theme

def render_topic_page(turns_df, topics_df, repairs_df, topic_id):
    topic_rows = topics_df[topics_df["topic_id"] == topic_id]
    if topic_rows.empty:
        st.error("Topic not found or no data available for this topic.")
        return

    topic = topic_rows.iloc[0]
    topic_turns = turns_df[turns_df["topic_id"] == topic_id]

    # Custom CSS for styling
    st.markdown("""
    <style>
    /* Page headers */
    .topic-header {
        font-size: 1.8rem;
        font-weight: 900;
        color: #0f172a;
        margin-bottom: 0.5rem;
        letter-spacing: -0.8px;
        border-bottom: 3px solid #3b82f6;
        padding-bottom: 0.5rem;
        display: inline-block;
    }
    .topic-caption {
        color: #64748b;
        font-size: 1.05rem;
        line-height: 1.6;
        margin-bottom: 1.5rem;
    }
    .section-divider {
        margin: 2rem 0;
        border: none;
        border-top: 2px solid #e2e8f0;
    }
    .section-subheader {
        font-size: 1.5rem;
        font-weight: 800;
        color: #1e293b;
        margin: 1.5rem 0 1rem 0;
        letter-spacing: -0.5px;
    }
    .topic-page .stColumns {
        background-color: #f9f9f9 !important;
        padding: 15px !important;
        border-radius: 8px !important;
        margin-bottom: 20px !important;
        border: 1px solid #ddd !important;
    }
    .topic-page .stSubheader:has-text("💬 Sample Conversations") ~ * {
        background-color: #fff3e0 !important;
        padding: 15px !important;
        border-radius: 8px !important;
        margin-bottom: 20px !important;
        border: 1px solid #ff9800 !important;
    }
    .topic-page .stSubheader:has-text("🛠 Repair Package") ~ * {
        background-color: #e8f5e8 !important;
        padding: 15px !important;
        border-radius: 8px !important;
        border: 1px solid #4caf50 !important;
    }
    .topic-info-box {
        background: linear-gradient(135deg, #e3f2fd 0%, #f0f7ff 100%);
        border: 2px solid #2196F3;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1.5rem 0;
        box-shadow: 0 4px 12px rgba(33, 150, 243, 0.15);
    }
    .topic-info-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1.2rem;
    }
    .topic-info-item {
        background: white;
        border-radius: 8px;
        padding: 1rem;
        border: 1.5px solid #bbdefb;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .topic-info-item:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(33, 150, 243, 0.2);
    }
    .topic-info-label {
        font-size: 0.85rem;
        font-weight: 600;
        color: #1565c0;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 0.4rem;
    }
    .topic-info-value {
        font-size: 1.75rem;
        font-weight: 800;
        color: #0d47a1;
        line-height: 1.2;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="topic-page">', unsafe_allow_html=True)
    
    # Use inferred theme label matching diagnostics page
    theme_label = topic["topic_label"]
    if not topic_turns.empty:
        inferred = infer_conversation_theme(topic_turns)
        if inferred:
            theme_label = inferred
    display_label = f"Failure - {theme_label}"
    
    st.markdown(f'<h1 class="topic-header">{display_label}</h1>', unsafe_allow_html=True)
    st.markdown(f'<div class="topic-caption">{topic["example_reason"]}</div>', unsafe_allow_html=True)

    severity = compute_severity_stats(topic_turns)

    # Create informative box with the three key metrics
    st.markdown(
        f"""
        <div class="topic-info-box">
            <div class="topic-info-grid">
                <div class="topic-info-item">
                    <div class="topic-info-label">📊 Examples</div>
                    <div class="topic-info-value">{int(topic['n_examples'])}</div>
                </div>
                <div class="topic-info-item">
                    <div class="topic-info-label">⭐ Avg Satisfaction</div>
                    <div class="topic-info-value">{topic['avg_satisfaction']:.2f}</div>
                </div>
                <div class="topic-info-item">
                    <div class="topic-info-label">🔥 Dominant Severity</div>
                    <div class="topic-info-value">{severity['dominant_severity']}</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    st.markdown('<h2 class="section-subheader">💬 Sample Conversations</h2>', unsafe_allow_html=True)
    st.markdown('<div class="topic-caption">User–Assistant conversations where this failure occurs</div>', unsafe_allow_html=True)
    render_conversations(turns_df, topic_id)

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    st.markdown('<h2 class="section-subheader">🛠 Repair Package</h2>', unsafe_allow_html=True)
    render_repair(repairs_df, topic_id)
    st.markdown('</div>', unsafe_allow_html=True)
