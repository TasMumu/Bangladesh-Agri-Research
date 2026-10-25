"""Shared paths and helpers for the v2 (BBS-only) pipeline."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]          # project root
V2 = ROOT / "v2"
BRONZE = ROOT / "data" / "bronze"
V2_BRONZE = V2 / "data" / "bronze"
V2_SILVER = V2 / "data" / "silver"
V2_GOLD = V2 / "data" / "gold" / "bangladesh_agri_v2.duckdb"
TABLES = V2 / "outputs" / "tables"
FIGURES = V2 / "outputs" / "figures"
LOGS = V2 / "logs"

for p in (V2_BRONZE, V2_SILVER, V2_GOLD.parent, TABLES, FIGURES, LOGS):
    p.mkdir(parents=True, exist_ok=True)

GEE_PROJECT = "bd-agri-climate"

# Canonical district names (64) and the spelling variants found across
# BBS yearbooks, GADM v4.1 and the GEE/ERA5 extracts.
CANONICAL = [
    "Bagerhat", "Bandarban", "Barguna", "Barishal", "Bhola", "Bogura",
    "Brahmanbaria", "Chandpur", "Chapai Nawabganj", "Chattogram", "Chuadanga",
    "Cox's Bazar", "Cumilla", "Dhaka", "Dinajpur", "Faridpur", "Feni",
    "Gaibandha", "Gazipur", "Gopalganj", "Habiganj", "Jamalpur", "Jashore",
    "Jhalokati", "Jhenaidah", "Joypurhat", "Khagrachhari", "Khulna",
    "Kishoreganj", "Kurigram", "Kushtia", "Lakshmipur", "Lalmonirhat",
    "Madaripur", "Magura", "Manikganj", "Meherpur", "Moulvibazar",
    "Munshiganj", "Mymensingh", "Naogaon", "Narail", "Narayanganj",
    "Narsingdi", "Natore", "Netrokona", "Nilphamari", "Noakhali", "Pabna",
    "Panchagarh", "Patuakhali", "Pirojpur", "Rajbari", "Rajshahi",
    "Rangamati", "Rangpur", "Satkhira", "Shariatpur", "Sherpur", "Sirajganj",
    "Sunamganj", "Sylhet", "Tangail", "Thakurgaon",
]

ALIASES = {
    "barisal": "Barishal", "bogra": "Bogura", "chapainawabganj": "Chapai Nawabganj",
    "nawabganj": "Chapai Nawabganj", "chapai": "Chapai Nawabganj",
    "chapainababganj": "Chapai Nawabganj", "chittagong": "Chattogram",
    "chattagram": "Chattogram", "chatogram": "Chattogram", "coxsbazar": "Cox's Bazar",
    "comilla": "Cumilla", "jessore": "Jashore", "jhalakati": "Jhalokati",
    "jhallokati": "Jhalokati", "jhalokathi": "Jhalokati", "jhenaidaha": "Jhenaidah",
    "jhenidah": "Jhenaidah", "khagrachari": "Khagrachhari", "khagrachhari": "Khagrachhari",
    "laxmipur": "Lakshmipur", "lakshimpur": "Lakshmipur", "maulvibazar": "Moulvibazar",
    "moulvibazaar": "Moulvibazar", "netrakona": "Netrokona", "netrokona": "Netrokona",
    "panchagar": "Panchagarh", "panchghar": "Panchagarh", "rangamati": "Rangamati",
    "rangamatihilltracts": "Rangamati", "narshingdi": "Narsingdi", "narsinghdi": "Narsingdi",
    "munshigonj": "Munshiganj", "sirajgonj": "Sirajganj", "sherpur": "Sherpur",
    "joypurhat": "Joypurhat", "jaipurhat": "Joypurhat", "kishorganj": "Kishoreganj",
    "kishoregonj": "Kishoreganj", "gopalgonj": "Gopalganj", "habigonj": "Habiganj",
    "sunamgonj": "Sunamganj", "madaripur": "Madaripur", "shariatpur": "Shariatpur",
    "brahamanbaria": "Brahmanbaria", "brahmanbaria": "Brahmanbaria",
    "patuakhali": "Patuakhali", "nilphamari": "Nilphamari", "manikgonj": "Manikganj",
    "maulavibazar": "Moulvibazar", "maulovibazar": "Moulvibazar", "hobigonj": "Habiganj",
    "munsigonj": "Munshiganj", "narayangonj": "Narayanganj", "jhalakathi": "Jhalokati",
    "perojpur": "Pirojpur", "noagaon": "Naogaon", "nawabgonj": "Chapai Nawabganj",
    "mymenshing": "Mymensingh", "chapinawabgonj": "Chapai Nawabganj",
    "chapainawabgonj": "Chapai Nawabganj", "kustia": "Kushtia", "coxbazar": "Cox's Bazar",
    "laksmipur": "Lakshmipur",
}

_CANON_KEY = {re.sub(r"[^a-z]", "", c.lower()): c for c in CANONICAL}


def canon_district(name: str):
    """Return the canonical district name, or None if not a district."""
    if name is None:
        return None
    key = re.sub(r"[^a-z]", "", str(name).lower())
    if not key:
        return None
    if key in _CANON_KEY:
        return _CANON_KEY[key]
    return ALIASES.get(key)
