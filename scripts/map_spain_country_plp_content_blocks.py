#!/usr/bin/env python3
"""
Map Spain Country PLP keywords to content blocks/slots from country-plp-country-example-def.html.

Reads Spain_Country_PLP_keywords_clustered.csv and writes Spain_Country_PLP_keywords_content_map.csv
(columns: Keyword … Tag, content_block_label, then metrics).
Taxonomy reference: keyword research/country_plp_spain_content_taxonomy.json.
"""

from __future__ import annotations

import csv
import re
import sys
from pathlib import Path


def read_clustered_rows(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        r = csv.DictReader(f)
        rows = list(r)
        return r.fieldnames or [], rows


# (block_id, block_label, slot_id or "", slot_label or "", compiled_regex)
# First match wins — order matters.
_RULES: list[tuple[str, str, str, str, re.Pattern[str]]] = [
    (
        "commercial_placeholder",
        "Featured tickets & tours (optional)",
        "",
        "",
        re.compile(
            r"\b(ticket(s)?|book(ing)?|guided tour|day tour|excursion|city pass|"
            r"sightseeing pass|skip.?the.?line)\b",
            re.I,
        ),
    ),
    (
        "faqs",
        "FAQs",
        "",
        "",
        re.compile(
            r"\b(how many days|first timer|first time|first visit|do i need|need a visa|"
            r"visa|schengen|passport|packing|insurance|what to bring|is spain safe|"
            r"safe to travel|tips before)\b",
            re.I,
        ),
    ),
    (
        "itinerary_picks",
        "Itinerary picks carousel",
        "",
        "",
        re.compile(
            r"\b(itinerary|itineraries|road trip|roadtrip|\d+\s*days in spain|\d+\s*day(s)?\b.*\bspain\b|"
            r"spain in \d+|one week in spain|two week|10 days|14 days|7 days|multi.?city|"
            r"north and south spain|andalusia tour|route across)\b",
            re.I,
        ),
    ),
    (
        "planning_spain",
        "Planning Spain (transport, seasons & routes)",
        "getting_around",
        "Getting around",
        re.compile(
            r"\b(train|renfe|high[- ]speed|ave\b|bus(es)?|flight(s)?|fly to|airport|"
            r"driving in spain|drive spain|car hire|rent a car|rental car|ferry|"
            r"getting around|public transport|metro\b)\b",
            re.I,
        ),
    ),
    (
        "planning_spain",
        "Planning Spain (transport, seasons & routes)",
        "trip_ideas",
        "Trip ideas",
        re.compile(
            r"\b(trip ideas|planning a trip|plan a trip|planning spain|organize|organise|"
            r"combine regions|which regions|north and south|city and beach|spain and portugal)\b",
            re.I,
        ),
    ),
    (
        "planning_spain",
        "Planning Spain (transport, seasons & routes)",
        "best_season",
        "Best season (planning depth)",
        re.compile(
            r"\b(by month|month by month|climate guide|seasonal guide|travel tips.*season|"
            r"season.*travel tips)\b",
            re.I,
        ),
    ),
    (
        "notable_attractions",
        "Notable tourist attractions carousel",
        "",
        "",
        re.compile(
            r"\b(attractions?\b|sightseeing|things to see|must see|must-see|landmarks?|"
            r"monuments?|historic sites|world heritage|unesco|tourist sites|tourist places|"
            r"visitor attractions)\b",
            re.I,
        ),
    ),
    (
        "city_hubs",
        "Best places to visit (city hubs carousel)",
        "",
        "",
        re.compile(
            r"\b(best cities|cities to visit|cities in spain|city break|places to visit|"
            r"places to go|places to travel|top places|where to go|holiday destinations|"
            r"vacation spots|destinations in spain|towns in spain|beautiful towns)\b",
            re.I,
        ),
    ),
    (
        "intro_line",
        "Intro cross-links strip",
        "",
        "",
        re.compile(
            r"\b(travel guide(s)?|spain guide\b.*\bguide\b|itineraries.*spain|spain itineraries)\b",
            re.I,
        ),
    ),
    (
        "country_summary",
        "Country summary (at a glance)",
        "quick_facts",
        "Quick facts",
        re.compile(
            r"\b(visa|schengen|currency|euro\b|language(s)?|speak spanish|entry requirement)\b",
            re.I,
        ),
    ),
    (
        "country_summary",
        "Country summary (at a glance)",
        "the_wallet",
        "The wallet",
        re.compile(
            r"\b(cheap|cheapest|budget|luxury|expensive|affordable|cost|costs|save money|deal)\b",
            re.I,
        ),
    ),
    (
        "country_summary",
        "Country summary (at a glance)",
        "sweet_spot",
        "Sweet spot",
        re.compile(
            r"\b(january|february|march|april|may|june|july|august|september|october|november|december)\b|"
            r"\b(winter|spring|summer|autumn|fall)\b.*\bspain\b|"
            r"\bspain\b.*\b(winter|spring|summer|autumn|fall)\b|"
            r"\b(best time to visit|when to visit|when to go|best month|weather|climate|"
            r"warmest|hottest|rainy|snow)\b",
            re.I,
        ),
    ),
    (
        "country_summary",
        "Country summary (at a glance)",
        "highlights",
        "Highlights",
        re.compile(
            r"\b(museum|museums|beach|beaches|islands?|coast|mountains?|hiking|architecture|"
            r"culture|heritage|history|food tour|wine|tapas|paella|flamenco|festivals?)\b",
            re.I,
        ),
    ),
    (
        "country_summary",
        "Country summary (at a glance)",
        "vibe",
        "Vibe",
        re.compile(
            r"\b(vibe|atmosphere|laid.back|romantic|family holiday|party|nightlife|"
            r"why visit|reasons to visit|what is spain like)\b",
            re.I,
        ),
    ),
    (
        "hero",
        "Hero & positioning",
        "",
        "",
        re.compile(
            r"^(visit spain|travel spain|spain travel|spain trip|trip to spain|holiday in spain|"
            r"vacation in spain|spain vacation)$",
            re.I,
        ),
    ),
]


_BLOCK_LABELS = {
    "hero": "Hero & positioning",
    "intro_line": "Intro cross-links strip",
    "country_summary": "Country summary (at a glance)",
    "city_hubs": "Best places to visit (city hubs carousel)",
    "notable_attractions": "Notable tourist attractions carousel",
    "planning_spain": "Planning Spain (transport, seasons & routes)",
    "itinerary_picks": "Itinerary picks carousel",
    "commercial_placeholder": "Featured tickets & tours (optional)",
    "faqs": "FAQs",
}


def assign_content_block_label(keyword: str) -> str:
    k = keyword.strip()
    for _bid, blabel, _sid, _slabel, rx in _RULES:
        if rx.search(k):
            return blabel
    return _BLOCK_LABELS["country_summary"]


def main() -> int:
    base = Path(__file__).resolve().parents[1]
    inp = (
        Path(sys.argv[1])
        if len(sys.argv) > 1
        else base / "keyword research" / "Spain_Country_PLP_keywords_clustered.csv"
    )
    out = (
        Path(sys.argv[2])
        if len(sys.argv) > 2
        else base / "keyword research" / "Spain_Country_PLP_keywords_content_map.csv"
    )

    fieldnames, rows = read_clustered_rows(inp)
    fn = [f for f in fieldnames if f]
    if "Tag" in fn:
        i = fn.index("Tag") + 1
        out_fields = fn[:i] + ["content_block_label"] + fn[i:]
    else:
        out_fields = fn + ["content_block_label"]

    out_rows: list[dict[str, str]] = []
    for row in rows:
        kw = (row.get("Keyword") or "").strip()
        cbl = assign_content_block_label(kw)
        merged = {**row, "content_block_label": cbl}
        out_rows.append(merged)

    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=out_fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(out_rows)

    print(f"Written {len(out_rows)} rows -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
