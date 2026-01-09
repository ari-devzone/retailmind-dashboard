import streamlit as st
import pandas as pd
from logic.aggregations import (
    get_top_success_topics_detailed,
    get_successful_conversations,
    get_success_insights_for_topic,
    get_top_conversations,
    get_top_performing_topics_from_conversations,
    get_why_it_works_patterns
)


def render_positive_insights(turns_df, topics_df):
    """
    Render the "What Works Well" page with:
    1. Top 50 conversations ranked by satisfaction
    2. Top Performing Topics extracted from top conversations
    3. "Why it works" patterns from existing signals
    4. Concrete success examples with explanations
    """
    
    # Page header styling
    st.markdown(
        """
        <style>
        /* Unified Page Headers */
        .page-header {
            font-size: 2rem;
            font-weight: 800;
            color: #0f172a;
            margin-bottom: 0.5rem;
            letter-spacing: -0.02em;
            border-bottom: 3px solid #22c55e;
            padding-bottom: 0.5rem;
            display: inline-block;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        }
        .page-subheader {
            font-size: 1.5rem;
            font-weight: 700;
            color: #1e293b;
            margin: 1.5rem 0 1rem 0;
            letter-spacing: -0.01em;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        }
        .section-divider {
            margin: 2rem 0;
            border: none;
            border-top: 2px solid #e2e8f0;
        }
        .pattern-card {
            background: linear-gradient(135deg, #f0fdf4 0%, #ffffff 100%);
            border: 1.5px solid #cde9d6;
            border-radius: 12px;
            padding: 14px 16px;
            margin-bottom: 0.8rem;
            box-shadow: 0 4px 12px rgba(34, 197, 94, 0.08);
        }
        .pattern-title {
            font-weight: 700;
            color: #166534;
            font-size: 1.05rem;
            margin-bottom: 0.3rem;
        }
        .pattern-desc {
            color: #0f172a;
            font-size: 0.98rem;
            line-height: 1.5;
            margin-bottom: 0.4rem;
        }
        .pattern-metric {
            color: #16a34a;
            font-weight: 700;
            font-size: 0.95rem;
        }
        .example-card {
            background: linear-gradient(135deg, #ecfdf3 0%, #ffffff 100%);
            border: 1.5px solid #cde9d6;
            border-radius: 10px;
            padding: 12px 14px;
            margin-bottom: 0.7rem;
            font-size: 0.98rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Page header
    st.markdown('<h1 class="page-header">✅ What Works Well</h1>', unsafe_allow_html=True)
    
    # Step 1: Get top 50 conversations
    top_conversations = get_top_conversations(turns_df, limit=50)
    
    if not top_conversations:
        st.info("📊 No successful conversations found. Add more data to see patterns.")
        return
    
    st.markdown("### 📊 Top Performing Topics")
    
    # Step 2: Build top performing topics table
    top_topics = get_top_performing_topics_from_conversations(top_conversations, limit=5)

    # Build a curated set of positive labels so "What Works Well" does not repeat failure topic names
    failure_labels = set(topics_df["topic_label"].tolist()) if not topics_df.empty else set()
    curated_positive_labels = {
        "Movie Recommendations & Reviews": "Personalized Streaming Wins",
        "Event & Ticket Booking": "Seamless Ticketing Journey",
        "Account & Profile": "Effortless Account Support",
        "Orders & Payments": "Checkout Success Stories",
        "Product Discovery": "Guided Discovery Delight",
    }
    used_positive_labels = set()

    def make_positive_label(original_label, idx):
        base = curated_positive_labels.get(original_label, f"{original_label} Excellence")
        # Ensure the displayed label differs from the raw conversation label and avoids failure titles
        if base == original_label:
            base = f"{original_label} Excellence"
        candidate = base
        suffix = 1
        while candidate in used_positive_labels or candidate in failure_labels:
            suffix += 1
            candidate = f"{base} #{suffix}"
        used_positive_labels.add(candidate)
        return candidate

    def make_positive_label_no_suffix(original_label):
        base = curated_positive_labels.get(original_label, f"{original_label} Excellence")
        if base == original_label:
            base = f"{original_label} Excellence"
        return base
    
    if not top_topics.empty:
        # Display as polished green cards
        for idx, (_, topic_row) in enumerate(top_topics.iterrows(), 1):
            topic_label = topic_row["topic_label"]
            display_label = make_positive_label(topic_label, idx)
            num_convs = int(topic_row["num_conversations"])
            avg_sat = topic_row["avg_satisfaction"]
            success_rate = topic_row["success_rate"]
            median_turns = int(topic_row["median_turns"])
            
            card_html = f"""
            <div style="
                background: linear-gradient(135deg, #f0fdf4 0%, #ffffff 100%);
                border: 1.5px solid #cde9d6;
                border-radius: 14px;
                padding: 16px 18px 14px;
                box-shadow: 0 8px 22px rgba(34, 197, 94, 0.12);
                margin-bottom: 1.0rem;
            ">
                <div style="display:flex; align-items:center; justify-content:space-between; gap:0.75rem;">
                    <div style="font-weight:800; font-size:1.12rem; color:#166534;">#{idx} {display_label}</div>
                    <div style="font-size:0.98rem; color:#16a34a; font-weight:700;">Success Rate {success_rate*100:.0f}%</div>
                </div>
                <div style="display:grid; grid-template-columns: repeat(4, minmax(0,1fr)); gap:0.75rem; margin:0.9rem 0 0.6rem 0;">
                    <div style="background:#ffffff; border:1px solid #e2e8f0; border-radius:10px; padding:10px 12px; text-align:center;">
                        <div style="font-size:1.6rem; font-weight:800; color:#0f172a;">{num_convs}</div>
                        <div style="font-size:0.95rem; color:#475569; font-weight:700;">Conversations</div>
                    </div>
                    <div style="background:#ffffff; border:1px solid #e2e8f0; border-radius:10px; padding:10px 12px; text-align:center;">
                        <div style="font-size:1.6rem; font-weight:800; color:#0f172a;">{avg_sat:.2f}</div>
                        <div style="font-size:0.95rem; color:#475569; font-weight:700;">Avg Satisfaction</div>
                    </div>
                    <div style="background:#ffffff; border:1px solid #e2e8f0; border-radius:10px; padding:10px 12px; text-align:center;">
                        <div style="font-size:1.6rem; font-weight:800; color:#0f172a;">{median_turns}</div>
                        <div style="font-size:0.95rem; color:#475569; font-weight:700;">Median Turns</div>
                    </div>
                    <div style="background:#ffffff; border:1px solid #e2e8f0; border-radius:10px; padding:10px 12px; text-align:center;">
                        <div style="font-size:1.6rem; font-weight:800; color:#0f172a;">{success_rate*100:.0f}%</div>
                        <div style="font-size:0.95rem; color:#475569; font-weight:700;">Success Rate</div>
                    </div>
                </div>
            </div>
            """
            st.markdown(card_html, unsafe_allow_html=True)
    else:
        st.info("No topic data available for top conversations.")
    
    # Step 3: Extract and display "Why it works" patterns
    st.divider()
    st.markdown("### 💡 Why These Interactions Work Well")
    st.markdown("*Patterns extracted from analysis of successful conversations:*")
    
    patterns_data = get_why_it_works_patterns(top_conversations, turns_df)
    
    if patterns_data["patterns"]:
        for pattern in patterns_data["patterns"]:
            pattern_html = f"""
            <div class="pattern-card">
                <div class="pattern-title">✓ {pattern['title']}</div>
                <div class="pattern-desc">{pattern['description']}</div>
                <div class="pattern-metric">📈 {pattern['metric']}</div>
            </div>
            """
            st.markdown(pattern_html, unsafe_allow_html=True)
    
    # Step 4: Show success examples
    st.divider()
    st.markdown("### 📖 Success Examples (Best Conversations)")
    st.markdown("*Representative conversations showing effective interaction patterns. Click any card to view the full conversation.*")
    
    # Initialize session state for expanded conversations
    if "expanded_conversations" not in st.session_state:
        st.session_state.expanded_conversations = {}
    
    # Get best examples from top conversations
    top_examples = sorted(top_conversations, key=lambda x: x["mean_satisfaction"], reverse=True)[:5]
    
    for i, conv in enumerate(top_examples, 1):
        # One-line reason based on metrics
        reason_parts = []
        if conv["turn_count"] <= 12:
            reason_parts.append("Efficient exchange")
        if conv["low_sat_count"] == 0:
            reason_parts.append("No issues")
        if conv["success_rate"] >= 0.95:
            reason_parts.append("High satisfaction")
        if not reason_parts:
            reason_parts.append("Exemplary interaction")
        
        one_line_reason = " • ".join(reason_parts)
        conv_id_key = int(conv['conv_id'])
        # For sample conversation cards, allow the same curated label without suffixes
        success_display_label = make_positive_label_no_suffix(conv["topic_label"])
        
        # Create columns for card and button
        col1, col2 = st.columns([0.95, 0.05])
        
        with col1:
            card_html = f"""
            <div style="
                background: linear-gradient(135deg, #eff6ff 0%, #ffffff 100%);
                border: 1.5px solid #bfdbfe;
                border-radius: 14px;
                padding: 16px 18px 14px;
                box-shadow: 0 8px 22px rgba(59, 130, 246, 0.12);
                margin-bottom: 1.0rem;
            ">
                <div style="display:flex; align-items:center; justify-content:space-between; gap:0.75rem;">
                    <div style="font-weight:800; font-size:1.12rem; color:#1e40af;">Example {i}: Conversation #{conv_id_key}</div>
                    <div style="font-size:0.98rem; color:#3b82f6; font-weight:700;">{one_line_reason}</div>
                </div>
                <div style="margin:0.6rem 0 0.6rem 0; color:#64748b; font-size:1.0rem; font-weight:600;">Topic: {success_display_label}</div>
                <div style="display:grid; grid-template-columns: repeat(3, minmax(0,1fr)); gap:0.75rem;">
                    <div style="background:#ffffff; border:1px solid #e2e8f0; border-radius:10px; padding:10px 12px; text-align:center;">
                        <div style="font-size:1.6rem; font-weight:800; color:#0f172a;">{conv['mean_satisfaction']:.2f}</div>
                        <div style="font-size:0.95rem; color:#475569; font-weight:700;">Satisfaction</div>
                    </div>
                    <div style="background:#ffffff; border:1px solid #e2e8f0; border-radius:10px; padding:10px 12px; text-align:center;">
                        <div style="font-size:1.6rem; font-weight:800; color:#0f172a;">{int(conv['turn_count'])}</div>
                        <div style="font-size:0.95rem; color:#475569; font-weight:700;">Turns</div>
                    </div>
                    <div style="background:#ffffff; border:1px solid #e2e8f0; border-radius:10px; padding:10px 12px; text-align:center;">
                        <div style="font-size:1.6rem; font-weight:800; color:#0f172a;">{conv['success_rate']*100:.0f}%</div>
                        <div style="font-size:0.95rem; color:#475569; font-weight:700;">Success Rate</div>
                    </div>
                </div>
            </div>
            """
            st.markdown(card_html, unsafe_allow_html=True)
        
        with col2:
            # Add button to toggle conversation view
            if st.button("→", key=f"conv_{conv_id_key}", help="View full conversation"):
                st.session_state.expanded_conversations[conv_id_key] = not st.session_state.expanded_conversations.get(conv_id_key, False)
                st.rerun()
        
        # Show conversation if expanded
        if st.session_state.expanded_conversations.get(conv_id_key, False):
            # Get all turns for this conversation
            conv_turns = turns_df[turns_df["conv_id"] == conv_id_key].sort_values("turn_id")
            
            if not conv_turns.empty:
                with st.container(border=True):
                    st.markdown(f"#### Conversation Details — #{conv_id_key}")
                    
                    # Success summary box
                    st.markdown(
                        f"""
                        <div style="padding: 0.75rem 0.9rem; border: 1px solid #34d399; background: #ecfdf3; border-radius: 10px; margin: 0.5rem 0 0.75rem;">
                            <div style="font-weight: 800; color: #065f46; margin-bottom: 0.35rem;">✓ Success Summary</div>
                            <div style="color: #334155;"><strong>Topic:</strong> {success_display_label}</div>
                            <div style="color: #334155;"><strong>Satisfaction:</strong> {conv['mean_satisfaction']:.2f}/5</div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                    
                    # Conversation turns
                    st.markdown("**Exchange:**")
                    for _, row in conv_turns.iterrows():
                        if row["speaker"] == "USER":
                            st.markdown(f"🧑 **User:** {row['text']}")
                        else:
                            st.markdown(f"🤖 **Assistant:** {row['text']}")
    
    # Additional insights box
    st.divider()
    with st.container(border=True):
        st.markdown("### 🎯 Key Takeaways")
        
        # Compute summary stats
        avg_sat = sum([c["mean_satisfaction"] for c in top_conversations]) / len(top_conversations)
        avg_turns = sum([c["turn_count"] for c in top_conversations]) / len(top_conversations)
        
        st.markdown(f"""
- **Top 50 conversations** have an average satisfaction of **{avg_sat:.2f}/5**
- **Average turns per conversation**: {avg_turns:.1f} (efficient, focused exchanges)
- **Most successful topic**: {top_topics.iloc[0]["topic_label"] if not top_topics.empty else "N/A"} 
  (Avg satisfaction: {top_topics.iloc[0]["avg_satisfaction"]:.2f} if not top_topics.empty else "N/A")
        """)
    
    # Next steps
    with st.container(border=True):
        st.markdown("### 🚀 Next Steps to Scale Success")
        st.markdown(
            "1. **Share playbook**: Distribute top 5 conversations as reference examples to the team\n"
            "2. **Mirror patterns**: Apply successful interaction patterns to similar topics\n"
            "3. **Monitor lift**: Re-run this analysis weekly to confirm improvements\n"
            "4. **Expand coverage**: Scale patterns from rare but successful topics to more requests"
        )

    # Technical notes
    with st.container(border=True):
        st.markdown("### 📌 Technical Notes")
        st.markdown(
            "- **Top 50 methodology**: Conversations ranked by satisfaction score (descending), with tie-breakers on success metrics\n"
            "- **Topic assignment**: Most frequent topic in conversation used; NaN topics replaced with 'General Product Questions & Miscellaneous'\n"
            "- **Patterns**: Extracted from issue presence, knowledge base alignment, turn efficiency, and success rates\n"
            "- **Examples**: Shows satisfaction score and turn count for full transparency"
        )
