import json
import pandas as pd
from logic.data_loader import load_turns, load_topics
from logic.aggregations import get_top_success_topics_detailed, get_successful_conversations, get_success_insights_for_topic

# Load data
turns_df = load_turns()
topics_df = load_topics()

print("=== Testing get_top_success_topics_detailed ===")
success_topics = get_top_success_topics_detailed(turns_df, topics_df, top_n=5)
print(success_topics[['topic_id', 'topic_label', 'mean_satisfaction', 'low_satisfaction_rate', 'successful_turns']])

print("\n=== Testing get_successful_conversations ===")
if not success_topics.empty:
    topic_id = int(success_topics.iloc[0]['topic_id'])
    examples = get_successful_conversations(turns_df, topic_id, limit=3)
    print(f"Topic {topic_id} - {len(examples)} examples:")
    for ex in examples:
        print(f"  Conv {ex['conv_id']}: satisfaction={ex['mean_satisfaction']:.2f}, turns={ex['turn_count']}")

print("\n=== Testing get_success_insights_for_topic ===")
if not success_topics.empty:
    topic_id = int(success_topics.iloc[0]['topic_id'])
    insights = get_success_insights_for_topic(turns_df, topic_id)
    print(f"Topic {topic_id} insights:")
    for key, value in insights.items():
        print(f"  {key}: {value}")
