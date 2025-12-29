"""Streamlit app to upload existing data, run scrapers and show new leads."""
import streamlit as st
import pandas as pd
import tempfile
import os

from src.scraper.google_maps import search_google_maps
from src.scraper.snappfood import search_snappfood
from src.comparator import filter_new_leads


st.set_page_config(page_title="Lead Gen Automation", layout="wide")
st.title("Lead Generation & Automation — Cafes / Restaurants / Ice Cream")

uploaded = st.file_uploader("Upload existing_data.csv", type=["csv"])
location = st.text_input("Search location (city or area)", value="")
categories = st.multiselect("Categories", ["Cafes", "Restaurants", "Ice Cream Shops"], default=["Cafes", "Restaurants", "Ice Cream Shops"])
start = st.button("Start Automatic Search")


def run_search(categories, location, headless=True):
    results = []
    for cat in categories:
        q = cat
        results += search_google_maps(q, location, headless=headless, max_results=40)
        results += search_snappfood(q, location, headless=headless, max_results=40)
    # simple dedupe by name+address
    seen = set()
    aggregated = []
    for r in results:
        key = (r.get('name', '').lower(), r.get('address', '').lower())
        if key in seen:
            continue
        seen.add(key)
        aggregated.append(r)
    return aggregated


if start:
    if not uploaded:
        st.error("Please upload `existing_data.csv` first.")
    else:
        with st.spinner("Running scrapers (this may take a few minutes)..."):
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.csv')
            tmp.write(uploaded.getvalue())
            tmp.flush()
            tmp.close()
            leads = run_search(categories, location, headless=True)
            if not leads:
                st.info("No leads were found by the scrapers.")
            else:
                new_df = filter_new_leads(leads, tmp.name, threshold=85)
                if new_df.empty:
                    st.success("No new leads — all found businesses exist in your CSV.")
                else:
                    st.subheader("New Leads Found")
                    st.dataframe(new_df)
                    csv = new_df.to_csv(index=False).encode('utf-8')
                    st.download_button("Download new leads CSV", data=csv, file_name='new_leads.csv', mime='text/csv')
            try:
                os.unlink(tmp.name)
            except Exception:
                pass
