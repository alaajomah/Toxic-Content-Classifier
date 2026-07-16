"""
CSV-backed storage for user inputs (text or image captions) and their
classification results. Acts as the shared "database" for the
Streamlit app

"""

import os
from datetime import datetime
import pandas as pd

CSV_PATH = "data/classifications.csv"


def init_db():
    if not os.path.exists("data"):
        os.makedirs("data")

    if not os.path.exists(CSV_PATH):
        df = pd.DataFrame(columns=[
            "timestamp",
            "input_type",
            "content",
            "classification",
            "category"
        ])
        df.to_csv(CSV_PATH, index=False)


def save_entry(input_type, content, classification, category=""):
    init_db()

    df = pd.read_csv(CSV_PATH)

    new_row = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "input_type": input_type,
        "content": content,
        "classification": classification,
        "category": category
    }

    df.loc[len(df)] = new_row
    df.to_csv(CSV_PATH, index=False)

    return new_row


def load_db():
    init_db()
    return pd.read_csv(CSV_PATH)