"""Streamlit app to upload existing data, run scrapers and show new leads.

This enhanced UI provides sidebar controls, progress/logging, and a card
style display for quick human review before downloading results.
"""
import os
import tempfile
import time
from typing import List

import pandas as pd
import streamlit as st

from src.comparator import filter_new_leads
from src.scraper.google_maps import search_google_maps
from src.scraper.snappfood import search_snappfood


st.set_page_config(page_title="Lead Gen Automation", layout="wide")

st.markdown(
    """
    <style>
    .header {display:flex; align-items:center}
    .logo {width:56px; height:56px; background:#f7630c; border-radius:8px; display:inline-block; margin-right:12px}
    .card {padding:12px; border-radius:8px; border:1px solid #eee; background:#fff}
    </style>
    <div class="header">
      <div class="logo"></div>
      <div>
        <h1 style="margin:0;">Lead Generation & Automation</h1>
        <div style="color:gray">Discover new Cafes, Restaurants and Ice Cream Shops</div>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)


with st.sidebar:
    st.header("Controls")
    uploaded = st.file_uploader("Upload existing_data.csv", type=["csv"])
    location = st.text_input("Location (city, area)")
    categories = st.multiselect("Categories", ["Cafes", "Restaurants", "Ice Cream Shops"], default=["Cafes", "Restaurants", "Ice Cream Shops"])
    max_results = st.slider("Max results per source", 10, 200, 40)
    threshold = st.slider("Duplicate match threshold", 60, 100, 85)
    headless = st.checkbox("Run browsers headless", value=True)
    start = st.button("Start Automatic Search")
    st.markdown("---")
    st.markdown("Tips:\n- Upload your `existing_data.csv` to avoid duplicates.\n- Increase `threshold` for stricter duplicate matching.")


def run_search(categories: List[str], location: str, headless: bool = True, max_results: int = 40) -> List[dict]:
    results = []
    for cat in categories:
        # try Google Maps first
        try:
            results += search_google_maps(cat, location, headless=headless, max_results=max_results)
        except Exception as e:
            st.warning(f"Google Maps scraper error for {cat}: {e}")
        # SnappFood fallback
        try:
            results += search_snappfood(cat, location, headless=headless, max_results=max_results)
        except Exception as e:
            st.warning(f"SnappFood scraper error for {cat}: {e}")

    # dedupe by normalized name+address
    seen = set()
    aggregated = []
    for r in results:
        key = (r.get('name', '').strip().lower(), r.get('address', '').strip().lower())
        if not key[0]:
            continue
        if key in seen:
            continue
        seen.add(key)
        aggregated.append(r)
    return aggregated


def render_lead_card(col, lead: dict):
    with col:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown(f"**{lead.get('name','-')}**  ")
        st.markdown(f"_{lead.get('address','').strip()}_")
        st.markdown(f"Source: **{lead.get('source','')}**")
        if lead.get('link'):
            st.markdown(f"[Open link]({lead.get('link')})")
        st.markdown("</div>", unsafe_allow_html=True)


if start:
    if not uploaded:
        st.error("Please upload `existing_data.csv` from the sidebar before starting.")
    else:
        temp = tempfile.NamedTemporaryFile(delete=False, suffix='.csv')
        temp.write(uploaded.getvalue())
        temp.flush()
        temp.close()

        status = st.empty()
        progress = st.progress(0)
        log_box = st.empty()

        status.info("Starting scrapers — this can take a few minutes...")
        t0 = time.time()
        try:
            leads = run_search(categories, location, headless=headless, max_results=max_results)
            progress.progress(40)
            status.info(f"Scrapers finished — {len(leads)} raw candidates found")

            # Filter against uploaded existing CSV
            status.info("Filtering duplicates against uploaded CSV...")
            new_df = filter_new_leads(leads, temp.name, threshold=threshold)
            progress.progress(80)

            if new_df.empty:
                status.success("No new leads found — all candidates were duplicates.")
                st.info("Try increasing `max results` or lowering the duplicate threshold.")
            else:
                status.success(f"{len(new_df)} new leads found")
                st.markdown("### New Leads")
                # Cards layout
                rows = (len(new_df) + 2) // 3
                for r in range(rows):
                    cols = st.columns(3)
                    for i in range(3):
                        idx = r * 3 + i
                        if idx >= len(new_df):
                            break
                        lead = new_df.iloc[idx].to_dict()
                        render_lead_card(cols[i], lead)

                st.markdown("---")
                st.dataframe(new_df)
                csv = new_df.to_csv(index=False).encode('utf-8')
                st.download_button("Download CSV", data=csv, file_name='new_leads.csv', mime='text/csv')

        except Exception as e:
            status.error(f"Error during scraping: {e}")
        finally:
            try:
                os.unlink(temp.name)
            except Exception:
                pass
            progress.progress(100)
            elapsed = time.time() - t0
            log_box.info(f"Completed in {elapsed:.1f}s")
