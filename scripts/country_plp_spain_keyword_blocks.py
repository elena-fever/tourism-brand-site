#!/usr/bin/env python3
"""
Spain runner: applies reusable rules from country_plp_classification_rules.py
to a Keyword Planner export and writes the Country PLP / City PDP CSV.

Usage:
  python country_plp_spain_keyword_blocks.py [<input.csv>] [<output.csv>]
"""

from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from country_plp_classification_rules import (
    DAY_TRIP_PAGE,
    OUT_COLUMNS,
    content_block_for_keyword,
    has_spain_connection,
    is_day_trip_keyword,
    norm,
    parse_planner_export,
    should_drop_keyword,
    tag_for_keyword,
)


def main() -> int:
    inp = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(
        r"c:\Users\FEVER\Downloads\Keyword Stats 2026-05-07 at 17_14_21.csv"
    )
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else (
        Path(__file__).resolve().parents[1]
        / "keyword research"
        / "Keyword Stats 2026-05-07 at 17_14_21_Spain_Country_PLP_blocks.csv"
    )

    header, rows = parse_planner_export(inp)

    def col(name: str) -> int:
        try:
            return header.index(name)
        except ValueError as e:
            raise KeyError(f"Missing column: {name}") from e

    i_kw = col("Keyword")
    pull_idx = [
        i_kw,
        col("Avg. monthly searches"),
        col("Three month change"),
        col("YoY change"),
        col("Competition"),
        *[col(f"Searches: {m} 2025") for m in ["Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]],
        col("Searches: Jan 2026"),
        col("Searches: Feb 2026"),
        col("Searches: Mar 2026"),
    ]

    out_rows: list[list[str]] = []
    skipped_rules = 0
    skipped_conn = 0

    for row in rows:
        if len(row) <= max(pull_idx):
            continue
        kw = row[i_kw].strip()
        if not kw:
            continue
        n = norm(kw)
        spaced = f" {n} "
        tokens_norm = set(re.findall(r"[\w'-]+", n))

        if should_drop_keyword(kw, spaced, tokens_norm):
            skipped_rules += 1
            continue

        if not has_spain_connection(kw, spaced):
            skipped_conn += 1
            continue

        tag = tag_for_keyword(kw)
        if is_day_trip_keyword(kw):
            page_type = DAY_TRIP_PAGE
            block = DAY_TRIP_PAGE
        else:
            page_type = "Country PLP"
            block = content_block_for_keyword(kw, country_display="Spain")

        vals = [row[j] for j in pull_idx]
        out_rows.append(
            [
                vals[0],
                page_type,
                "Spain",
                tag,
                block,
                *vals[1:],
            ]
        )

    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(OUT_COLUMNS)
        w.writerows(out_rows)

    print(f"Written {len(out_rows)} rows -> {out}")
    print(f"Skipped (rules): {skipped_rules}")
    print(f"Skipped (no Spain connection): {skipped_conn}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
