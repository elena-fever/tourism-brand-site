"""One-off generator for matriz-urls-ciudades-completo.csv — run from repo root or this folder."""
from __future__ import annotations

import csv
import re
import unicodedata
from pathlib import Path

BASE = "https://tourism-tickets.com"

# (City label as in source list, English country name, country slug)
ROWS_RAW: list[tuple[str, str, str]] = [
    # United States
    ("New York", "United States", "united-states"),
    ("Orlando", "United States", "united-states"),
    ("Los Angeles", "United States", "united-states"),
    ("Chicago", "United States", "united-states"),
    ("San Diego", "United States", "united-states"),
    ("Miami", "United States", "united-states"),
    ("Washington", "United States", "united-states"),
    ("San Francisco", "United States", "united-states"),
    ("Boston", "United States", "united-states"),
    ("Seattle", "United States", "united-states"),
    ("Nashville", "United States", "united-states"),
    ("Houston", "United States", "united-states"),
    ("Atlanta", "United States", "united-states"),
    ("New Orleans", "United States", "united-states"),
    ("Tampa", "United States", "united-states"),
    ("Austin", "United States", "united-states"),
    ("San Antonio", "United States", "united-states"),
    ("Phoenix", "United States", "united-states"),
    ("Las Vegas", "United States", "united-states"),
    ("Denver", "United States", "united-states"),
    ("Philadelphia", "United States", "united-states"),
    ("Huntsville", "United States", "united-states"),
    ("Woodside", "United States", "united-states"),
    ("Daytona Beach", "United States", "united-states"),
    ("Pigeon Forge", "United States", "united-states"),
    # United Kingdom
    ("London", "United Kingdom", "united-kingdom"),
    ("Liverpool", "United Kingdom", "united-kingdom"),
    ("Birmingham", "United Kingdom", "united-kingdom"),
    ("Belfast", "United Kingdom", "united-kingdom"),
    ("Edinburgh", "United Kingdom", "united-kingdom"),
    # Australia
    ("Brisbane", "Australia", "australia"),
    ("Sydney", "Australia", "australia"),
    ("Melbourne", "Australia", "australia"),
    # Canada
    ("Vancouver", "Canada", "canada"),
    ("Toronto", "Canada", "canada"),
    ("Montreal", "Canada", "canada"),
    ("Calgary", "Canada", "canada"),
    ("Ottawa", "Canada", "canada"),
    # Netherlands
    ("Amsterdam", "Netherlands", "netherlands"),
    ("Rotterdam", "Netherlands", "netherlands"),
    ("Leiden", "Netherlands", "netherlands"),
    # Germany
    ("Berlin", "Germany", "germany"),
    ("Cologne", "Germany", "germany"),
    ("Dortmund", "Germany", "germany"),
    ("Hamburg", "Germany", "germany"),
    ("Munich", "Germany", "germany"),
    # Spain
    ("Madrid", "Spain", "spain"),
    ("Barcelona", "Spain", "spain"),
    ("Seville", "Spain", "spain"),
    ("Valencia", "Spain", "spain"),
    ("Malaga", "Spain", "spain"),
    ("Murcia", "Spain", "spain"),
    ("Toledo", "Spain", "spain"),
    ("Tenerife", "Spain", "spain"),
    ("Las Palmas de Gran Canaria", "Spain", "spain"),
    ("Benidorm", "Spain", "spain"),
    ("Gijón", "Spain", "spain"),
    ("Córdoba", "Spain", "spain"),
    ("Mallorca", "Spain", "spain"),
    # Italy
    ("Milan", "Italy", "italy"),
    ("Venice", "Italy", "italy"),
    ("Florence", "Italy", "italy"),
    ("Rome", "Italy", "italy"),
    ("Naples", "Italy", "italy"),
    ("Turin", "Italy", "italy"),
    ("Bologna", "Italy", "italy"),
    ("Rimini", "Italy", "italy"),
    ("Genova", "Italy", "italy"),
    ("Verona", "Italy", "italy"),
    ("Palermo", "Italy", "italy"),
    # France
    ("Paris", "France", "france"),
    ("Lyon", "France", "france"),
    ("Nice", "France", "france"),
    ("Marseille", "France", "france"),
    ("Toulouse", "France", "france"),
    ("Montpellier", "France", "france"),
    ("Lille", "France", "france"),
    ("Avignon", "France", "france"),
    ("Chantilly", "France", "france"),
    ("Aix-en-Provence", "France", "france"),
    ("Tours", "France", "france"),
    ("Metz", "France", "france"),
    ("Poitiers", "France", "france"),
    ("Colmar", "France", "france"),
    # United Arab Emirates
    ("Dubai", "United Arab Emirates", "united-arab-emirates"),
    # Sweden
    ("Stockholm", "Sweden", "sweden"),
    # Austria
    ("Vienna", "Austria", "austria"),
    # Brazil
    ("Rio de Janeiro", "Brazil", "brazil"),
    # Mexico
    ("Mexico DF", "Mexico", "mexico"),
    # Denmark
    ("Copenhagen", "Denmark", "denmark"),
    # Belgium
    ("Brussels", "Belgium", "belgium"),
    ("Ghent", "Belgium", "belgium"),
    ("Antwerp", "Belgium", "belgium"),
    # Switzerland
    ("Zurich", "Switzerland", "switzerland"),
    # Czech Republic
    ("Prague", "Czech Republic", "czech-republic"),
    # Norway
    ("Oslo", "Norway", "norway"),
    # Finland
    ("Helsinki", "Finland", "finland"),
    # Portugal
    ("Lisbon", "Portugal", "portugal"),
    ("Porto", "Portugal", "portugal"),
    # Ireland
    ("Dublin", "Ireland", "ireland"),
]

# English URL slug for city (override when label != canonical slug)
CITY_SLUG_OVERRIDE: dict[str, str] = {
    "Mexico DF": "mexico-city",
    "Genova": "genoa",
    "Las Palmas de Gran Canaria": "las-palmas-de-gran-canaria",
    "Gijón": "gijon",
    "Córdoba": "cordoba",
}

# English labels for the sheet "City" column (City PDP only); URLs still use slugify / overrides.
CITY_DISPLAY: dict[str, str] = {
    "Mexico DF": "Mexico City",
    "Genova": "Genoa",
    "Gijón": "Gijon",
    "Córdoba": "Cordoba",
}


def slugify(name: str) -> str:
    s = unicodedata.normalize("NFKD", name)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s


def city_slug(label: str) -> str:
    if label in CITY_SLUG_OVERRIDE:
        return CITY_SLUG_OVERRIDE[label]
    return slugify(label)


def main() -> None:
    out = Path(__file__).resolve().parent / "matriz-urls-ciudades-completo.csv"
    with out.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Page type", "Country", "City", "URLs"])
        for city_label, country_name, cslug in ROWS_RAW:
            cs = city_slug(city_label)
            w.writerow(
                ["Country (PLP)", country_name, "N/A", f"{BASE}/{cslug}/"]
            )
            w.writerow(
                [
                    "City (PDP)",
                    country_name,
                    CITY_DISPLAY.get(city_label, city_label),
                    f"{BASE}/{cslug}/{cs}/",
                ]
            )
            w.writerow(
                [
                    "Itineraries (PLP)",
                    country_name,
                    "N/A",
                    f"{BASE}/itineraries/{cslug}/",
                ]
            )
            w.writerow(
                [
                    "Travel guide (PLP)",
                    country_name,
                    "N/A",
                    f"{BASE}/travel-guides/{cslug}/",
                ]
            )
    print(f"Wrote {out} ({len(ROWS_RAW) * 4} rows)")


if __name__ == "__main__":
    main()
