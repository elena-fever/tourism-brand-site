#!/usr/bin/env python3
"""Assign intent clusters to filtered Spain country keywords; emit Country PLP layout CSV."""

from __future__ import annotations

import csv
import re
import sys
from pathlib import Path


OUT_COLUMNS = [
    "Keyword",
    "Page type",
    "Location",
    "Tag",
    "Avg. monthly searches",
    "Three month change",
    "YoY change",
    "Competition",
    "Searches: Apr 2025",
    "Searches: May 2025",
    "Searches: Jun 2025",
    "Searches: Jul 2025",
    "Searches: Aug 2025",
    "Searches: Sep 2025",
    "Searches: Oct 2025",
    "Searches: Nov 2025",
    "Searches: Dec 2025",
    "Searches: Jan 2026",
    "Searches: Feb 2026",
    "Searches: Mar 2026",
]

# (cluster_label, compiled_regex) — first match wins
_CLUSTER_RULES: list[tuple[str, re.Pattern[str]]] = [
    (
        "Budget & value",
        re.compile(
            r"\b(cheap|cheapest|budget|affordable|luxury|expensive|cost|costs|money|save money|deal)\b",
            re.I,
        ),
    ),
    (
        "Stay & accommodation",
        re.compile(
            r"\b(hotel|hotels|resort|resorts|hostel|hostels|airbnb|accommodation|lodging|where to stay|places to stay|rent an apartment)\b",
            re.I,
        ),
    ),
    (
        "Transport & getting around",
        re.compile(
            r"\b(flight|flights|fly to|train|trains|renfe|high-speed rail|ferry|ferries|"
            r"car hire|hire car|rent a car|rental car|driving in|drive around|bus tour|public transport)\b",
            re.I,
        ),
    ),
    (
        "Food & drink",
        re.compile(
            r"\b(food|foods|wine|tapas|paella|gastronomy|culinary|restaurant|restaurants|eat in|eating in|drinks)\b",
            re.I,
        ),
    ),
    (
        "Nightlife & parties",
        re.compile(r"\b(party|nightlife|clubbing|clubs|bars)\b", re.I),
    ),
    (
        "Beaches & coast",
        re.compile(
            r"\b(beach|beaches|seaside|coastal|seafront|sunbathe|swimming|mediterranean coast)\b",
            re.I,
        ),
    ),
    (
        "Seasonality & weather",
        re.compile(
            r"\b(january|february|march|april|may|june|july|august|september|october|november|december)\b|"
            r"\b(winter|spring|summer|autumn|fall)\b|"
            r"\b(weather|climate|temperature|warmest|coldest|hottest|rainy|snow)\b|"
            r"\b(when to visit|when to go|best time to visit|best month)\b",
            re.I,
        ),
    ),
    (
        "Itineraries & road trips",
        re.compile(
            r"\b(itinerary|itineraries|road trip|roadtrip|driving tour|route\b|routes\b|"
            r"one week|two week|three week|10 days|14 days|7 days|\d+\s*days in spain)\b",
            re.I,
        ),
    ),
    (
        "Regional exploration",
        re.compile(
            r"\b(north spain|south spain|east spain|west spain|northern spain|southern spain|"
            r"eastern spain|western spain|north of spain|south of spain|mainland spain|central spain|"
            r"north coast|south coast|east coast|west coast)\b",
            re.I,
        ),
    ),
    (
        "Urban destinations",
        re.compile(
            r"\b(cities\b|city\b|towns\b|town\b|city break|urban)\b",
            re.I,
        ),
    ),
    (
        "Nature & outdoors",
        re.compile(
            r"\b(natural attraction|national park|hiking|trek|countryside|rural|scenery|scenic|mountains|outdoor)\b",
            re.I,
        ),
    ),
    (
        "Activities & experiences",
        re.compile(
            r"\b(things to do|what to do|activities|experiences|fun things)\b",
            re.I,
        ),
    ),
    (
        "Sightseeing & landmarks",
        re.compile(
            r"\b(sights\b|sightseeing|things to see|must see|must-see|must visit|landmarks|"
            r"tourist attractions?\b|attractions in spain|top sights|famous places|iconic)\b",
            re.I,
        ),
    ),
    (
        "Trip types & holidays",
        re.compile(
            r"\b(holiday|holidays|vacation|honeymoon|family trip|with family|with kids|for couples|"
            r"solo travel|getaway|city trip)\b",
            re.I,
        ),
    ),
    (
        "Hidden gems & alternatives",
        re.compile(
            r"\b(off the beaten|hidden gem|non tourist|secret place|underrated|less touristy)\b",
            re.I,
        ),
    ),
    (
        "Practical planning",
        re.compile(
            r"\b(tips|travel guide|guide to|safety|visa|packing|first time|first timers|reddit|checklist|what to know)\b",
            re.I,
        ),
    ),
]


def cluster_for_keyword(keyword: str) -> str:
    k = keyword.strip()
    for label, rx in _CLUSTER_RULES:
        if rx.search(k):
            return label
    return "Places & destinations"


def read_rows(path: Path) -> tuple[list[str], list[list[str]]]:
    text = path.read_text(encoding="utf-8-sig", errors="replace")
    lines = text.splitlines()
    if len(lines) < 4:
        raise ValueError("CSV too short")
    # Planner export: title + date range, then header row, then data
    header_line = lines[2]
    header = next(csv.reader([header_line], delimiter="\t"))
    reader = csv.reader(lines[3:], delimiter="\t")
    rows: list[list[str]] = []
    for row in reader:
        if row and any(cell.strip() for cell in row):
            rows.append(row)
    return header, rows


def main() -> int:
    base = Path(__file__).resolve().parents[1]
    inp = (
        Path(sys.argv[1])
        if len(sys.argv) > 1
        else base / "keyword research" / "Keyword Stats 2026-05-07 at 13_02_21_spain-country-only.csv"
    )
    out = (
        Path(sys.argv[2])
        if len(sys.argv) > 2
        else base
        / "keyword research"
        / "Spain_Country_PLP_keywords_clustered.csv"
    )

    header, rows = read_rows(inp)

    def idx(name: str) -> int:
        try:
            return header.index(name)
        except ValueError as e:
            raise KeyError(f"Missing column: {name}") from e

    i_kw = idx("Keyword")
    pull = [
        i_kw,
        idx("Avg. monthly searches"),
        idx("Three month change"),
        idx("YoY change"),
        idx("Competition"),
        *[idx(f"Searches: {m} 2025") for m in ["Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]],
        idx("Searches: Jan 2026"),
        idx("Searches: Feb 2026"),
        idx("Searches: Mar 2026"),
    ]

    out_rows: list[list[str]] = []
    for row in rows:
        if len(row) <= max(pull):
            continue
        kw = row[i_kw].strip()
        if not kw:
            continue
        tag = cluster_for_keyword(kw)
        vals = [row[j] for j in pull]
        out_rows.append(
            [
                vals[0],
                "Country PLP",
                "Spain",
                tag,
                *vals[1:],
            ]
        )

    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(OUT_COLUMNS)
        w.writerows(out_rows)

    print(f"Written {len(out_rows)} rows -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
