import json
import pandas as pd
import streamlit as st

DATA_DIR = "data"

@st.cache_data
def load_turns():
    records = []
    with open(f"{DATA_DIR}/dashboard_turns.jsonl", "r", encoding="utf-8") as f:
        for line in f:
            records.append(json.loads(line))
    return pd.DataFrame(records)

@st.cache_data
def load_topics():
    with open(f"{DATA_DIR}/dashboard_topics.json", "r", encoding="utf-8") as f:
        return pd.DataFrame(json.load(f))

@st.cache_data
def load_repairs():
    with open(f"{DATA_DIR}/dashboard_repairs.json", "r", encoding="utf-8") as f:
        return pd.DataFrame(json.load(f))

@st.cache_data
def load_sandbox_cases():
    try:
        with open(f"{DATA_DIR}/dashboard_sandbox_cases.json", "r", encoding="utf-8") as f:
            return pd.DataFrame(json.load(f))
    except FileNotFoundError:
        return pd.DataFrame()
