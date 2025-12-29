# Agent-Lead — Lead Generation & Automation

Automates discovery of new Cafes, Restaurants, and Ice Cream Shops from Google Maps and SnappFood and filters out existing entries using `existing_data.csv`.

Quickstart

1. Install Python deps and Playwright browsers:

```bash
pip install -r requirements.txt
python -m playwright install
```

2. (Optional) Install OS packages required by browsers on Linux:

```bash
sudo ./setup_playwright_deps.sh
```

3. Run the Streamlit UI and upload your `existing_data.csv`:

```bash
streamlit run app.py
```

4. Or run the CLI to produce `new_leads.csv` directly:

```bash
python run_scrape.py --existing existing_data.csv --out new_leads.csv --location "Tehran" --headless
```

Files of interest

- `app.py` — Streamlit web UI for uploading existing CSV and running scrapers.
- `run_scrape.py` — Simple CLI runner that runs scrapers and writes new leads CSV.
- `src/scraper` — Playwright helpers and scrapers for Google Maps and SnappFood.
- `src/comparator.py` — Loads `existing_data.csv` and filters duplicates using RapidFuzz.
- `requirements.txt` — Python dependencies.

Notes & safety

- Playwright downloads browser binaries; the `setup_playwright_deps.sh` helper installs common Linux libraries required by the browsers (requires `sudo`).
- The scrapers use Playwright and may require selector tweaks if target sites change.
- The comparator uses fuzzy matching (token sort ratio) to reduce duplicates; adjust the threshold in `src/comparator.py` if you need stricter/looser matching.

Next steps

- Add scheduled runs (GitHub Actions / cron) to periodically gather leads.
- Add authentication and access controls to the Streamlit app before exposing it.
# Agent-Lead