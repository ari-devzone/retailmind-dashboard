import streamlit as st
from logic.aggregations import rank_topics
from logic.aggregations import compute_severity_stats
from logic.aggregations import infer_conversation_theme
from ui.conversations import render_conversations
from ui.repairs import render_repair

# def diagnostics_page(df_topics):
#     st.title("🔍 Diagnostics – Failure Topics")

#     ranked = rank_topics(df_topics)

#     for _, row in ranked.iterrows():
#         with st.container(border=True):
#             st.subheader(row["topic_label"])
#             st.write(f"**Examples:** {row['n_examples']}")
#             st.write(f"**Low satisfaction rate:** {row['low_satisfaction_rate']:.2f}")

#             if st.button(
#                 "Explore topic",
#                 key=f"topic_{row['topic_id']}"
#             ):
#                 st.session_state["selected_topic"] = row["topic_id"]
#                 st.session_state["page"] = "topic"

# def render_diagnostics(turns_df, topics_df, repairs_df):
#     st.header("Diagnostics – Failures")

#     topic_id = st.selectbox(
#         "Select Failure Topic",
#         topics_df["topic_id"],
#         format_func=lambda x: topics_df.set_index("topic_id").loc[x, "topic_label"]
#     )

#     topic_meta = topics_df[topics_df["topic_id"] == topic_id].iloc[0]
#     topic_turns = turns_df[turns_df["topic_id"] == topic_id]

#     severity = compute_severity_stats(topic_turns)

#     st.subheader(topic_meta["topic_label"])
#     st.caption(topic_meta["example_reason"])

#     st.markdown(
#         f"""
# **Examples:** {topic_meta["n_examples"]}  
# **Avg Satisfaction:** {topic_meta["avg_satisfaction"]:.2f}  
# **Dominant Severity:** {severity["dominant_severity"]}
# """
#     )

#     render_conversations(turns_df, topic_id)
#     render_repair(repairs_df, topic_id)

import streamlit as st
from ui.topic_page import render_topic_page

def render_diagnostics(turns_df, topics_df, repairs_df):
    if "selected_topic" not in st.session_state:
        st.session_state.selected_topic = None

    # ---- Topic List ----
    if st.session_state.selected_topic is None:
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
                border-bottom: 3px solid #dc2626;
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
            </style>
            """,
            unsafe_allow_html=True
        )
        st.markdown('<h1 class="page-header">🚨 Failure Topics</h1>', unsafe_allow_html=True)

        # Custom CSS for styling
        st.markdown("""
        <style>
        /* Diagnostics card container styling */
        .diag-card-container {
            background: linear-gradient(135deg, #fef2f2 0%, #ffffff 100%);
            border: 2px solid #fecaca;
            border-radius: 12px;
            padding: 1rem;
            margin-bottom: 0.5rem;
            box-shadow: 0 4px 12px rgba(239, 68, 68, 0.1);
            transition: all 0.3s ease;
        }
        .diag-card-container:hover {
            box-shadow: 0 8px 24px rgba(239, 68, 68, 0.18);
            transform: translateY(-2px);
        }
        
        /* Topic title styling */
        .diag-topic-title {
            font-size: 1.4rem;
            font-weight: 800;
            color: #991b1b;
            margin-bottom: 0.5rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        .diag-topic-icon {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background: #dc2626;
            display: inline-block;
        }
        
        /* Caption styling */
        .diag-caption {
            color: #64748b;
            font-size: 1rem;
            line-height: 1.5;
            margin-bottom: 1rem;
            padding-bottom: 0.75rem;
            border-bottom: 1px solid #fee2e2;
        }
        
        /* Metrics container */
        .diag-metrics {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 1rem;
            margin: 1rem 0;
        }
        
        .diag-metric-card {
            background: white;
            border: 1.5px solid #fecaca;
            border-radius: 8px;
            padding: 0.9rem;
            text-align: center;
            transition: all 0.2s ease;
        }
        .diag-metric-card:hover {
            border-color: #f87171;
            box-shadow: 0 2px 8px rgba(239, 68, 68, 0.15);
        }
        
        .diag-metric-label {
            font-size: 0.85rem;
            font-weight: 600;
            color: #b91c1c;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 0.4rem;
        }
        
        .diag-metric-value {
            font-size: 1.8rem;
            font-weight: 800;
            color: #0f172a;
            line-height: 1.2;
        }
        
        /* Top issues section */
        .diag-issues {
            background: #fef3c7;
            border: 1px solid #fcd34d;
            border-radius: 8px;
            padding: 0.9rem;
            margin-top: 1rem;
        }
        
        .diag-issues-label {
            font-size: 0.85rem;
            font-weight: 700;
            color: #92400e;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 0.4rem;
        }
        
        .diag-issues-list {
            color: #451a03;
            font-size: 0.95rem;
            font-weight: 500;
        }
        </style>
        """, unsafe_allow_html=True)

        used_failure_labels = set()

        for idx, (_, row) in enumerate(topics_df.iterrows(), 1):
            # Infer a human-friendly theme from the topic's conversations
            topic_turns = turns_df[turns_df["topic_id"] == row["topic_id"]]
            theme_label = row["topic_label"]
            if not topic_turns.empty:
                inferred = infer_conversation_theme(topic_turns)
                if inferred:
                    theme_label = inferred

            # Ensure failure titles are distinct from success titles and from each other
            base_label = f"Failure - {theme_label}"
            unique_label = base_label
            suffix = 1
            while unique_label in used_failure_labels:
                suffix += 1
                unique_label = f"{base_label} #{suffix}"
            used_failure_labels.add(unique_label)
            
            # Create columns for card and arrow button
            col1, col2 = st.columns([0.95, 0.05])
            
            with col1:
                card_html = f"""
                <div style="
                    background: linear-gradient(135deg, #fef2f2 0%, #ffffff 100%);
                    border: 1.5px solid #fecaca;
                    border-radius: 14px;
                    padding: 16px 18px 14px;
                    box-shadow: 0 8px 22px rgba(220, 38, 38, 0.12);
                    margin-bottom: 1.0rem;
                ">
                    <div style="font-weight:800; font-size:1.12rem; color:#991b1b; margin-bottom:0.3rem;">#{idx} {unique_label}</div>
                    <div style="color: #64748b; font-size:1.0rem; line-height:1.5; margin:0.6rem 0 0.8rem 0; padding-bottom:0.7rem; border-bottom:1px solid #fee2e2;">{row['example_reason']}</div>
                    <div style="display:grid; grid-template-columns: repeat(3, minmax(0,1fr)); gap:0.75rem; margin:0.9rem 0 0.6rem 0;">
                        <div style="background:#ffffff; border:1px solid #e2e8f0; border-radius:10px; padding:10px 12px; text-align:center;">
                            <div style="font-size:1.6rem; font-weight:800; color:#0f172a;">{int(row['n_examples'])}</div>
                            <div style="font-size:0.95rem; color:#475569; font-weight:700;">Examples</div>
                        </div>
                        <div style="background:#ffffff; border:1px solid #e2e8f0; border-radius:10px; padding:10px 12px; text-align:center;">
                            <div style="font-size:1.6rem; font-weight:800; color:#0f172a;">{row['avg_satisfaction']:.2f}</div>
                            <div style="font-size:0.95rem; color:#475569; font-weight:700;">Avg Satisfaction</div>
                        </div>
                        <div style="background:#ffffff; border:1px solid #e2e8f0; border-radius:10px; padding:10px 12px; text-align:center;">
                            <div style="font-size:1.6rem; font-weight:800; color:#0f172a;">{int(row['n_user_turns'])}</div>
                            <div style="font-size:0.95rem; color:#475569; font-weight:700;">User Turns</div>
                        </div>
                    </div>
                    <div style="background:#fffbeb; border:1px solid #fde68a; border-radius:10px; padding:1rem; margin-top:0.6rem;">
                        <div style="font-weight:800; color:#b45309; margin-bottom:0.4rem; font-size:0.95rem;">🔍 Top Issues</div>
                        <div style="color:#78350f; font-size:1.02rem; line-height:1.5;">{', '.join(row['top_issues'])}</div>
                    </div>
                </div>
                """
                
                st.markdown(card_html, unsafe_allow_html=True)
            
            with col2:
                # Arrow button to navigate to topic details
                if st.button("→", key=f"explore_{row['topic_id']}", help="View topic details"):
                    st.session_state.selected_topic = row["topic_id"]
                    st.session_state.topic_rank = idx  # Store the rank number
                    st.session_state.topic_display_label = unique_label  # Store the full label
                    st.rerun()

    # ---- Topic Detail Page ----
    else:
        # Validate the selected topic and try to resolve by label if needed
        selected = st.session_state.selected_topic

        if not topics_df["topic_id"].isin([selected]).any():
            # Attempt to map from topic_label to topic_id if a label snuck into state
            if "topic_label" in topics_df.columns and topics_df["topic_label"].isin([selected]).any():
                resolved_id = topics_df.loc[topics_df["topic_label"] == selected, "topic_id"].iloc[0]
                st.session_state.selected_topic = resolved_id
                selected = resolved_id
            else:
                st.warning("Selected topic not found. Returning to topics list.")
                st.session_state.selected_topic = None
                st.rerun()

        # If we have a valid topic id, render details
        if st.session_state.selected_topic is not None:
            render_topic_page(
                turns_df,
                topics_df,
                repairs_df,
                st.session_state.selected_topic
            )

            if st.button("← Back to Topics"):
                st.session_state.selected_topic = None
                st.rerun()
