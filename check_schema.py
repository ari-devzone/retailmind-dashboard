import json
import pandas as pd

# Check topics schema
with open('data/dashboard_topics.json') as f:
    topics = json.load(f)
    print("=== TOPICS SCHEMA ===")
    print(json.dumps(topics[0] if topics else {}, indent=2))
    print(f"\nTotal topics: {len(topics)}")
    print(f"Columns: {list(topics[0].keys()) if topics else []}")
    print("\n")

# Check turns schema  
with open('data/dashboard_turns.jsonl') as f:
    line = f.readline()
    turn = json.loads(line)
    print("=== TURNS SCHEMA ===")
    print(json.dumps(turn, indent=2))
    print(f"\nColumns: {list(turn.keys())}")
