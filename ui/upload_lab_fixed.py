import io
import json
import random
import re
from datetime import datetime

import pandas as pd
import streamlit as st
from logic.aggregations import infer_conversation_theme


def _clean_topic_label(label: str) -> str:
    """Remove numeric prefixes like 'Topic 4: ' from topic labels."""
    if not label:
        return ""
    return re.sub(r"^Topic\s*\d+\s*[:\-]\s*", "", str(label)).strip()


def _parse_uploaded_conversation(data) -> list:
    """Parse uploaded JSON/JSONL conversation data into turn records."""
    turns = []
    
    if isinstance(data, list):
        # JSON array format
        for item in data:
            if isinstance(item, dict) and "text" in item:
                turns.append(item)
    else:
        # Try JSONL format (one JSON per line)
        lines = data.strip().split('\n') if isinstance(data, str) else [data]
        for line in lines:
            try:
                item = json.loads(line) if isinstance(line, str) else line
                if isinstance(item, dict) and "text" in item:
                    turns.append(item)
            except:
                continue
    
    return turns


def _add_conversation_to_data(turns: list):
    """Add uploaded conversation turns to the session state dataframes."""
    if not turns or "turns_df" not in st.session_state:
        return False
    
    # Get the next conversation ID
    current_max_conv_id = st.session_state.turns_df["conv_id"].max()
    new_conv_id = int(current_max_conv_id) + 1
    
    # Convert uploaded turns to proper format
    new_records = []
    for idx, turn in enumerate(turns, 1):
        # Calculate satisfaction score based on sentiment
        text = turn.get("text", "")
        satisfaction_score = turn.get("satisfaction_score", None)
        
        # If no satisfaction score provided, calculate it
        if satisfaction_score is None:
            text_lower = text.lower()
            positive_words = ["thank", "great", "helpful", "resolved", "love", "fast", "excellent", "perfect", "good"]
            negative_words = ["angry", "bad", "slow", "issue", "problem", "refund", "disappointed", "terrible"]
            
            positive_count = sum(1 for word in positive_words if word in text_lower)
            negative_count = sum(1 for word in negative_words if word in text_lower)
            
            base_score = 3.5
            satisfaction_score = base_score + (positive_count * 0.3) - (negative_count * 0.4)
            satisfaction_score = max(1.0, min(5.0, satisfaction_score))
        
        # Determine if low satisfaction
        low_satisfaction = satisfaction_score < 3.5 if satisfaction_score else False
        
        # Create turn record matching existing format
        record = {
            "dataset": "UPLOAD",
            "conv_id": new_conv_id,
            "turn_id": idx,
            "speaker": turn.get("speaker", "USER"),
            "text": text,
            "satisfaction_score": satisfaction_score,
            "low_satisfaction": low_satisfaction,
            "issues": turn.get("issues", []),
            "severity": turn.get("severity", "NONE"),
            "reason": turn.get("reason", ""),
            "topic_id": turn.get("topic_id", -1),
            "topic_label": _clean_topic_label(turn.get("topic_label", "UNCLUSTERED")),
            "satisfaction_source": "upload"
        }
        new_records.append(record)
    
    # Append to existing dataframe
    new_df = pd.DataFrame(new_records)
    st.session_state.turns_df = pd.concat([st.session_state.turns_df, new_df], ignore_index=True)
    
    return True


def _analyze_uploaded_conversation(turns: list) -> dict:
    """Analyze uploaded conversation and return metrics."""
    if not turns:
        return None
    
    total_turns = len(turns)
    
    # Calculate average satisfaction
    satisfaction_scores = []
    for turn in turns:
        score = turn.get("satisfaction_score")
        if score is not None:
            satisfaction_scores.append(float(score))
    
    avg_satisfaction = sum(satisfaction_scores) / len(satisfaction_scores) if satisfaction_scores else 3.5
    
    # Determine resolution status
    low_sat_count = sum(1 for turn in turns if turn.get("low_satisfaction", False))
    resolution = "Resolved" if avg_satisfaction >= 3.5 and low_sat_count <= 1 else "Unresolved"
    
    # Determine effort level
    if total_turns <= 6:
        effort = "Low"
    elif total_turns <= 12:
        effort = "Medium"
    else:
        effort = "High"
    
    # Extract theme from most common topic (cleaned) or infer from text
    topics = [
        _clean_topic_label(turn.get("topic_label", "UNCLUSTERED"))
        for turn in turns
        if turn.get("topic_label") and turn.get("topic_label") != "UNCLUSTERED"
    ]
    topics = [t for t in topics if t]
    if topics:
        theme = max(set(topics), key=topics.count)
    else:
        # Infer from conversation text
        all_text = " ".join([turn.get("text", "") for turn in turns])
        theme = infer_conversation_theme(pd.DataFrame({"text": [all_text], "speaker": ["customer"]}))
    
    return {
        "satisfaction": round(avg_satisfaction * 20, 1),  # Scale to 0-100
        "resolution": resolution,
        "effort": effort,
        "theme": theme,
        "turn_count": total_turns,
        "low_satisfaction_turns": low_sat_count
    }


def _read_uploaded_text(upload) -> str:
    """Best-effort text extraction from csv/json/jsonl/txt uploads."""
    name = upload.name.lower()
    data = upload.read()
    try:
        content = data.decode("utf-8")
    except Exception:
        content = data.decode("latin-1", errors="ignore")

    return content


def render_upload_lab():
    # Page header styling - consistent with other pages
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
            border-bottom: 3px solid #8b5cf6;
            padding-bottom: 0.5rem;
            display: inline-block;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        }
        .info-box {
            background: #f0f9ff;
            border-left: 4px solid #3b82f6;
            padding: 0.85rem 1.2rem;
            border-radius: 8px;
            margin: 1rem 0;
            color: #1e293b;
            line-height: 1.6;
        }
        .success-box {
            background: #f0fdf4;
            border-left: 4px solid #22c55e;
            padding: 0.85rem 1.2rem;
            border-radius: 8px;
            margin: 1rem 0;
            color: #1e293b;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
    
    st.markdown('<h1 class="page-header">🚀 Upload Lab</h1>', unsafe_allow_html=True)

    if "upload_lab_ready" not in st.session_state:
        st.session_state.upload_lab_ready = False
    if "upload_lab_results" not in st.session_state:
        st.session_state.upload_lab_results = None
    if "upload_lab_payload" not in st.session_state:
        st.session_state.upload_lab_payload = None
    if "upload_lab_source" not in st.session_state:
        st.session_state.upload_lab_source = None
    if "upload_history" not in st.session_state:
        st.session_state.upload_history = []
    
    # Display upload history if exists
    if st.session_state.upload_history:
        st.markdown("### 📚 Upload History")
        
        with st.expander(f"📋 View all uploads ({len(st.session_state.upload_history)} total)", expanded=False):
            # Create history dataframe
            history_df = pd.DataFrame([
                {
                    "Filename": record["filename"],
                    "Upload Time": record["timestamp"].strftime("%Y-%m-%d %H:%M"),
                    "Turns": record["turn_count"],
                    "CSAT": f"{record['satisfaction']:.1f}",
                    "Resolution": record["resolution"],
                    "Theme": record["theme"],
                    "Low Sat": record["low_sat_turns"]
                }
                for record in reversed(st.session_state.upload_history)  # Most recent first
            ])
            
            st.dataframe(history_df, use_container_width=True, hide_index=True)
            
            st.markdown("---")
            
            # Summary stats in clean layout
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Uploads", len(st.session_state.upload_history))
            with col2:
                total_turns = sum(r["turn_count"] for r in st.session_state.upload_history)
                st.metric("Total Turns", total_turns)
            with col3:
                avg_sat = sum(r["satisfaction"] for r in st.session_state.upload_history) / len(st.session_state.upload_history)
                st.metric("Avg CSAT", f"{avg_sat:.1f}")
            with col4:
                resolved_count = sum(1 for r in st.session_state.upload_history if r["resolution"] == "Resolved")
                st.metric("Resolved", f"{resolved_count}/{len(st.session_state.upload_history)}")

    # Input region
    st.markdown("### 📁 Upload Conversation")
    
    with st.container(border=True):
        upload = st.file_uploader(
            "Choose a JSON or JSONL file",
            type=["json", "jsonl"],
            help="Upload a conversation in JSON or JSONL format.",
            label_visibility="visible"
        )
        if not upload:
            st.caption("💡 **Supported formats:** JSON array or JSONL (one JSON object per line)")

    # Analysis section
    st.divider()
    st.markdown("### 🔍 Analysis & Integration")

    chosen_data = None
    chosen_source = None
    
    if upload is not None:
        raw_content = _read_uploaded_text(upload)
        chosen_source = upload.name
        try:
            # Try to parse as JSON
            chosen_data = json.loads(raw_content)
        except:
            try:
                # Try JSONL format
                lines = raw_content.strip().split('\n')
                chosen_data = [json.loads(line) for line in lines if line.strip()]
            except:
                st.error("⚠️ Unable to parse file. Please upload valid JSON or JSONL format.")
                chosen_data = None
    
    col1, col2, col3 = st.columns([2, 1, 2])
    with col2:
        analyze_clicked = st.button(
            "🔍 Analyze & Add to Dashboard", 
            type="primary", 
            disabled=not bool(chosen_data), 
            use_container_width=True
        )

    if analyze_clicked and chosen_data:
        # Parse conversation turns
        turns = _parse_uploaded_conversation(chosen_data)
        
        if turns:
            # Analyze the conversation
            results = _analyze_uploaded_conversation(turns)
            
            # Add to session state dataframes
            success = _add_conversation_to_data(turns)
            
            if success and results:
                st.session_state.upload_lab_results = results
                st.session_state.upload_lab_source = chosen_source
                st.session_state.upload_lab_turns = turns
                st.session_state.upload_lab_ready = True
                
                # Add to upload history
                upload_record = {
                    "timestamp": datetime.now(),
                    "filename": chosen_source,
                    "turn_count": results["turn_count"],
                    "satisfaction": results["satisfaction"],
                    "resolution": results["resolution"],
                    "theme": results["theme"],
                    "low_sat_turns": results["low_satisfaction_turns"]
                }
                st.session_state.upload_history.append(upload_record)
                
                st.success(f"✅ Successfully added conversation to dashboard! The Overview page now reflects this data.")
            else:
                st.error("⚠️ Failed to add conversation. Please check the format.")
        else:
            st.error("⚠️ No valid conversation turns found in the uploaded data.")

    if st.session_state.upload_lab_ready and st.session_state.upload_lab_results:
        results = st.session_state.upload_lab_results
        source = st.session_state.upload_lab_source or "Current session"
        turns = st.session_state.get("upload_lab_turns", [])
        
        # Success message
        st.markdown(
            f"""
            <div style="
                background: #f0f9ff;
                border-left: 4px solid #3b82f6;
                padding: 0.85rem 1.2rem;
                border-radius: 8px;
                margin: 1rem 0;
                color: #1e293b;
            ">
            ✅ <strong>Analysis Complete:</strong> {source}
            </div>
            """,
            unsafe_allow_html=True
        )

        # Key metrics section
        st.markdown("### 📊 Conversation Metrics")
        
        # Metrics in a professional card using container
        with st.container(border=True):
            # First row - 4 metrics
            col1, col2, col3, col4 = st.columns(4, gap="large")
            with col1:
                st.metric("Satisfaction Score", f"{results['satisfaction']}%")
            with col2:
                # Color-coded resolution status
                resolution_color = "#22c55e" if results["resolution"] == "Resolved" else "#ef4444"
                st.markdown(
                    f"""
                    <div style="text-align: center;">
                        <div style="color: #64748b; font-size: 0.875rem; margin-bottom: 0.25rem;">Resolution</div>
                        <div style="color: {resolution_color}; font-weight: 700; font-size: 1.5rem;">
                            {results["resolution"]}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            with col3:
                st.metric("Effort Level", results["effort"])
            with col4:
                st.metric("Total Turns", results["turn_count"])
            
            # Add spacing
            st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)
            
            # Second row - 2 metrics
            col5, col6 = st.columns(2, gap="large")
            with col5:
                st.metric("Low Sat Turns", results["low_satisfaction_turns"])
            with col6:
                st.metric("Theme", results["theme"])

        st.divider()
        
        # View conversation
        st.markdown("### 💬 Conversation Transcript")
        
        with st.container(border=True):
            st.markdown(f"**Conversation — {source}**")
            
            for idx, turn in enumerate(turns):
                speaker = turn.get("speaker", "USER")
                text = turn.get("text", "")
                satisfaction = turn.get("satisfaction_score")
                
                # Display turn with formatting
                if speaker == "USER":
                    st.markdown(f"🧑 **User:** {text}")
                else:
                    st.markdown(f"🤖 **Assistant:** {text}")
                
                # Show satisfaction score if available
                if satisfaction is not None:
                    st.caption(f"Satisfaction: {satisfaction:.1f}/5.0")

        st.divider()
        
        # Impact and actions section
        st.markdown("### ✅ Next Steps")
        
        st.markdown(
            """
            <div class="info-box">
            <strong>Data Integration Complete</strong>
            <ul style="margin: 0.5rem 0 0 0; padding-left: 1.5rem; line-height: 1.8;">
                <li>Conversation has been added to the main dataset</li>
                <li>Overview page metrics now include this conversation</li>
                <li>All aggregations and statistics have been updated</li>
            </ul>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        # Action buttons in clean layout
        col1, col2, col3 = st.columns([1.2, 1.2, 1.6])
        with col1:
            if st.button("📊 View Updated Stats", key="view_stats_btn", use_container_width=True, type="primary"):
                st.session_state.page = "Overview"
                st.rerun()
        with col2:
            if st.button("📋 Upload Another", key="upload_another_btn", use_container_width=True):
                st.session_state.upload_lab_file = None
                st.session_state.upload_lab_results = None
                st.session_state.upload_lab_ready = False
                st.rerun()
        
        st.divider()
# Reference section
        with st.expander("📖 Metric Definitions", expanded=False):
            col_left, col_right = st.columns(2)
            
            with col_left:
                st.markdown("""
                **Satisfaction Score**  
                Calculated from sentiment analysis and explicit satisfaction ratings, scaled to 0-100 for easy interpretation.
                
                **Resolution Status**  
                - *Resolved*: Avg satisfaction ≥ 3.5/5 with minimal issues
                - *Unresolved*: Multiple low satisfaction turns or unresolved concerns
                """)
            
            with col_right:
                st.markdown("""
                **Effort Level**  
                - *Low*: 1-6 turns (simple interaction)
                - *Medium*: 7-12 turns (moderate complexity)
                - *High*: 13+ turns (complex conversation)
                
                **Theme**  
                Automatically categorized based on conversation content and topic labels.
                """)
    else:
        st.markdown(
            """
            <div class="info-box">
            <strong>👋 Welcome to Upload Lab</strong><br><br>
            Upload a conversation file (JSON or JSONL format), then click <strong>"Analyze & Add to Dashboard"</strong> to integrate it with your data and see real-time impact on your KPIs.
            </div>
            """,
            unsafe_allow_html=True
        )
