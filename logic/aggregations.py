def rank_topics(df_topics):
    return df_topics.sort_values(
        by=["low_satisfaction_rate", "n_examples"],
        ascending=[False, False]
    )

def get_topic_turns(df_turns, topic_id):
    return df_turns[df_turns["topic_id"] == topic_id]

def group_conversations(df_turns):
    return df_turns.groupby("conv_id")
import pandas as pd

# ---- Severity mapping (EXPLAINED BELOW) ----
SEVERITY_MAP = {
    "LOW": 1,
    "MEDIUM": 2,
    "HIGH": 3
}

def compute_severity_stats(turns_df: pd.DataFrame):
    df = turns_df.copy()
    # Consider only valid severity labels and drop missing values
    valid = df[df["severity"].isin(SEVERITY_MAP.keys())].copy()
    valid["severity_score"] = valid["severity"].map(SEVERITY_MAP)

    avg = None
    dom = None
    counts = {}

    if not valid.empty:
        avg = round(valid["severity_score"].mean(), 2)
        counts = valid["severity"].value_counts().to_dict()
        dom = valid["severity"].value_counts().idxmax()
    else:
        # Fallback: if only "NONE" or missing severities exist, set a friendly default
        non_missing = df["severity"].dropna()
        if not non_missing.empty and (non_missing == "NONE").any():
            dom = "NONE"
            counts = non_missing.value_counts().to_dict()
        else:
            dom = "N/A"
            counts = {}

    return {
        "avg_severity": avg,
        "severity_counts": counts,
        "dominant_severity": dom
    }


def get_success_topics(turns_df: pd.DataFrame, top_n=5):
    # Successful patterns are reflected in USER turns with a valid satisfaction score
    success_turns = turns_df[
        (turns_df["speaker"] == "USER") &
        (turns_df["low_satisfaction"] == False) &
        (turns_df["satisfaction_score"].notna())
    ]

    if success_turns.empty:
        return pd.DataFrame()

    return (
        success_turns
        .groupby("topic_id")
        .agg(
            mean_satisfaction=("satisfaction_score", "mean"),
            successful_turns=("satisfaction_score", "count")
        )
        .reset_index()
        .sort_values("mean_satisfaction", ascending=False)
        .head(top_n)
    )


def get_top_success_topics_detailed(turns_df: pd.DataFrame, topics_df: pd.DataFrame, top_n=5):
    """
    Get top successful topics with satisfaction metrics and low-satisfaction rates.
    Success is determined by lowest low_satisfaction_rate and highest mean_satisfaction.
    
    Returns DataFrame with:
    - topic_id
    - topic_label
    - mean_satisfaction
    - successful_turns
    - low_satisfaction_rate (% of turns marked as low-satisfaction)
    - n_examples
    """
    # Get all turns with valid satisfaction scores
    user_turns = turns_df[
        (turns_df["speaker"] == "USER") &
        (turns_df["satisfaction_score"].notna())
    ]

    if user_turns.empty:
        return pd.DataFrame()

    # Aggregate by topic
    by_topic = (
        user_turns
        .groupby("topic_id")
        .agg(
            mean_satisfaction=("satisfaction_score", "mean"),
            successful_turns=("satisfaction_score", "count"),
            low_sat_count=("low_satisfaction", "sum")
        )
        .reset_index()
    )

    # Calculate low satisfaction rate
    by_topic["low_satisfaction_rate"] = (
        by_topic["low_sat_count"] / by_topic["successful_turns"]
    )

    # Merge with topic labels and examples count
    result = by_topic.merge(
        topics_df[["topic_id", "topic_label", "n_examples"]],
        on="topic_id",
        how="left"
    )

    # Sort by low satisfaction rate (ascending = best first) and then by mean satisfaction (descending)
    result = result.sort_values(
        by=["low_satisfaction_rate", "mean_satisfaction"],
        ascending=[True, False]
    ).head(top_n)

    return result


def get_successful_conversations(turns_df: pd.DataFrame, topic_id: int, limit: int = 5):
    """
    Get example successful conversations for a given topic.
    Returns conversations with the highest satisfaction scores.
    
    Returns list of conversation dictionaries with their success metrics.
    """
    topic_turns = turns_df[turns_df["topic_id"] == topic_id].copy()
    
    if topic_turns.empty:
        return []

    # Group by conversation and get satisfaction metrics
    conv_data = []
    for conv_id, conv_group in topic_turns.groupby("conv_id"):
        # Get satisfaction info
        user_turns = conv_group[conv_group["speaker"] == "USER"]
        if len(user_turns) == 0:
            continue
            
        sat_scores = user_turns["satisfaction_score"].dropna()
        if len(sat_scores) == 0:
            continue
        
        conv_data.append({
            "conv_id": conv_id,
            "min_satisfaction": sat_scores.min(),
            "max_satisfaction": sat_scores.max(),
            "mean_satisfaction": sat_scores.mean(),
            "turn_count": conv_group["turn_id"].max(),
            "system_turns": (conv_group["speaker"] == "SYSTEM").sum(),
            "user_turns": len(user_turns),
            "low_sat_count": user_turns["low_satisfaction"].sum()
        })

    if not conv_data:
        return []

    # Convert to DataFrame for sorting
    conv_df = pd.DataFrame(conv_data)
    
    # Sort by mean satisfaction (descending), then by low satisfaction count (ascending)
    conv_df = conv_df.sort_values(
        by=["mean_satisfaction", "low_sat_count"],
        ascending=[False, True]
    ).head(limit)

    return conv_df.to_dict("records")


def get_success_insights_for_topic(turns_df: pd.DataFrame, topic_id: int) -> dict:
    """
    Generate "Why it worked" insights for a successful topic.
    Analyzes characteristics of conversations in this topic.
    
    Returns dict with:
    - clear_intent: % of turns without issues (indicating clear intent)
    - concise: avg turns per conversation
    - kb_coverage: % of turns without UNSUPPORTED_INTENT issues
    - dominant_issues: most common issues in this topic (even if rare)
    """
    topic_turns = turns_df[turns_df["topic_id"] == topic_id].copy()

    if topic_turns.empty:
        return {
            "clear_intent": "N/A",
            "concise": "N/A",
            "kb_coverage": "N/A",
            "dominant_issues": {}
        }

    # Check for issues
    has_issues = topic_turns["issues"].apply(
        lambda x: len(x) > 0 if isinstance(x, list) else False
    )
    clear_intent_pct = (1 - has_issues.sum() / len(topic_turns)) * 100

    # Conciseness: avg turns per conversation
    conv_turn_counts = topic_turns.groupby("conv_id")["turn_id"].max()
    avg_turns = conv_turn_counts.mean()

    # KB coverage: % without UNSUPPORTED_INTENT
    def has_unsupported(issues):
        if isinstance(issues, list):
            return "UNSUPPORTED_INTENT" in issues
        return False

    unsupported_pct = topic_turns["issues"].apply(has_unsupported).sum() / len(topic_turns)
    kb_coverage = (1 - unsupported_pct) * 100

    # Most common issues
    all_issues = []
    for issues_list in topic_turns["issues"]:
        if isinstance(issues_list, list):
            all_issues.extend(issues_list)

    issue_counts = pd.Series(all_issues).value_counts().head(3).to_dict() if all_issues else {}

    return {
        "clear_intent": f"{clear_intent_pct:.0f}%",
        "concise": f"{avg_turns:.1f} turns",
        "kb_coverage": f"{kb_coverage:.0f}%",
        "dominant_issues": issue_counts
    }


def get_top_conversations(turns_df: pd.DataFrame, limit: int = 50):
    """
    Get top conversations ranked by satisfaction score.
    
    Ranking logic:
    1. Sort by mean satisfaction (descending)
    2. Tie-breaker: successful turns (descending) / low-sat count (ascending)
    3. Filter out empty conversations
    
    Returns list of conversation dicts with metadata and assigned topic.
    """
    # Group by conversation and aggregate
    conv_data = []
    for conv_id, conv_group in turns_df.groupby("conv_id"):
        user_turns = conv_group[conv_group["speaker"] == "USER"]
        if len(user_turns) == 0:
            continue
        
        sat_scores = user_turns["satisfaction_score"].dropna()
        if len(sat_scores) == 0:
            continue
        
        # Get the most common topic for this conversation (avoid NaN)
        topics = conv_group["topic_id"].dropna().unique()
        if len(topics) > 0:
            # Get the most common topic
            topic_counts = conv_group["topic_id"].value_counts()
            assigned_topic = topic_counts.idxmax() if not topic_counts.empty else -1
        else:
            assigned_topic = -1
        
        # Get topic label
        topic_label = None
        if assigned_topic >= 0:
            topic_label_series = conv_group[conv_group["topic_id"] == assigned_topic]["topic_label"].unique()
            if len(topic_label_series) > 0:
                topic_label = topic_label_series[0]

        # Fallback: infer a human-friendly conversation theme from content
        if not topic_label or pd.isna(topic_label):
            topic_label = infer_conversation_theme(conv_group)
            assigned_topic = -1
        
        conv_data.append({
            "conv_id": conv_id,
            "mean_satisfaction": sat_scores.mean(),
            "min_satisfaction": sat_scores.min(),
            "max_satisfaction": sat_scores.max(),
            "turn_count": int(conv_group["turn_id"].max()),
            "user_turns": len(user_turns),
            "system_turns": (conv_group["speaker"] == "SYSTEM").sum(),
            "low_sat_count": int(user_turns["low_satisfaction"].sum()),
            "success_rate": 1.0 - (user_turns["low_satisfaction"].sum() / len(user_turns)),
            "topic_id": assigned_topic,
            "topic_label": topic_label
        })
    
    if not conv_data:
        return []
    
    # Convert to DataFrame
    conv_df = pd.DataFrame(conv_data)
    
    # Sort by satisfaction, then by success metrics
    conv_df = conv_df.sort_values(
        by=["mean_satisfaction", "user_turns", "low_sat_count"],
        ascending=[False, False, True]
    ).head(limit)
    
    return conv_df.to_dict("records")


def get_top_performing_topics_from_conversations(conv_list: list, limit: int = 5) -> pd.DataFrame:
    """
    Build "Top Performing Topics" from a list of conversations.
    
    Groups by topic and computes:
    - # conversations
    - Avg satisfaction
    - Success rate
    - Avg/median turns
    
    Returns sorted DataFrame.
    """
    if not conv_list:
        return pd.DataFrame()
    
    conv_df = pd.DataFrame(conv_list)
    
    # Group by topic
    topic_stats = (
        conv_df
        .groupby("topic_label")
        .agg(
            num_conversations=("conv_id", "count"),
            avg_satisfaction=("mean_satisfaction", "mean"),
            success_rate=("success_rate", "mean"),
            median_turns=("turn_count", "median"),
            avg_turns=("turn_count", "mean")
        )
        .reset_index()
    )
    
    # Sort by success rate (descending), then by avg satisfaction
    topic_stats = topic_stats.sort_values(
        by=["success_rate", "avg_satisfaction"],
        ascending=[False, False]
    ).head(limit)
    
    return topic_stats


def get_why_it_works_patterns(conv_list: list, turns_df: pd.DataFrame) -> dict:
    """
    Extract "Why it works" patterns from top conversations using existing signals.
    
    Analyzes:
    - Clear intent: % of conversations with no issues
    - Constraints/KB alignment: % without UNSUPPORTED_INTENT
    - Conciseness: avg turns in successful conversations
    - Low error rate: % with minimal low-sat turns
    
    Returns dict with pattern descriptions suitable for bullet points.
    """
    if not conv_list or len(conv_list) == 0:
        return {
            "patterns": [],
            "metrics": {}
        }
    
    conv_ids = [c["conv_id"] for c in conv_list]
    top_conv_turns = turns_df[turns_df["conv_id"].isin(conv_ids)].copy()
    
    # Pattern 1: Clear Intent (no issues)
    has_issues = top_conv_turns["issues"].apply(
        lambda x: len(x) > 0 if isinstance(x, list) else False
    )
    clear_intent_pct = (1 - has_issues.sum() / len(top_conv_turns)) * 100 if len(top_conv_turns) > 0 else 0
    
    # Pattern 2: Knowledge Base Alignment (no UNSUPPORTED_INTENT)
    def has_unsupported(issues):
        if isinstance(issues, list):
            return "UNSUPPORTED_INTENT" in issues
        return False
    
    unsupported_count = top_conv_turns["issues"].apply(has_unsupported).sum()
    kb_alignment = (1 - unsupported_count / len(top_conv_turns)) * 100 if len(top_conv_turns) > 0 else 0
    
    # Pattern 3: Conciseness
    avg_turns = sum([c["turn_count"] for c in conv_list]) / len(conv_list) if conv_list else 0
    
    # Pattern 4: Low Error Rate
    total_low_sat = sum([c["low_sat_count"] for c in conv_list])
    avg_low_sat_per_conv = total_low_sat / len(conv_list) if conv_list else 0
    low_error_rate = 1.0 - (avg_low_sat_per_conv / avg_turns) if avg_turns > 0 else 0.95
    
    # Pattern 5: Most common positive signals (absence of issues)
    all_issues = []
    for issues_list in top_conv_turns["issues"]:
        if isinstance(issues_list, list):
            all_issues.extend(issues_list)
    
    issue_counts = pd.Series(all_issues).value_counts().head(5).to_dict() if all_issues else {}
    
    # Build human-readable patterns
    patterns = []
    
    if clear_intent_pct >= 70:
        patterns.append({
            "title": "Clear Intent & Specificity",
            "description": f"Users state goals and expected outcomes clearly ({clear_intent_pct:.0f}% of turns free of ambiguity), reducing clarification rounds.",
            "metric": f"{clear_intent_pct:.0f}%"
        })
    
    if kb_alignment >= 80:
        patterns.append({
            "title": "Strong Knowledge Base Alignment",
            "description": f"Requests align well with system knowledge ({kb_alignment:.0f}% coverage), leading to faster, more accurate responses.",
            "metric": f"{kb_alignment:.0f}%"
        })
    
    if avg_turns <= 15:
        patterns.append({
            "title": "Efficient Conversation Flow",
            "description": f"Conversations are concise (avg {avg_turns:.1f} turns), indicating well-structured exchanges with minimal back-and-forth.",
            "metric": f"{avg_turns:.1f} turns"
        })
    
    if low_error_rate >= 0.85:
        patterns.append({
            "title": "High Success Rate",
            "description": f"Very few satisfaction issues ({(1-low_error_rate)*100:.0f}% avg low-sat turns per conversation), indicating user needs are met efficiently.",
            "metric": f"{(1-low_error_rate)*100:.0f}% issues"
        })
    
    # Always add this if KB has good coverage
    if len(issue_counts) < 3:  # Few issue types = well-covered domain
        patterns.append({
            "title": "Well-Scoped Domain",
            "description": "Interactions are focused on topics the system handles well, with minimal edge cases or ambiguities.",
            "metric": f"{len(issue_counts)} issue types"
        })
    else:
        patterns.append({
            "title": "Detailed Context & Constraints",
            "description": "Users provide sufficient context (examples, data, format preferences) upfront, enabling accurate, complete responses.",
            "metric": "Context-rich"
        })
    
    return {
        "patterns": patterns[:5],  # Top 5 patterns
        "metrics": {
            "clear_intent_pct": clear_intent_pct,
            "kb_alignment": kb_alignment,
            "avg_turns": avg_turns,
            "low_error_rate": low_error_rate
        }
    }


def infer_conversation_theme(conv_group: pd.DataFrame) -> str:
    """
    Infer a human-friendly conversation theme from the conversation text.
    Uses lightweight keyword heuristics so it works offline and fast.
    """
    text_blob = " ".join(conv_group["text"].astype(str)).lower()

    # Keyword buckets for quick domain inference
    buckets = [
        ("Movie Recommendations & Reviews", ["movie", "film", "show", "cinema", "actor", "actress", "review", "tickets", "avengers", "disney", "x-men", "marvel", "netflix"]),
        ("Event & Ticket Booking", ["ticket", "event", "concert", "festival", "venue", "seats", "book", "reserve", "reservation", "showtime", "perform", "tour"]),
        ("Travel & Flight Planning", ["flight", "plane", "airport", "departure", "arrival", "round trip", "one way", "london", "philly", "philadelphia", "hotel", "check-in", "booking"]),
        ("Food & Dining / Reservations", ["restaurant", "table", "dining", "reservation", "book a table", "cuisine", "menu", "waiter", "booking" ]),
        ("Commerce & Orders", ["order", "refund", "purchase", "buy", "price", "cart", "delivery", "shipping", "return", "payment"]),
        ("Support & Account Help", ["account", "login", "password", "support", "help", "issue", "problem", "troubleshoot", "reset"]),
    ]

    for label, keywords in buckets:
        if any(k in text_blob for k in keywords):
            return label

    # Fallback by turn count flavor
    turns = conv_group["turn_id"].max()
    if pd.notna(turns):
        if turns <= 8:
            return "Quick Q&A"
        if turns <= 15:
            return "Standard Assistance"
        return "Complex Multi-Turn Help"

    return "General Conversation"
