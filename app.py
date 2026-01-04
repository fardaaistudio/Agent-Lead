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
from src.scraper.phone_extractor import fetch_phone_from_page
from concurrent.futures import ThreadPoolExecutor, as_completed


st.set_page_config(page_title="Lead Gen Automation", page_icon=":rocket:", layout="wide", initial_sidebar_state="expanded")

css_path = os.path.join(os.path.dirname(__file__), "static", "style.css")
try:
    with open(css_path, "r", encoding="utf-8") as _css:
        st.markdown(f"<style>{_css.read()}</style>", unsafe_allow_html=True)
except Exception:
    # fallback: minimal inline style if file missing
    st.markdown("<style>body{background:#0f1724;color:#e6eef8}</style>", unsafe_allow_html=True)

# header: show logo image from static files and brand text
col1, col2 = st.columns([0.08, 0.92])
with col1:
    try:
        st.image(os.path.join("static", "logo.svg"), width=64)
    except Exception:
        st.markdown('<div class="logo" aria-hidden="true"></div>', unsafe_allow_html=True)
with col2:
    st.markdown(
        """
        <div class='brand'>
          <h1>LeadGen — Modern Minimal</h1>
          <p>Find and filter top local Cafes, Restaurants and Ice Cream Shops</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


with st.sidebar:
    st.header("Controls")
    uploaded = st.file_uploader("Upload existing_data.csv (optional)", type=["csv"])
    location = st.text_input("Location (city, area)")
    categories = st.multiselect("Categories", ["Cafes", "Restaurants", "Ice Cream Shops"], default=["Cafes", "Restaurants", "Ice Cream Shops"])
    max_results = st.slider("Max results per source", 10, 200, 40)
    desired_count = st.slider("Desired leads to return", 5, 100, 100)
    threshold = st.slider("Duplicate match threshold", 60, 100, 85)
    headless = st.checkbox("Run browsers headless", value=True)
    start = st.button("Start Automatic Search")
    st.markdown("---")
    st.markdown("Tips:\n- Upload your `existing_data.csv` to avoid duplicates.\n- Increase `threshold` for stricter duplicate matching.")
    demo_btn = st.button("Quick Test (Demo) — generate sample leads")
from src.demo import demo_leads


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

    # attempt to fetch phone numbers for candidates that have links — parallel
    to_fetch = []
    for idx, r in enumerate(aggregated):
        if r.get('phone'):
            continue
        link = r.get('link')
        if not link:
            r['phone'] = ''
            continue
        to_fetch.append((idx, link))

    if to_fetch:
        max_workers = min(8, len(to_fetch))
        with ThreadPoolExecutor(max_workers=max_workers) as ex:
            futures = {ex.submit(fetch_phone_from_page, link, headless): idx for (idx, link) in to_fetch}
            for fut in as_completed(futures):
                idx = futures[fut]
                try:
                    phone = fut.result()
                    aggregated[idx]['phone'] = phone or ''
                except Exception:
                    aggregated[idx]['phone'] = ''
    return aggregated


def render_lead_card(col, lead: dict):
    with col:
                name = lead.get('name', '-')
                address = lead.get('address', '').strip()
                source = lead.get('source', '')
                phone = lead.get('phone', '-')
                link = lead.get('link')
                html = f"""
                <div class='card'>
                    <div class='lead-title'>{name}</div>
                    <div class='lead-sub'>{address} · <span style='opacity:0.85'>{source}</span></div>
                    <div style='display:flex;justify-content:space-between;align-items:center;margin-top:8px'>
                        <div style='font-weight:600;color:#ffd36a'>{phone or '-'}</div>
                        {f"<a href='{link}' target='_blank'>Open link →</a>" if link else ""}
                    </div>
                </div>
                """
                st.markdown(html, unsafe_allow_html=True)


def _execute_flow(leads, temp_path=None):
    status = st.empty()
    progress = st.progress(0)
    log_box = st.empty()

    status.info("Processing leads...")
    t0 = time.time()
    try:
        progress.progress(40)
        status.info(f"Candidates found — {len(leads)}")

        if temp_path:
            status.info("Filtering duplicates against uploaded CSV...")
            new_df = filter_new_leads(leads, temp_path, threshold=threshold)
        else:
            status.info("No existing CSV provided — returning top candidates.")
            import pandas as _pd
            new_df = _pd.DataFrame(leads)
            if new_df.empty:
                new_df = _pd.DataFrame(columns=["name", "address", "source", "link", "phone"])
            else:
                new_df = new_df.drop_duplicates(subset=["name", "address"])[:desired_count]

        progress.progress(80)

        if new_df.empty:
            status.success("No leads available after processing.")
            st.info("Try increasing `max results` or changing the location/categories.")
        else:
            if temp_path is None:
                new_df = new_df.head(desired_count)
            status.success(f"{len(new_df)} leads ready")
            st.markdown("### Leads")
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
        status.error(f"Error during processing: {e}")
    finally:
        if temp_path:
            try:
                os.unlink(temp_path)
            except Exception:
                pass
        progress.progress(100)
        elapsed = time.time() - t0
        log_box.info(f"Completed in {elapsed:.1f}s")


# Demo button acts independently
if demo_btn:
    leads = demo_leads(desired_count, location)
    _execute_flow(leads, temp_path=None)

# Start performs real scraping (may require Playwright deps). Works with or without uploaded CSV.
if start:
    temp_path = None
    if uploaded:
        tfile = tempfile.NamedTemporaryFile(delete=False, suffix='.csv')
        tfile.write(uploaded.getvalue())
        tfile.flush()
        tfile.close()
        temp_path = tfile.name

    try:
        leads = run_search(categories, location, headless=headless, max_results=max_results)
    except Exception as e:
        st.error(f"Error running scrapers: {e}")
        leads = []

    _execute_flow(leads, temp_path=temp_path)
