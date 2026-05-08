#!/usr/bin/env python3
"""Assign intent clusters to filtered USA country keywords; emit Country PLP layout CSV."""

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
            r"\b(hotel|hotels|resort|resorts|hostel|hostels|airbnb|accommodation|lodging|where to stay|"
            r"places to stay|rent an apartment)\b",
            re.I,
        ),
    ),
    (
        "Transport & getting around",
        re.compile(
            r"\b(flight|flights|fly to|train|trains|amtrak|greyhound|ferry|ferries|"
            r"car hire|hire car|rent a car|rental car|rv\b|camper|campervan|"
            r"driving in|drive across|bus tour|public transport|getting around)\b",
            re.I,
        ),
    ),
    (
        "Food & drink",
        re.compile(
            r"\b(food|foods|wine|bbq|barbecue|breweries|brewery|gastronomy|culinary|restaurant|restaurants|"
            r"eat in america|eating in america)\b",
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
            r"\b(beach|beaches|seaside|coastal|seafront|sunbathe|swimming|gulf coast|east coast|west coast)\b",
            re.I,
        ),
    ),
    (
        "Seasonality & weather",
        re.compile(
            r"\b(january|february|march|april|may|june|july|august|september|october|november|december)\b|"
            r"\b(winter|spring|summer|autumn|fall)\b|"
            r"\b(weather|climate|temperature|warmest|coldest|hottest|rainy|snow|hurricane season)\b|"
            r"\b(when to visit|when to go|best time to visit|best month)\b",
            re.I,
        ),
    ),
    (
        "Itineraries & road trips",
        re.compile(
            r"\b(itinerary|itineraries|road trip|roadtrip|driving tour|route\b|routes\b|"
            r"one week|two week|three week|10 days|14 days|7 days|\d+\s*days in (the )?(us|usa)|"
            r"\d+\s*days in america)\b",
            re.I,
        ),
    ),
    (
        "Regional exploration",
        re.compile(
            r"\b(north(eastern)? us\b|south(eastern)? us\b|east(ern)? us\b|west(ern)? us\b|"
            r"northern us\b|southern us\b|eastern us\b|western us\b|"
            r"midwest|midwestern|northeast|northwest|southeast|southwest|deep south|pacific northwest|"
            r"east coast of (the )?(us|usa)|west coast of (the )?(us|usa)|gulf states\b)\b",
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
            r"\b(natural attraction|national park|hiking|trek|countryside|rural|scenery|scenic|mountains|"
            r"outdoor|great outdoors)\b",
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
            r"tourist attractions?\b|attractions in (the )?(us|usa)|attractions in america|"
            r"top sights|famous places|iconic)\b",
            re.I,
        ),
    ),
    (
        "Trip types & holidays",
        re.compile(
            r"\b(holiday|holidays|vacation|honeymoon|family trip|with family|with kids|for couples|"
            r"solo travel|solo trips?|\bsolo\b|getaway|city trip)\b",
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
        else base / "keyword research" / "Keyword Stats 2026-05-07 at 13_24_24_usa-country-only.csv"
    )
    out = (
        Path(sys.argv[2])
        if len(sys.argv) > 2
        else base / "keyword research" / "USA_Country_PLP_keywords_clustered.csv"
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
                "America (US)",
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
