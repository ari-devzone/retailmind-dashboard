import io
import json

import pandas as pd
import streamlit as st
from logic.aggregations import infer_conversation_theme


def _mock_analyze_conversation(raw_text: str) -> dict:
    """Lightweight, non-persistent scoring to make uploads feel real."""
    text = raw_text.lower()
    words = text.split()
    length = len(words)
    positive_hits = sum(k in text for k in ["thank", "great", "helpful", "resolved", "love", "fast"])
    negative_hits = sum(k in text for k in ["angry", "bad", "slow", "issue", "problem", "refund"])

    # Start with a mid score and nudge based on tone/length
    base = 82
    sentiment_delta = (positive_hits * 2.5) - (negative_hits * 2)
    length_delta = min(length / 80, 4)
    satisfaction = max(68, min(98, base + sentiment_delta + length_delta))

    resolution = "Resolved" if satisfaction >= 80 and negative_hits < 3 else "Unresolved"
    effort = "Low" if length < 80 else "Medium"
    theme = infer_conversation_theme(pd.DataFrame({"text": [raw_text], "speaker": ["customer"]}))

    return {
        "satisfaction": round(satisfaction, 1),
        "resolution": resolution,
        "effort": effort,
        "theme": theme,
    }


def _read_uploaded_text(upload) -> str:
    """Best-effort text extraction from csv/json/jsonl/txt uploads."""
    name = upload.name.lower()
    data = upload.read()
    try:
        content = data.decode("utf-8")
    except Exception:
        content = data.decode("latin-1", errors="ignore")

    if name.endswith(".json") or name.endswith(".jsonl"):
        lines = content.strip().splitlines()
        collected = []
        for line in lines:
            try:
                obj = json.loads(line)
                text_val = obj.get("text") or obj.get("message") or json.dumps(obj)
            except Exception:
                text_val = line
            collected.append(str(text_val))
        return "\n".join(collected)

    if name.endswith(".csv"):
        try:
            df = pd.read_csv(io.StringIO(content), nrows=200)
            text_col = None
            for candidate in ["text", "message", "content", "utterance"]:
                if candidate in df.columns:
                    text_col = candidate
                    break
            if text_col:
                return "\n".join(df[text_col].astype(str).tolist())
        except Exception:
            pass
    return content


def render_upload_lab():
    # Page header styling - consistent with other pages
    st.markdown(
        """
        <style>
        /* Page headers */
        .upload-header {
            font-size: 1.9rem;
            font-weight: 900;
            color: #0f172a;
            margin-bottom: 0.55rem;
            letter-spacing: -0.8px;
            border-bottom: 3px solid #8b5cf6;
            padding-bottom: 0.55rem;
            display: inline-block;
        }
        .upload-subtitle {
            color: #475569;
            font-size: 1.12rem;
            margin-top: 0.65rem;
            margin-bottom: 1.15rem;
        }
        .upload-subheader {
            font-size: 1.5rem;
            font-weight: 800;
            color: #1e293b;
            margin: 1.5rem 0 1rem 0;
            letter-spacing: -0.5px;
        }
        .section-divider {
            margin: 2rem 0;
            border: none;
            border-top: 2px solid #e2e8f0;
        }
        /* Input cards */
        .input-card {
            background: linear-gradient(135deg, #faf5ff 0%, #ffffff 100%);
            border: 1.5px solid #ddd6fe;
            border-radius: 12px;
            padding: 1.2rem;
            margin-bottom: 1rem;
        }
        /* Results card */
        .results-card {
            background: linear-gradient(135deg, #f0f9ff 0%, #ffffff 100%);
            border: 1.5px solid #bfdbfe;
            border-radius: 12px;
            padding: 1.2rem;
            margin: 1rem 0;
            box-shadow: 0 4px 12px rgba(59, 130, 246, 0.08);
        }
        .info-box {
            background: #f0f9ff;
            border-left: 4px solid #3b82f6;
            padding: 0.75rem 1rem;
            border-radius: 8px;
            margin: 1rem 0;
            color: #1e293b;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
    
    st.markdown('<h1 class="upload-header">🔬 Upload Lab</h1>', unsafe_allow_html=True)
    st.markdown(
        '<p class="upload-subtitle">Upload conversation data and analyze it in real-time. Results are shown instantly and kept in-memory for this session only.</p>',
        unsafe_allow_html=True
    )

    # Session storage for the last analyzed payload/results
    if "upload_lab_ready" not in st.session_state:
        st.session_state.upload_lab_ready = False
    if "upload_lab_results" not in st.session_state:
        st.session_state.upload_lab_results = None
    if "upload_lab_payload" not in st.session_state:
        st.session_state.upload_lab_payload = None
    if "upload_lab_source" not in st.session_state:
        st.session_state.upload_lab_source = None

    # Input region
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    st.markdown('<h2 class="upload-subheader">Input Methods</h2>', unsafe_allow_html=True)
    
    upload_col, example_col = st.columns([1, 1], gap="large")

    with upload_col:
        st.markdown("**📁 Upload File**")
        upload = st.file_uploader(
            "Choose a file to upload",
            type=["json", "jsonl", "csv", "txt"],
            help="We read text/message/content columns when present. Data is not persisted.",
            label_visibility="collapsed"
        )
        st.caption("💡 **Supported formats:** JSON, JSONL (with text/message fields), CSV (with text/message/content columns), or plain TXT files.")

    with example_col:
        st.markdown("**✍️ Paste Transcript**")
        sample_text = st.text_area(
            "Paste conversation transcript",
            value=(
                "Customer: Hi, I need to reschedule my delivery for tomorrow.\n"
                "Agent: Sure, I can move it to Thursday afternoon. Does that work?\n"
                "Customer: Yes, thanks for making that easy!"
            ),
            height=150,
            label_visibility="collapsed"
        )
        st.caption("💡 **Quick test:** Paste a conversation here for instant analysis without uploading a file.")

    # Analysis section
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    st.markdown('<h2 class="upload-subheader">Analysis Preview</h2>', unsafe_allow_html=True)

    chosen_text = None
    chosen_source = None
    if upload is not None:
        chosen_text = _read_uploaded_text(upload)
        chosen_source = upload.name
    elif sample_text.strip():
        chosen_text = sample_text
        chosen_source = "Pasted text"

    col1, col2, col3 = st.columns([2, 1, 2])
    with col2:
        analyze_clicked = st.button("🔍 Analyze Conversation", type="primary", disabled=not bool(chosen_text), use_container_width=True)

    if analyze_clicked and chosen_text:
        st.session_state.upload_lab_payload = chosen_text
        st.session_state.upload_lab_source = chosen_source
        st.session_state.upload_lab_results = _mock_analyze_conversation(chosen_text)
        st.session_state.upload_lab_ready = True

    if st.session_state.upload_lab_ready and st.session_state.upload_lab_results:
        results = st.session_state.upload_lab_results
        source = st.session_state.upload_lab_source or "Current session"
        
        st.markdown(
            f'<div class="info-box">📊 <strong>Analyzed:</strong> {source}</div>',
            unsafe_allow_html=True
        )

        # Key metrics in card format
        st.markdown("#### Key Metrics")
        card1, card2, card3, card4 = st.columns(4, gap="medium")
        card1.metric("Satisfaction (mock)", f"{results['satisfaction']}%")
        card2.metric("Resolution", results["resolution"])
        card3.metric("Effort", results["effort"])
        card4.metric("Theme", results["theme"])

        st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
        
        # Conversation preview in expandable section
        with st.expander("📄 View Conversation Transcript", expanded=False):
            st.text((st.session_state.upload_lab_payload or "")[:2000])

        # Insights section
        st.markdown("#### Analysis Insights")
        st.markdown(
            """
            <div class="info-box">
            ℹ️ <strong>About this analysis:</strong>
            <ul style="margin: 0.5rem 0 0 0; padding-left: 1.2rem;">
                <li>Satisfaction score derived from conversation tone and length patterns</li>
                <li>Resolution status indicates whether the conversation appears complete</li>
                <li>Effort level reflects the complexity of the customer interaction</li>
                <li>Theme automatically categorized based on conversation content</li>
            </ul>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        # Field meanings in a clean format
        with st.expander("📖 Field Definitions"):
            st.markdown("""
            **Resolution Status**
            - *Resolved*: The conversation appears to have reached a satisfactory conclusion
            - *Unresolved*: Issues remain or the conversation seems incomplete
            
            **Effort Level**
            - *Low*: Simple, straightforward interaction
            - *Medium*: Moderate complexity requiring some back-and-forth
            - *High*: Complex issue requiring extensive discussion
            
            **Theme**
            - Automatically inferred from conversation content and keywords
            - Helps categorize and organize conversations by topic
            """)
        
        st.info("💡 **Note:** Results are illustrative and kept in-memory for this session only. No data is persisted to the database.")
    else:
        st.markdown(
            """
            <div class="info-box">
            👆 <strong>Get Started:</strong> Upload a file or paste conversation text above, then click the "Analyze Conversation" button to see instant results.
            </div>
            """,
            unsafe_allow_html=True
        )
