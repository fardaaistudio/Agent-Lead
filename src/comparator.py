"""Comparator to load existing CSV and filter new leads.

Uses RapidFuzz token-sort ratio to avoid duplicates even with small name/address
variations. Exposes `filter_new_leads(leads, existing_path)` which returns a
DataFrame of leads not present in the existing CSV.
"""
import re
import pandas as pd
from rapidfuzz import fuzz


def normalize(s: str) -> str:
    if pd.isna(s):
        return ''
    s = str(s).lower()
    s = re.sub(r'[^a-z0-9\u0600-\u06FF\s]', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s


def load_existing(path: str) -> pd.DataFrame:
    return pd.read_csv(path, dtype=str)


def is_duplicate(lead: dict, existing_df: pd.DataFrame, threshold: int = 85) -> bool:
    ln = normalize(lead.get('name', '')) + ' ' + normalize(lead.get('address', ''))
    for _, row in existing_df.iterrows():
        en = normalize(row.get('name', '')) + ' ' + normalize(row.get('address', ''))
        score = fuzz.token_sort_ratio(ln, en)
        if score >= threshold:
            return True
    return False


def filter_new_leads(leads: list, existing_path: str, threshold: int = 85) -> pd.DataFrame:
    existing = load_existing(existing_path)
    new = []
    for l in leads:
        if not is_duplicate(l, existing, threshold=threshold):
            new.append(l)
    return pd.DataFrame(new)
