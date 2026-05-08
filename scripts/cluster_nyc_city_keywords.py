#!/usr/bin/env python3
"""Cluster NYC City PDP keywords (attractions, boroughs, neighbourhoods)."""

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
        "Major sights & landmarks",
        re.compile(
            r"\b(statue of liberty|ellis island|empire state building|empire state observation|"
            r"top of the rock|rockefeller center|one world observatory|one world trade|freedom tower|"
            r"summit one vanderbilt|summit ov|the edge|hudson yards observation|"
            r"vessel\b|flatiron building|chrysler building|grand central terminal|grand central station|"
            r"times square|washington square park|brooklyn bridge|manhattan bridge|williamsburg bridge|"
            r"9/11 memorial|september 11 memorial|national september 11|911 memorial|ground zero|"
            r"wall street|charging bull|bowling green)\b",
            re.I,
        ),
    ),
    (
        # Boroughs + districts → one Tag (works for any city when you replicate this pattern)
        "Neighbourhoods",
        re.compile(
            r"\b(manhattan|brooklyn|queens|bronx|staten island|staten|"
            r"harlem|soho|tribeca|williamsburg|bushwick|astoria|dumbo|long island city|"
            r"east village|west village|lower east side|upper east side|upper west side|"
            r"chinatown|little italy|chelsea|flatiron district|meatpacking|greenwich village|"
            r"financial district|murray hill|gramercy|noho|nolita|nomad|midtown|uptown|"
            r"washington heights|inwood|ridgewood|flushing|jackson heights|sunset park|crown heights|"
            r"park slope|red hook|bay ridge|cobble hill|carroll gardens|greenpoint|"
            r"fordham|city island)\b",
            re.I,
        ),
    ),
    (
        "Museums & culture",
        re.compile(
            r"\b(moma\b|metropolitan museum|met museum|\bthe met\b|guggenheim|whitney museum|"
            r"american museum of natural history|natural history museum|\bamnh\b|frick collection|"
            r"brooklyn museum|tenement museum|cooper hewitt|morgan library|"
            r"intrepid museum|911 museum|titanic museum)\b",
            re.I,
        ),
    ),
    (
        "Parks & waterfront",
        re.compile(
            r"\b(central park|high line|highline|battery park|brooklyn bridge park|riverside park|"
            r"prospect park|domino park|little island|chelsea piers|battery park city)\b",
            re.I,
        ),
    ),
    (
        "Broadway & live shows",
        re.compile(
            r"\b(broadway\b|broadway show|broadway ticket|broadway musical|off broadway|tkts|radio city|rockettes)\b",
            re.I,
        ),
    ),
    (
        "Cruises & ferries",
        re.compile(
            r"\b(circle line|staten island ferry|ny waterway|manhattan cruise|harbor cruise|"
            r"hudson cruise|sightseeing cruise)\b",
            re.I,
        ),
    ),
    (
        "Passes & bundled tickets",
        re.compile(
            r"\b(explorer pass|citypass|new york pass|nyc pass|sightseeing pass|flex pass|"
            r"go city|turbo pass|attractions pass|sightseeing flex)\b",
            re.I,
        ),
    ),
    (
        "Budget & free",
        re.compile(r"\b(cheap|free\b|budget|affordable|deal)\b", re.I),
    ),
    (
        "Seasonality & timing",
        re.compile(
            r"\b(january|february|march|april|may|june|july|august|september|october|november|december)\b|"
            r"\b(winter|spring|summer|autumn|fall)\b|"
            r"\b(when to visit|best time)\b",
            re.I,
        ),
    ),
    (
        "Nightlife & events",
        re.compile(
            r"\b(events\b|nightlife|club|rooftop bar|bar crawl|concert|festival)\b",
            re.I,
        ),
    ),
    (
        "Food & dining",
        re.compile(
            r"\b(food tour|restaurant|brunch|pizza|bagel|street food|dining|eat in nyc|food hall)\b",
            re.I,
        ),
    ),
    (
        "Shopping",
        re.compile(r"\b(shopping|mall|soho shopping|fifth avenue shopping|outlet)\b", re.I),
    ),
    (
        "Stay & accommodation",
        re.compile(
            r"\b(hotel|hotels|hostel|airbnb|where to stay|lodging)\b",
            re.I,
        ),
    ),
    (
        "Getting around",
        re.compile(
            r"\b(subway|metro card|metrocard|metro\b|uber|taxi|yellow cab|hop on hop off|bus tour|"
            r"jfk\b|laguardia|newark airport|etrain)\b",
            re.I,
        ),
    ),
    (
        "Activities & experiences",
        re.compile(r"\b(things to do|what to do|activities|experiences|fun things)\b", re.I),
    ),
    (
        "Sightseeing & attractions (general)",
        re.compile(
            r"\b(sightseeing|tourist attraction|attractions|must see|must-see|things to see|"
            r"places to see|top sights|guided tour|walking tour)\b",
            re.I,
        ),
    ),
]


def cluster_for_keyword(keyword: str) -> str:
    k = keyword.strip()
    for label, rx in _CLUSTER_RULES:
        if rx.search(k):
            return label
    return "NYC discovery & planning"


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
        else base / "keyword research" / "Keyword Stats 2026-05-07 at 13_33_59_nyc-city-only.csv"
    )
    out = (
        Path(sys.argv[2])
        if len(sys.argv) > 2
        else base / "keyword research" / "NYC_City_PDP_keywords_clustered.csv"
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
        out_rows.append([vals[0], "City PDP", "New York", tag, *vals[1:]])

    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(OUT_COLUMNS)
        w.writerows(out_rows)

    print(f"Written {len(out_rows)} rows -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
