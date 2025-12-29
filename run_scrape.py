"""CLI runner to run scrapers and save new leads compared to existing CSV."""
import argparse
import sys
import pandas as pd

from src.scraper.google_maps import search_google_maps
from src.scraper.snappfood import search_snappfood
from src.comparator import filter_new_leads


def aggregate_search(categories, location, headless=True):
    results = []
    for cat in categories:
        results += search_google_maps(cat, location, headless=headless, max_results=50)
        results += search_snappfood(cat, location, headless=headless, max_results=50)
    # dedupe
    seen = set()
    out = []
    for r in results:
        key = (r.get('name', '').lower(), r.get('address', '').lower())
        if key in seen:
            continue
        seen.add(key)
        out.append(r)
    return out


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--existing', required=True, help='Path to existing_data.csv')
    p.add_argument('--out', default='new_leads.csv', help='Output CSV file')
    p.add_argument('--location', default='', help='Location hint for searches')
    p.add_argument('--headless', action='store_true', help='Run browsers in headless mode')
    p.add_argument('--categories', nargs='+', default=['Cafes', 'Restaurants', 'Ice Cream Shops'])
    args = p.parse_args()

    leads = aggregate_search(args.categories, args.location, headless=args.headless)
    if not leads:
        print('No leads found by scrapers.')
        sys.exit(0)

    new_df = filter_new_leads(leads, args.existing)
    if new_df.empty:
        print('No new leads — nothing to save.')
    else:
        new_df.to_csv(args.out, index=False)
        print(f'Wrote {len(new_df)} new leads to {args.out}')


if __name__ == '__main__':
    main()
