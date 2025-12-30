"""Demo data generator for quick UI testing without real scrapers."""
import random
from typing import List


SAMPLE_NAMES = [
    "Cafe Roya",
    "Bistro Negin",
    "Ice Cream Ziba",
    "Saffron Restaurant",
    "Coffee House Tehran",
    "Sweet Scoop",
    "Neighborhood Cafe",
    "Green Garden Restaurant",
    "Petit Cafe",
    "Ocean Ice Cream",
    "Laleh Cafe",
    "Taste Kitchen",
    "City Diner",
    "Minoo Cafe",
    "Sunset Restaurant",
    "Polar Ice Cream",
    "Rose Cafe",
    "Golden Spoon",
    "Downtown Deli",
    "Family Bistro",
]

SAMPLE_ADDRESSES = [
    "Valiasr St, Tehran",
    "Enghelab Sq, Tehran",
    "Shariati Ave, Tehran",
    "Niavaran, Tehran",
    "Tajrish Bazaar, Tehran",
    "Beheshti St, Tehran",
    "Saadat Abad, Tehran",
    "Jordan St, Tehran",
    "Mirdamad Blvd, Tehran",
    "Keshavarz Blvd, Tehran",
]

SOURCES = ["google_maps", "snappfood", "instagram"]


def demo_leads(count: int = 20, location: str = "") -> List[dict]:
    random.seed(42)
    leads = []
    for i in range(count):
        name = SAMPLE_NAMES[i % len(SAMPLE_NAMES)]
        addr = SAMPLE_ADDRESSES[i % len(SAMPLE_ADDRESSES)]
        if location:
            addr = f"{addr} ({location})"
        leads.append({
            "name": f"{name} {i+1}",
            "address": addr,
            "source": random.choice(SOURCES),
            "link": f"https://example.com/{name.replace(' ','_')}/{i+1}",
        })
    return leads
