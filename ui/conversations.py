import streamlit as st

PAGE_SIZE = 1

def render_conversations(turns_df, topic_id):
    # Find conv_ids that have at least one turn with the given topic_id
    relevant_conv_ids = turns_df[turns_df["topic_id"] == topic_id]["conv_id"].unique()

    if "conv_page" not in st.session_state:
        st.session_state.conv_page = 0

    start = st.session_state.conv_page * PAGE_SIZE
    end = start + PAGE_SIZE

    for conv_id in relevant_conv_ids[start:end]:
        # Get all turns for this conv_id, regardless of topic_id
        conv = turns_df[turns_df["conv_id"] == conv_id].sort_values("turn_id")

        # Pull failure details for this specific topic within the conversation
        failed = conv[(conv["low_satisfaction"] == True) & (conv["topic_id"] == topic_id)]

        with st.container(border=True):
            st.markdown(f"**Conversation ID:** {conv_id}")

            # Distinct summary box above the conversation
            if not failed.empty:
                f = failed.iloc[0]
                st.markdown(
                    """
                    <div style="padding: 0.75rem 0.9rem; border: 1px solid #f59e0b; background: #fff7ed; border-radius: 10px; margin: 0.5rem 0 0.75rem;">
                        <div style="font-weight: 800; color: #9a3412; margin-bottom: 0.35rem;">Failure Summary</div>
                        <div style="color: #334155;"><strong>Issues:</strong> {issues}</div>
                        <div style="color: #334155;"><strong>Reason:</strong> {reason}</div>
                        <div style="color: #334155;"><strong>Severity:</strong> {severity}</div>
                    </div>
                    """
                    .format(
                        issues=", ".join(f["issues"]) if f.get("issues") else "General failure",
                        reason=f.get("reason", "N/A"),
                        severity=f.get("severity", "N/A")
                    ),
                    unsafe_allow_html=True
                )

            # Conversation turns
            for _, row in conv.iterrows():
                if row["speaker"] == "USER":
                    st.markdown(f"🧑 **User:** {row['text']}")
                else:
                    st.markdown(f"🤖 **Assistant:** {row['text']}")

    if end < len(relevant_conv_ids):
        st.markdown('<div class="topic-page-buttons">', unsafe_allow_html=True)
        if st.button("Other Sample"):
            st.session_state.conv_page += 1
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
