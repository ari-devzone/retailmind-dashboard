import json
import pandas as pd
from logic.data_loader import load_turns, load_topics

# Load data
turns_df = load_turns()
topics_df = load_topics()

print("=== Topics Summary ===")
print(topics_df[['topic_id', 'topic_label', 'low_satisfaction_rate', 'avg_satisfaction', 'n_examples']].to_string())

print("\n=== USER turns with satisfaction by topic ===")
user_turns = turns_df[(turns_df['speaker'] == 'USER') & (turns_df['satisfaction_score'].notna())]
by_topic = user_turns.groupby('topic_id').agg({
    'low_satisfaction': lambda x: (x.sum() / len(x)),
    'satisfaction_score': ['mean', 'count']
}).reset_index()
by_topic.columns = ['topic_id', 'low_sat_rate', 'mean_sat', 'count']
print(by_topic.sort_values('low_sat_rate').to_string())
