import streamlit as st

# def repair_page(df_topics, df_repairs):
#     topic_id = st.session_state.get("selected_topic")

#     topic = df_topics[df_topics["topic_id"] == topic_id].iloc[0]
#     repair = df_repairs[df_repairs["topic_id"] == topic_id].iloc[0]

#     st.title("🛠 Repair Package")

#     st.subheader("Root Cause")
#     st.write(repair["root_cause"])

#     st.subheader("Suggested Prompt Changes")
#     for item in repair["suggested_prompt_changes"]:
#         st.markdown(f"- {item}")

#     st.subheader("System Prompt Snippet")
#     st.code(repair["system_prompt_snippet"])

#     st.subheader("Guardrails")
#     for rule in repair["guardrail_rules"]:
#         st.markdown(f"- {rule}")

#     st.subheader("Evaluation Checks")
#     for check in repair["evaluation_checks"]:
#         st.markdown(f"- {check}")

#     if st.button("⬅ Back to Diagnostics"):
#         st.session_state["page"] = "diagnostics"


def render_repair(repairs_df, topic_id):
    repair = repairs_df[repairs_df["topic_id"] == topic_id]

    if repair.empty:
        st.info("No repair package available.")
        return

    r = repair.iloc[0]

    with st.expander("View Repair Package", expanded=False):
        # Root Cause
        st.markdown("### 🔍 Root Cause")
        st.markdown(
            f"""
            <div style="background: #fef2f2; border-left: 4px solid #dc2626; border-radius: 8px; padding: 1rem; margin: 0.5rem 0;">
                <p style="margin: 0; font-size: 1rem; line-height: 1.6; color: #1e293b;">{r['root_cause']}</p>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        st.markdown("---")
        
        # Suggested Prompt Changes
        st.markdown("### 📝 Suggested Prompt Changes")
        prompt_changes = r["suggested_prompt_changes"]
        if isinstance(prompt_changes, list):
            formatted_text = "\n".join(prompt_changes)
        else:
            formatted_text = prompt_changes
        st.code(formatted_text, language=None)

        st.markdown("---")
        
        # System Prompt Snippet
        st.markdown("### ⚙️ System Prompt Snippet")
        st.code(r["system_prompt_snippet"], language=None)

        st.markdown("---")
        
        # Guardrails
        st.markdown("### 🛡️ Guardrails")
        for idx, g in enumerate(r["guardrail_rules"], 1):
            st.markdown(f"{idx}. {g}")
