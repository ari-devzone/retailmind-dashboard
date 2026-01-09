import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime, timedelta
from logic.aggregations import infer_conversation_theme

def render_overview(turns_df, topics_df):
    # Initialize metrics history in session state
    if "metrics_history" not in st.session_state:
        st.session_state.metrics_history = []
    
    # Calculate current metrics
    mean_sat = turns_df["satisfaction_score"].mean()
    low_sat_rate = turns_df["low_satisfaction"].mean()
    n_topics = len(topics_df)
    low_sat_turns = (turns_df["low_satisfaction"] == True).sum()
    avg_severity_low_sat = turns_df[turns_df["low_satisfaction"] == True]["satisfaction_score"].mean()
    
    current_metrics = {
        "mean_sat": mean_sat,
        "low_sat_rate": low_sat_rate,
        "n_topics": n_topics,
        "low_sat_turns": low_sat_turns,
        "avg_severity": avg_severity_low_sat,
        "total_turns": len(turns_df),
        "total_convs": turns_df["conv_id"].nunique(),
        "timestamp": datetime.now()
    }
    
    # Check if metrics changed (data updated)
    if not st.session_state.metrics_history or st.session_state.metrics_history[-1]["total_turns"] != current_metrics["total_turns"]:
        st.session_state.metrics_history.append(current_metrics)
        # Keep only last 10 snapshots
        if len(st.session_state.metrics_history) > 10:
            st.session_state.metrics_history = st.session_state.metrics_history[-10:]
    
    # Calculate deltas if we have previous data
    prev_metrics = st.session_state.metrics_history[-2] if len(st.session_state.metrics_history) > 1 else None
    
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
            border-bottom: 3px solid #3b82f6;
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
    
    st.markdown('<h1 class="page-header">📊 System Overview</h1>', unsafe_allow_html=True)
    
    # Add comparison toggle and history selector in a professional container
    with st.container(border=True):
        col_compare, col_spacer, col_history = st.columns([1.2, 0.3, 1])
        with col_compare:
            if len(st.session_state.metrics_history) > 1:
                st.markdown("**Show Changes**")
                show_comparison = st.toggle("", value=True, help="Compare with previous snapshot", label_visibility="collapsed")
            else:
                show_comparison = False
                st.caption("_Upload data to see changes_")
        
        with col_history:
            if len(st.session_state.metrics_history) > 1:
                st.markdown("**📅 Time Period**")
                history_view = st.selectbox(
                    "View Period",
                    options=["Past Day", "Past Week", "Past Month", "All History"],
                    help="Filter metrics by time period",
                    label_visibility="collapsed"
                )
            else:
                history_view = "Past Day"
    
    st.markdown('<h2 class="page-subheader">Key Metrics</h2>', unsafe_allow_html=True)

    st.markdown(
        """
<style>
.kpi-grid {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 0.9rem;
    margin-bottom: 1rem;
}
@media (max-width: 1100px) { .kpi-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
@media (max-width: 700px) { .kpi-grid { grid-template-columns: 1fr; } }

.kpi-card {
    border-radius: 12px;
    padding: 1rem 1.05rem 0.85rem;
    border: 1.5px solid #e2e8f0;
    background: #ffffff;
    box-shadow: 0 6px 18px rgba(15, 23, 42, 0.08);
    display: flex;
    flex-direction: column;
    gap: 0.45rem;
}
.kpi-head { display: flex; align-items: center; gap: 0.4rem; font-weight: 700; color: #0f172a; }
.dot { width: 10px; height: 10px; border-radius: 50%; }
.dot-amber { background: #d97706; }
.dot-red { background: #dc2626; }
.dot-green { background: #059669; }

.kpi-value { font-size: 2rem; font-weight: 800; color: #0b1324; line-height: 1.1; }
.kpi-sub { color: #475569; font-size: 1.02rem; }

.kpi-footer { margin-top: 0.25rem; display: flex; justify-content: space-between; align-items: center; gap: 0.5rem; }
.kpi-btn {
    background: #0b1324;
    color: #f8fafc;
    border: 1px solid #0f172a;
    border-radius: 8px;
    padding: 0.35rem 0.75rem;
    font-weight: 700;
    font-size: 1rem;
    cursor: default;
    text-align: center;
}
.kpi-hint { color: #6b7280; font-size: 0.95rem; }

/* Color accents for card borders/backgrounds */
.card-amber { border-color: #facc15; background: #fffbeb; }
.card-red { border-color: #f87171; background: #fef2f2; }
.card-green { border-color: #34d399; background: #e7f8f1; }

/* Topic cards */
.topic-grid {
    display: grid;
    grid-template-columns: repeat(5, minmax(0, 1fr));
    gap: 0.9rem;
}
@media (max-width: 1200px) { .topic-grid { grid-template-columns: repeat(3, minmax(0, 1fr)); } }
@media (max-width: 900px) { .topic-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
@media (max-width: 640px) { .topic-grid { grid-template-columns: 1fr; } }

.topic-card {
    border-radius: 12px;
    padding: 0.9rem 1.05rem 1rem;
    border: 1.5px solid #f87171;
    background: #fef2f2;
    box-shadow: 0 6px 18px rgba(15, 23, 42, 0.08);
    display: flex;
    flex-direction: column;
    gap: 0.35rem;
    min-height: 140px;
    position: relative;
}
.topic-title { font-weight: 750; color: #991b1b; display: flex; align-items: center; gap: 0.4rem; font-size: 1rem; }
.topic-value { font-size: 1.6rem; font-weight: 800; color: #0b1324; line-height: 1.1; }
.topic-sub { color: #475569; font-size: 1.02rem; margin-bottom: 0.5rem; }
.topic-footer { position: absolute; bottom: 0.5rem; right: 0.5rem; }
.topic-btn {
    background: linear-gradient(135deg, #64748b 0%, #475569 100%);
    color: #ffffff;
    border: none;
    border-radius: 6px;
    padding: 0.4rem 0.8rem;
    font-weight: 700;
    font-size: 0.92rem;
    text-align: center;
    display: inline-block;
}

/* Investigate button styling */
.topic-card .topic-footer div[data-testid="stButton"] button {
    background: linear-gradient(135deg, #64748b 0%, #475569 100%) !important;
    color: white !important;
    border: none !important;
    font-weight: 700 !important;
    border-radius: 6px !important;
    padding: 0.4rem 0.8rem !important;
    font-size: 0.92rem !important;
    box-shadow: 0 2px 8px rgba(71, 85, 105, 0.4) !important;
    transition: all 0.2s ease !important;
    height: auto !important;
    min-height: 32px !important;
    position: absolute !important;
    bottom: 0 !important;
    right: 0 !important;
}
div[data-testid="column"] > div > div[data-testid="stVerticalBlock"] > div[data-testid="stButton"] button:hover {
    background: linear-gradient(135deg, #475569 0%, #334155 100%) !important;
    box-shadow: 0 4px 12px rgba(71, 85, 105, 0.5) !important;
    transform: translateY(-1px) !important;
}
.topic-card-wrapper {
    display: flex;
    flex-direction: column;
    height: 100%;
}
.topic-card-wrapper .topic-card {
    flex: 1;
    display: flex;
    flex-direction: column;
}
hr {
    margin: 0.35rem 0 0.65rem;
    border: none;
    border-top: 1px solid #e2e8f0;
}
</style>
        """,
        unsafe_allow_html=True,
    )

    # Build labels that mirror the Diagnostics page (inferred themes + unique prefixes)
    diagnostics_labels = {}
    diagnostics_ranks = {}  # Store rank for each topic
    used_labels = set()
    for rank, (_, topic_row) in enumerate(topics_df.sort_values("n_examples", ascending=False).iterrows(), 1):
        topic_turns = turns_df[turns_df["topic_id"] == topic_row["topic_id"]]
        theme_label = topic_row["topic_label"]
        if not topic_turns.empty:
            inferred = infer_conversation_theme(topic_turns)
            if inferred:
                theme_label = inferred

        base_label = f"Failure - {theme_label}"
        unique_label = base_label
        suffix = 1
        while unique_label in used_labels:
            suffix += 1
            unique_label = f"{base_label} #{suffix}"

        used_labels.add(unique_label)
        diagnostics_labels[topic_row["topic_id"]] = unique_label
        diagnostics_ranks[topic_row["topic_id"]] = rank

    avg_severity_display = f"{avg_severity_low_sat:.2f}" if pd.notna(avg_severity_low_sat) else "N/A"
    
    # Calculate deltas for display
    if show_comparison and prev_metrics:
        delta_low_sat_rate = ((low_sat_rate - prev_metrics["low_sat_rate"]) * 100)
        delta_low_sat_turns = low_sat_turns - prev_metrics["low_sat_turns"]
        delta_mean_sat = mean_sat - prev_metrics["mean_sat"]
        delta_severity = avg_severity_low_sat - prev_metrics["avg_severity"] if pd.notna(avg_severity_low_sat) and pd.notna(prev_metrics["avg_severity"]) else 0
        delta_topics = n_topics - prev_metrics["n_topics"]
        
        # Format deltas with arrows - Green for good, Red for bad
        def format_delta(value, is_percentage=False, inverse=False):
            if abs(value) < 0.01:
                return ""
            
            arrow = "↑" if value > 0 else "↓"
            
            # Determine color based on whether change is good or bad
            if inverse:
                # For satisfaction/severity: up is good (green), down is bad (red)
                is_good = value > 0
            else:
                # For low sat rate/turns: down is good (green), up is bad (red)
                is_good = value < 0
            
            color = "#059669" if is_good else "#dc2626"  # Green if good, Red if bad
            
            if is_percentage:
                return f'<span style="color:{color}; font-size:1.3rem; font-weight:800;">{arrow} {abs(value):.1f}pp</span>'
            else:
                return f'<span style="color:{color}; font-size:1.3rem; font-weight:800;">{arrow} {abs(value):.0f}</span>'
        
        delta_html_low_sat_rate = format_delta(delta_low_sat_rate, is_percentage=True)
        delta_html_low_sat_turns = format_delta(delta_low_sat_turns)
        delta_html_mean_sat = format_delta(delta_mean_sat, inverse=True)
        delta_html_severity = format_delta(delta_severity, inverse=True) if delta_severity != 0 else ""
        delta_html_topics = format_delta(delta_topics)
    else:
        delta_html_low_sat_rate = ""
        delta_html_low_sat_turns = ""
        delta_html_mean_sat = ""
        delta_html_severity = ""
        delta_html_topics = ""

    st.markdown(
        f"""
<div class="kpi-grid">
    <div class="kpi-card card-amber">
        <div class="kpi-head"><span class="dot dot-amber"></span>Low Satisfaction Rate (&lt;3)</div>
        <div class="kpi-value">{low_sat_rate*100:.1f}% {delta_html_low_sat_rate}</div>
        <div class="kpi-sub">share of all turns</div>
    </div>
    <div class="kpi-card card-red">
        <div class="kpi-head"><span class="dot dot-red"></span>Failure Volume (low-sat turns)</div>
        <div class="kpi-value">{low_sat_turns} {delta_html_low_sat_turns}</div>
        <div class="kpi-sub">total low-satisfaction turns</div>
    </div>
    <div class="kpi-card card-green">
        <div class="kpi-head"><span class="dot dot-green"></span>Satisfaction Mean (CSAT proxy)</div>
        <div class="kpi-value">{mean_sat:.2f} {delta_html_mean_sat}</div>
        <div class="kpi-sub">average satisfaction</div>
    </div>
    <div class="kpi-card card-green">
        <div class="kpi-head"><span class="dot dot-green"></span>Avg Severity (low-sat only)</div>
        <div class="kpi-value">{avg_severity_display} {delta_html_severity}</div>
        <div class="kpi-sub">out of 5</div>
    </div>
    <div class="kpi-card card-red">
        <div class="kpi-head"><span class="dot dot-amber"></span>Failure Topics</div>
        <div class="kpi-value">{n_topics} {delta_html_topics}</div>
        <div class="kpi-sub">active low-satisfaction topics</div>
    </div>
</div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

    # ---- Satisfaction Distribution ----
    st.markdown('<h2 class="page-subheader">Failure Analytics</h2>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3, gap="medium")
    
    with col1:
        with st.container(border=True):
            st.markdown("**� Failure Root Causes Breakdown**")
            
            # Get all failure turns and extract issues
            failure_turns = turns_df[turns_df["low_satisfaction"] == True].copy()
            
            # Explode the issues list to count individual issue types
            issue_counts = {}
            for issues_list in failure_turns["issues"]:
                if isinstance(issues_list, list):
                    for issue in issues_list:
                        if issue:  # Skip empty strings
                            issue_counts[issue] = issue_counts.get(issue, 0) + 1
            
            if issue_counts:
                issue_df = pd.DataFrame([
                    {"Issue Type": issue, "Count": count}
                    for issue, count in sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)
                ])
                
                # Create selection for interactivity
                issue_click = alt.selection_point(fields=['Issue Type'], name='issue_select')
                
                chart = alt.Chart(issue_df).mark_bar(color="#ef4444").encode(
                    x=alt.X("Count:Q", title="Number of Occurrences"),
                    y=alt.Y("Issue Type:N", title="", sort="-x"),
                    opacity=alt.condition(issue_click, alt.value(1), alt.value(0.5)),
                    tooltip=["Issue Type", "Count"]
                ).add_params(issue_click).properties(height=300)
                
                issue_chart_selection = st.altair_chart(chart, use_container_width=True, on_select="rerun", key="issue_chart")
                
                # Show topics for selected issue type
                if issue_chart_selection and "selection" in issue_chart_selection and "issue_select" in issue_chart_selection["selection"]:
                    selected_points = issue_chart_selection["selection"]["issue_select"]
                    if selected_points:
                        selected_issue = selected_points[0]["Issue Type"]
                        
                        # Find topics with this issue type
                        topics_with_issue = []
                        for _, turn in failure_turns.iterrows():
                            if isinstance(turn["issues"], list) and selected_issue in turn["issues"]:
                                if turn["topic_id"] != -1:
                                    topics_with_issue.append(turn["topic_id"])
                        
                        if topics_with_issue:
                            # Count occurrences
                            from collections import Counter
                            topic_counts = Counter(topics_with_issue)
                            top_topics = topic_counts.most_common(5)
                            
                            st.markdown(f"**Topics with {selected_issue}:**")
                            for topic_id, count in top_topics:
                                # Use diagnostics label mapping
                                display_label = diagnostics_labels.get(topic_id, "Unknown Topic")
                                col_topic, col_btn = st.columns([3, 1])
                                with col_topic:
                                    st.markdown(f"• **{display_label}** ({count} occurrences)")
                                with col_btn:
                                    if st.button("View", key=f"issue_{selected_issue}_{topic_id}"):
                                        st.session_state.page = "Diagnostics"
                                        st.session_state.selected_topic = topic_id
                                        st.rerun()
            else:
                st.info("No issues detected in failure data.")
    
    with col2:
        with st.container(border=True):
            st.markdown("**✅ Success vs. Failure Rate**")
            success_dist = pd.DataFrame({
                "Status": ["Successful", "Failed"],
                "Count": [
                    (turns_df["low_satisfaction"] == False).sum(),
                    (turns_df["low_satisfaction"] == True).sum()
                ]
            })
            
            total = success_dist["Count"].sum()
            success_dist["Percentage"] = (success_dist["Count"] / total * 100).round(1)

            # Create columns for chart and legend
            chart_col, legend_col = st.columns([2, 1])
            
            with chart_col:
                success_click = alt.selection_point(fields=['Status'], name='status_select')

                pie_chart = alt.Chart(success_dist).mark_arc(innerRadius=55).encode(
                    theta="Count:Q",
                    color=alt.Color(
                        "Status:N",
                        scale=alt.Scale(
                            domain=["Successful", "Failed"],
                            range=["#22c55e", "#ef4444"]
                        ),
                        legend=None
                    ),
                    opacity=alt.condition(success_click, alt.value(1), alt.value(0.55)),
                    tooltip=["Status", "Count", "Percentage"]
                ).add_params(success_click).properties(height=280, width=280)

                success_chart_selection = st.altair_chart(pie_chart, use_container_width=False, on_select="rerun", key="success_failure_chart")
            
            with legend_col:
                st.markdown(
                    f"""
                    <div style="display: flex; flex-direction: column; justify-content: center; height: 280px; padding-left: 0.5rem; font-size: 0.85rem;">
                        <div style="margin-bottom: 1.5rem;">
                            <div style="display: flex; align-items: center; margin-bottom: 0.4rem;">
                                <div style="width: 18px; height: 18px; background: #22c55e; border-radius: 4px; margin-right: 0.5rem;"></div>
                                <strong style="color: #22c55e; font-size: 0.95rem;">Successful</strong>
                            </div>
                            <div style="font-size: 1.4rem; font-weight: 800; color: #0f172a; margin-left: 1.5rem;">
                                {success_dist[success_dist['Status'] == 'Successful']['Percentage'].values[0]:.1f}%
                            </div>
                        </div>
                        <div>
                            <div style="display: flex; align-items: center; margin-bottom: 0.4rem;">
                                <div style="width: 18px; height: 18px; background: #ef4444; border-radius: 4px; margin-right: 0.5rem;"></div>
                                <strong style="color: #ef4444; font-size: 0.95rem;">Failed</strong>
                            </div>
                            <div style="font-size: 1.4rem; font-weight: 800; color: #0f172a; margin-left: 1.5rem;">
                                {success_dist[success_dist['Status'] == 'Failed']['Percentage'].values[0]:.1f}%
                            </div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            
            # Show topics for selected status
            if success_chart_selection and "selection" in success_chart_selection and "status_select" in success_chart_selection["selection"]:
                selected_points = success_chart_selection["selection"]["status_select"]
                if selected_points:
                    selected_status = selected_points[0]["Status"]
                    
                    if selected_status == "Failed":
                        st.markdown(f"**Top Failure Topics:**")
                        top_failure_topics = topics_df.nlargest(5, "n_examples")[
                            ["topic_id", "topic_label", "n_examples"]
                        ].copy()
                        top_failure_topics["diag_label"] = top_failure_topics["topic_id"].map(diagnostics_labels)

                        for _, row in top_failure_topics.iterrows():
                            col_topic, col_btn = st.columns([3, 1])
                            with col_topic:
                                st.markdown(f"• **{row['diag_label']}** ({int(row['n_examples'])} examples)")
                            with col_btn:
                                if st.button("View", key=f"fail_{row['topic_id']}"):
                                    st.session_state.page = "Diagnostics"
                                    st.session_state.selected_topic = row['topic_id']
                                    st.session_state.topic_rank = diagnostics_ranks.get(row['topic_id'], 0)
                                    st.session_state.topic_display_label = row['diag_label']
                                    st.rerun()
    
    with col3:
        with st.container(border=True):
            st.markdown("**⚠️ Failure Severity Distribution**")
            
            # Get severity distribution for failed turns
            failure_turns = turns_df[turns_df["low_satisfaction"] == True].copy()

            # Compute counts by dominant severity per topic to align with topic pages
            from logic.aggregations import compute_severity_stats, get_topic_turns
            topic_ids = failure_turns["topic_id"].dropna().unique().tolist()
            dominant_counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0, "NONE": 0}
            for tid in topic_ids:
                topic_df = get_topic_turns(failure_turns, tid)
                stats = compute_severity_stats(topic_df)
                dom = stats.get("dominant_severity")
                if dom in dominant_counts:
                    dominant_counts[dom] += 1

            severity_counts = pd.DataFrame({
                "Severity": list(dominant_counts.keys()),
                "Count": list(dominant_counts.values())
            })
            
            # Define severity order and colors
            severity_order = ["HIGH", "MEDIUM", "LOW", "NONE"]
            severity_colors = {"HIGH": "#dc2626", "MEDIUM": "#f59e0b", "LOW": "#fbbf24", "NONE": "#d1d5db"}
            
            # Filter to only existing severities
            severity_counts = severity_counts[severity_counts["Severity"].isin(severity_order)]
            
            if not severity_counts.empty:
                # Create columns for chart and legend (similar to success/failure chart)
                sev_chart_col, sev_legend_col = st.columns([2, 1])
                
                with sev_chart_col:
                    click = alt.selection_point(fields=['Severity'], name='severity_select')

                    severity_chart = alt.Chart(severity_counts).mark_arc(innerRadius=55).encode(
                        theta="Count:Q",
                        color=alt.Color(
                            "Severity:N",
                            scale=alt.Scale(
                                domain=list(severity_colors.keys()),
                                range=list(severity_colors.values())
                            ),
                            sort=severity_order,
                            legend=None
                        ),
                        opacity=alt.condition(click, alt.value(1), alt.value(0.55)),
                        tooltip=["Severity", "Count"]
                    ).add_params(click).properties(height=280, width=280)
                    
                    chart_selection = st.altair_chart(severity_chart, use_container_width=False, on_select="rerun", key="severity_chart")
                
                with sev_legend_col:
                    # Calculate percentages
                    total_failures = severity_counts["Count"].sum()
                    high_count = severity_counts[severity_counts['Severity'] == 'HIGH']['Count'].sum() if 'HIGH' in severity_counts['Severity'].values else 0
                    medium_count = severity_counts[severity_counts['Severity'] == 'MEDIUM']['Count'].sum() if 'MEDIUM' in severity_counts['Severity'].values else 0
                    low_count = severity_counts[severity_counts['Severity'] == 'LOW']['Count'].sum() if 'LOW' in severity_counts['Severity'].values else 0
                    none_count = severity_counts[severity_counts['Severity'] == 'NONE']['Count'].sum() if 'NONE' in severity_counts['Severity'].values else 0
                    
                    st.markdown(
                        f"""
                        <div style="display: flex; flex-direction: column; justify-content: center; height: 280px; padding-left: 0.5rem; font-size: 0.85rem;">
                            <div style="margin-bottom: 1rem;">
                                <div style="display: flex; align-items: center; margin-bottom: 0.35rem;">
                                    <div style="width: 16px; height: 16px; background: #dc2626; border-radius: 3px; margin-right: 0.5rem;"></div>
                                    <strong style="color: #dc2626; font-size: 0.92rem;">HIGH</strong>
                                </div>
                                <div style="font-size: 1.3rem; font-weight: 800; color: #0f172a; margin-left: 1.4rem;">{high_count}</div>
                            </div>
                            <div style="margin-bottom: 1rem;">
                                <div style="display: flex; align-items: center; margin-bottom: 0.35rem;">
                                    <div style="width: 16px; height: 16px; background: #f59e0b; border-radius: 3px; margin-right: 0.5rem;"></div>
                                    <strong style="color: #f59e0b; font-size: 0.92rem;">MEDIUM</strong>
                                </div>
                                <div style="font-size: 1.3rem; font-weight: 800; color: #0f172a; margin-left: 1.4rem;">{medium_count}</div>
                            </div>
                            <div style="margin-bottom: 1rem;">
                                <div style="display: flex; align-items: center; margin-bottom: 0.35rem;">
                                    <div style="width: 16px; height: 16px; background: #fbbf24; border-radius: 3px; margin-right: 0.5rem;"></div>
                                    <strong style="color: #d97706; font-size: 0.92rem;">LOW</strong>
                                </div>
                                <div style="font-size: 1.3rem; font-weight: 800; color: #0f172a; margin-left: 1.4rem;">{low_count}</div>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                
                # Show topics for selected severity
                if chart_selection and "selection" in chart_selection and "severity_select" in chart_selection["selection"]:
                    selected_points = chart_selection["selection"]["severity_select"]
                    if selected_points:
                        selected_severity = selected_points[0]["Severity"]
                        
                        # Find topics where DOMINANT severity matches selected severity
                        from logic.aggregations import compute_severity_stats, get_topic_turns
                        
                        matching_topics = []
                        for topic_id in failure_turns["topic_id"].unique():
                            topic_turns = get_topic_turns(failure_turns, topic_id)
                            severity_stats = compute_severity_stats(topic_turns)
                            
                            # Only include topics where dominant severity matches selection
                            if severity_stats["dominant_severity"] == selected_severity:
                                turn_count = len(topic_turns)
                                matching_topics.append((topic_id, turn_count))
                        
                        if matching_topics:
                            # Sort by turn count descending
                            matching_topics = sorted(matching_topics, key=lambda x: x[1], reverse=True)[:5]
                            
                            st.markdown(f"**Topics with {selected_severity} dominant severity:**")
                            for topic_id, count in matching_topics:
                                # Use diagnostics label mapping
                                display_label = diagnostics_labels.get(topic_id, "Unknown Topic")
                                col_topic, col_btn = st.columns([3, 1])
                                with col_topic:
                                    st.markdown(f"• **{display_label}** ({count} turn{'s' if count > 1 else ''})")
                                with col_btn:
                                    if st.button("View", key=f"sev_{selected_severity}_{topic_id}"):
                                        st.session_state.page = "Diagnostics"
                                        st.session_state.selected_topic = topic_id
                                        st.rerun()
                        else:
                            st.info(f"No topics with {selected_severity} as dominant severity.")
            else:
                st.info("No severity data available.")

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

    # ---- Top Failure Topics ----
    st.markdown('<h2 class="page-subheader">Top Failure Topics by Volume</h2>', unsafe_allow_html=True)

    # Keep topic_id so navigation can target the correct details page
    top_topics = topics_df.nlargest(5, "n_examples")[["topic_id", "topic_label", "n_examples", "avg_satisfaction"]].copy()
    top_topics["diag_label"] = top_topics["topic_id"].map(diagnostics_labels)

    cols = st.columns(min(5, len(top_topics)))
    
    for idx, (col, (_, row)) in enumerate(zip(cols, top_topics.iterrows())):
        with col:
            st.markdown(
                f"""
                <div class="topic-card-wrapper">
                    <div class="topic-card">
                        <div class="topic-title"><span class="dot dot-red"></span>{row['diag_label']}</div>
                        <div class="topic-value">{row['avg_satisfaction']:.2f}</div>
                        <div class="topic-sub">Avg Satisfaction</div>
                        <div style="margin-top: 0.5rem; padding-top: 0.5rem; border-top: 1px solid #fecaca;">
                            <div style="font-size: 0.85rem; color: #991b1b; font-weight: 600;">📊 Examples</div>
                            <div style="font-size: 1.2rem; font-weight: 800; color: #0f172a; margin-top: 0.2rem;">{int(row['n_examples'])}</div>
                        </div>
                    </div>
                """,
                unsafe_allow_html=True,
            )
            st.markdown('<div style="margin-top: 0.8rem;">', unsafe_allow_html=True)
            if st.button("🔍 Investigate", key=f"topic_{idx}"):
                    # Navigate to Diagnostics and open this specific topic by id
                    st.session_state.page = "Diagnostics"
                    st.session_state.selected_topic = row['topic_id']
                    st.session_state.topic_rank = diagnostics_ranks.get(row['topic_id'], 0)
                    st.session_state.topic_display_label = row['diag_label']
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
            st.markdown(
                """
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    
    # History tracking section
    if len(st.session_state.metrics_history) > 1:
        st.markdown('<h2 class="page-subheader">📈 Metrics History</h2>', unsafe_allow_html=True)
        
        # Determine which snapshots to display based on view period
        now = datetime.now()
        if history_view == "Past Day":
            cutoff = now - timedelta(days=1)
        elif history_view == "Past Week":
            cutoff = now - timedelta(days=7)
        elif history_view == "Past Month":
            cutoff = now - timedelta(days=30)
        else:  # All History
            cutoff = datetime.min
        
        display_history = [s for s in st.session_state.metrics_history if s["timestamp"] >= cutoff]
        
        # Create history visualization
        history_data = []
        for idx, snapshot in enumerate(display_history):
            abs_idx = len(st.session_state.metrics_history) - len(display_history) + idx
            history_data.append({
                "Snapshot": f"#{abs_idx + 1}",
                "Total Turns": snapshot["total_turns"],
                "Conversations": snapshot["total_convs"],
                "Satisfaction Mean": f"{snapshot['mean_sat']:.2f}",
                "Low Sat Rate (%)": f"{snapshot['low_sat_rate'] * 100:.1f}",
                "Low Sat Turns": snapshot["low_sat_turns"]
            })
        
        history_df = pd.DataFrame(history_data)
        
        # Show table
        col1, col2 = st.columns([1, 1])
        with col1:
            st.markdown("**Recent Snapshots**")
            st.dataframe(history_df, use_container_width=True, hide_index=True)
        
        with col2:
            st.markdown("**Satisfaction Trend**")
            # Prepare trend data with numeric values
            trend_data = []
            for idx, snapshot in enumerate(display_history):
                abs_idx = len(st.session_state.metrics_history) - len(display_history) + idx
                trend_data.append({
                    "Snapshot": f"#{abs_idx + 1}",
                    "Satisfaction Mean": snapshot["mean_sat"]
                })
            trend_df = pd.DataFrame(trend_data)
            
            # Create trend chart
            if len(trend_df) > 0:
                # Auto-scale based on data with padding
                min_val = trend_df["Satisfaction Mean"].min()
                max_val = trend_df["Satisfaction Mean"].max()
                # Add 0.3 padding on both sides for better visualization
                y_min = max(0, min_val - 0.3)
                y_max = min(5, max_val + 0.3)
                
                chart = alt.Chart(trend_df).mark_line(point=True, color="#3b82f6", size=2).encode(
                    x=alt.X("Snapshot:N", title="Timeline", sort=list(range(len(trend_df)))),
                    y=alt.Y("Satisfaction Mean:Q", title="CSAT", scale=alt.Scale(domain=[y_min, y_max])),
                    tooltip=["Snapshot", alt.Tooltip("Satisfaction Mean:Q", format=".2f")]
                ).properties(height=250)
                
                st.altair_chart(chart, use_container_width=True)

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

    # ---- Call to Action ----
    st.markdown(
        """
        <div style="background: linear-gradient(135deg, #dbeafe 0%, #eff6ff 100%); border-left: 4px solid #3b82f6; border-radius: 12px; padding: 1.2rem 1.5rem; margin: 1rem 0;">
            <div style="font-size: 1.1rem; font-weight: 700; color: #1e40af; margin-bottom: 0.3rem;">🔍 Next Step</div>
            <div style="color: #334155; font-size: 1rem; line-height: 1.5;">Click <strong>Diagnostics</strong> to investigate specific failure topics and explore repair suggestions.</div>
        </div>
        """,
        unsafe_allow_html=True
    )
