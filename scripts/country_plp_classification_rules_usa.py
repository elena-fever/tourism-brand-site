#!/usr/bin/env python3
"""
USA Country PLP keyword classification — mirrors final Spain rulebook structure.

Uses place tokens from filter_usa_country_keywords.py (states + major cities + helpers).
"""

from __future__ import annotations

import csv
import importlib.util
import re
import unicodedata
from pathlib import Path

RULEBOOK_VERSION_USA = "2026-05-08"


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return s.lower()


_YEAR_RE = re.compile(r"\b(19|20)\d{2}\b")
_HOTELS_RE = re.compile(r"\bhotels?\b", re.I)

_MONTH_MARKERS_RE = re.compile(
    r"\b(january|february|march|april|may|june|july|august|september|october|november|december|"
    r"enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|setiembre|octubre|noviembre|diciembre)\b",
    re.I,
)

_TRANSPORT_LEGS = re.compile(
    r"\b(train|trains|bus|buses|coach|coaches|flight|flights|plane|planes|ferry|ferries|"
    r"railway|rail\b|subway|metro\b|high[\s-]speed|transportation|transporting|transport\b|"
    r"transfers?\b|shuttle\b|amtrak\b)\b",
    re.I,
)

_TRANSPORT_MODE_TOKENS = frozenset(
    norm(x)
    for x in [
        "train",
        "trains",
        "bus",
        "buses",
        "coach",
        "coaches",
        "flight",
        "flights",
        "metro",
        "subway",
        "ferry",
        "ferries",
        "rail",
        "railway",
        "amtrak",
    ]
)

_PAIR_ENDPOINT_SKIP_US = frozenset(
    norm(x)
    for x in [
        "united",
        "states",
        "usa",
        "america",
        "u.s.",
        "us",
        "country",
        "world",
        "home",
        "here",
        "there",
        "airport",
        "hotel",
        "hotels",
        "city",
        "town",
        "beach",
        "coast",
        "canada",
        "mexico",
        "europe",
        "uk",
        "france",
        "worldwide",
    ]
)


def read_text_smart(path: Path) -> str:
    raw = path.read_bytes()
    if raw.startswith(b"\xff\xfe"):
        return raw.decode("utf-16-le")
    if raw.startswith(b"\xfe\xff"):
        return raw.decode("utf-16-be")
    if raw.startswith(b"\xef\xbb\xbf"):
        return raw.decode("utf-8-sig")
    if len(raw) >= 2 and raw[1::2] == b"\x00" * (len(raw) // 2):
        return raw.decode("utf-16-le")
    return raw.decode("utf-8", errors="replace")


def load_usa_filter_module():
    here = Path(__file__).resolve().parent / "filter_usa_country_keywords.py"
    spec = importlib.util.spec_from_file_location("filter_usa_country_keywords", here)
    if spec is None or spec.loader is None:
        raise RuntimeError("Cannot load filter_usa_country_keywords.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_USA_FILTER = load_usa_filter_module()
_USA_PLACE_TOKENS: frozenset[str] = frozenset(norm(t) for t in getattr(_USA_FILTER, "_TOKEN_EXCLUDE"))

_USA_RESORT_EXTRA = frozenset(
    norm(x)
    for x in [
        "oahu",
        "maui",
        "kauai",
        "honolulu",
        "waikiki",
        "vegas",
    ]
)


def usa_micro_destination_tokens() -> frozenset[str]:
    return _USA_PLACE_TOKENS | _USA_RESORT_EXTRA


_BAD_AMERICA = re.compile(r"\b(latin|south|central|north)\s+america\b", re.I)

_USA_COUNTRY_ANCHOR_RE = re.compile(
    r"\b(united\s+states|usa|u\.s\.a\.?)\b|\bu\.s\.(?![a-z])\b|\bamerica\b|"
    r"\b(in|to|across|around|throughout|from|within|outside|for)\s+the\s+us\b|\bthe\s+us\b|"
    r"\b(in|to|across|around|throughout|within|outside|for)\s+us\b|\baround\s+the\s+states\b|"
    r"\bin\s+the\s+states\b|\bamerican\b",
    re.I,
)


def has_usa_anchor_keyword(keyword: str) -> bool:
    if _BAD_AMERICA.search(keyword):
        return False
    nk = norm(keyword)
    if "canada" in nk:
        return False
    if "mexico" in nk and "new mexico" not in nk:
        return False
    return bool(_USA_FILTER.has_usa_anchor(keyword))


def has_usa_connection(keyword: str, spaced_norm: str) -> bool:
    if has_usa_anchor_keyword(keyword):
        return True
    toks = set(re.findall(r"[\w'-]+", spaced_norm))
    if toks & usa_micro_destination_tokens():
        return True
    return False


_FAQ_SHAPE_RE = re.compile(
    r"(^|[\s,])(what|how|when|where|why|which|who|whom|whose|can i|could i|should i|do i|does |"
    r"is there|are there)(\s|$)|[¿?]",
    re.I,
)

DAY_TRIP_PAGE = "City PDP - day trip"


def is_day_trip_keyword(keyword: str) -> bool:
    return bool(re.search(r"\bday\s+trips?\b", keyword, re.I))


def keyword_has_us_place(spaced_norm: str, tokens_norm: set[str]) -> bool:
    return bool(tokens_norm & usa_micro_destination_tokens())


def _pair_endpoints_iter(normalized_keyword: str) -> list[tuple[str, str]]:
    n = normalized_keyword
    pairs: list[tuple[str, str]] = []
    pairs.extend(re.findall(r"\b([\w'-]{2,})\s+to\s+([\w'-]{2,})\b", n))
    pairs.extend(re.findall(r"\bfrom\s+([\w'-]{2,})\s+to\s+([\w'-]{2,})\b", n))
    return pairs


def _has_usa_place_pair_leg(keyword: str) -> bool:
    places = usa_micro_destination_tokens()
    for a, b in _pair_endpoints_iter(norm(keyword)):
        if a in _PAIR_ENDPOINT_SKIP_US or b in _PAIR_ENDPOINT_SKIP_US:
            continue
        if a in places and b in places:
            return True
    return False


def _has_inter_city_transport_leg(keyword: str) -> bool:
    if not _TRANSPORT_LEGS.search(keyword):
        return False
    for a, b in _pair_endpoints_iter(norm(keyword)):
        if a in _PAIR_ENDPOINT_SKIP_US or b in _PAIR_ENDPOINT_SKIP_US:
            continue
        return True
    return False


def _has_place_pair_plus_transport_token(keyword: str) -> bool:
    toks = re.findall(r"[\w'-]+", norm(keyword))
    if len(toks) < 3:
        return False
    places = usa_micro_destination_tokens()
    for i in range(len(toks) - 2):
        a, b, c = toks[i], toks[i + 1], toks[i + 2]
        if a in places and b in places and c in _TRANSPORT_MODE_TOKENS:
            return True
        if a in _TRANSPORT_MODE_TOKENS and b in places and c in places:
            return True
    return False


_PACKAGE_OR_FLIGHT_HOTEL_RE = re.compile(
    r"\b(all[\s-]?inclusive)\b|"
    r"\b(flights?\s+and\s+hotel|hotel\s+and\s+flights?|flights?\s+and\s+accommodation|"
    r"accommodation\s+and\s+flights?)\b|"
    r"\b(holiday\s+packages?|package\s+holidays?|packages?\s+holiday)\b|"
    r"\bvilla\b.*\bflights?\b|\bflights?\b.*\bvilla\b|"
    r"\bflights?\s+.*\bhotel\b|\bhotel\b.*\bflights?\b",
    re.I,
)


def _usa_country_tail_tokens() -> frozenset[str]:
    return frozenset(
        norm(x)
        for x in [
            "united states",
            "usa",
            "america",
            "us",
            "states",
        ]
    )


def _is_place_holidays_package_us(keyword: str, spaced_norm: str, tokens_norm: set[str]) -> bool:
    if "holidays" not in spaced_norm and "holiday" not in spaced_norm:
        return False
    places = usa_micro_destination_tokens()
    n = norm(keyword)

    tail_skip = _usa_country_tail_tokens()

    for m in re.finditer(r"\bholidays?\s+(?:in\s+)?to\s+([\w'-]+(?:\s+[\w'-]+){0,3})\b", n):
        tail = m.group(1).strip()
        tail_tokens = set(re.findall(r"[\w'-]+", tail))
        tail_join = tail.replace(" ", "")
        if tail_tokens & tail_skip or "unitedstates" in tail_join:
            continue
        if tail_tokens & tokens_norm & places:
            return True

    for m in re.finditer(r"\b([\w'-]+)\s+holidays?\b", n):
        head = m.group(1)
        if head in {"cheap", "luxury", "family", "summer", "winter", "last", "minute", "school", "package", "all"}:
            continue
        if head in places:
            return True

    return False


def should_drop_keyword_usa(keyword: str, spaced_norm: str, tokens_norm: set[str]) -> bool:
    raw = keyword.strip()
    if not raw:
        return True
    if _YEAR_RE.search(raw):
        return True
    if _HOTELS_RE.search(raw):
        return True
    if _MONTH_MARKERS_RE.search(raw) and keyword_has_us_place(spaced_norm, tokens_norm):
        return True
    if _PACKAGE_OR_FLIGHT_HOTEL_RE.search(raw):
        return True
    if not is_day_trip_keyword(raw):
        if _has_inter_city_transport_leg(raw) or _has_usa_place_pair_leg(raw) or _has_place_pair_plus_transport_token(raw):
            return True
    if _is_place_holidays_package_us(raw, spaced_norm, tokens_norm):
        return True
    if _FAQ_SHAPE_RE.search(raw) and not _USA_COUNTRY_ANCHOR_RE.search(raw):
        return True
    return False


# --- Tags (USA regional tweak) ---
_TAG_RULES: list[tuple[str, re.Pattern[str]]] = [
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
        "Food & drink",
        re.compile(
            r"\b(food|foods|wine|bbq|barbecue|gastronomy|culinary|restaurant|restaurants|eat in|eating in|drinks)\b",
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
            r"\b(beach|beaches|seaside|coastal|seafront|sunbathe|swimming|ocean)\b",
            re.I,
        ),
    ),
    (
        "Nature & outdoors",
        re.compile(
            r"\b(national park|hiking|trek|countryside|rural|scenery|scenic|mountains|outdoor)\b",
            re.I,
        ),
    ),
    (
        "Activities & experiences",
        re.compile(r"\b(things to do|what to do|activities|experiences|fun things)\b", re.I),
    ),
    (
        "Sightseeing & landmarks",
        re.compile(
            r"\b(sightseeing|things to see|must see|must-see|must visit|landmarks?|monuments?|"
            r"tourist attractions?\b|attractions?\b|visitor attractions|historic sites)\b",
            re.I,
        ),
    ),
    (
        "Transport & getting around",
        re.compile(
            r"\b(flight|flights|fly to|train|trains|high-speed rail|ferry|ferries|"
            r"car hire|hire car|rent a car|rental car|driving in|drive around|bus tour|public transport|transportation|"
            r"taxi|metro\b|railway|amtrak)\b",
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
            r"\b(itinerary|itineraries|road trip|roadtrip|driving tour|routes?\b|multi.?city|"
            r"one week|two week|three week|10 days|14 days|7 days|\d+\s*days in)\b",
            re.I,
        ),
    ),
    (
        "Regional exploration",
        re.compile(
            r"\b(northeast|southwest|northwest|southeast|midwest|west coast|east coast|sun belt|deep south|"
            r"new england|great plains|four corners|pacific northwest|gulf coast)\b",
            re.I,
        ),
    ),
    (
        "Urban destinations",
        re.compile(r"\b(cities\b|city\b|towns\b|town\b|city break|urban)\b", re.I),
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
        "Practical planning",
        re.compile(
            r"\b(tips|travel guide|guide to|safety|packing|first time|first timers|reddit|checklist|what to know)\b",
            re.I,
        ),
    ),
]


def tag_for_keyword_usa(keyword: str) -> str:
    for label, rx in _TAG_RULES:
        if rx.search(keyword):
            return label
    return "Places & destinations"


_QUICK_FACTS_US = re.compile(
    r"\b(currency|currencies|exchange rate|dollar(s)?\b|usd\b|languages?\b|english language|official language|"
    r"visa|esta\b|passport|entry requirement)\b",
    re.I,
)

_ITINERARY_US = re.compile(
    r"\b(itinerary|itineraries|road trip|roadtrip|multi.?city)\b|"
    r"\broute(s)?\b.*\b(united states|usa|u\.s\.|america)\b|"
    r"\b(united states|usa|u\.s\.|america)\b.*\broute(s)?\b|"
    r"\d+\s*days in (the\s+)?(usa|us\b|united states)\b|"
    r"\b(usa|us|united states)\s+in\s+\d+\b|"
    r"\bone week in (the\s+)?(usa|us\b|united states)\b|"
    r"\btwo weeks in (the\s+)?(usa|us\b|united states)\b|"
    r"\b(10|14|7)\s+days in (the\s+)?(usa|us\b|united states)\b",
    re.I,
)

_GETTING_AROUND_US = re.compile(
    r"\b(train|trains|amtrak|high[\s-]speed|flight|flights|plane|airport|bus\b|buses|coach|"
    r"car hire|hire car|rent a car|rental car|driving in (the\s+)?(usa|us\b|united states)|"
    r"drive (the\s+)?(usa|us\b)|taxi|subway|metro\b|public transport|transportation|"
    r"transport in (the\s+)?(usa|us\b|united states)|ferry|ferries|railway|rail\b)\b",
    re.I,
)

_SEASONS_RE = re.compile(
    r"\b(weather|climate|temperature|season(s)?\b|spring|summer|autumn|fall|winter|"
    r"january|february|march|april|may|june|july|august|september|october|november|december|"
    r"when to visit|when to go|best time to visit|best month)\b",
    re.I,
)

_TRIP_IDEAS_US_RE = re.compile(
    r"\b(northeast|southwest|northwest|southeast|midwest|west coast|east coast|cross.country|cross-country|"
    r"coast to coast|multiple states|several states|from .* to .*\b(united states|usa|america)\b)\b",
    re.I,
)

_US_STATE_NAMES = frozenset(
    norm(x)
    for x in [
        "alabama",
        "alaska",
        "arizona",
        "arkansas",
        "california",
        "colorado",
        "connecticut",
        "delaware",
        "florida",
        "georgia",
        "hawaii",
        "idaho",
        "illinois",
        "indiana",
        "iowa",
        "kansas",
        "kentucky",
        "louisiana",
        "maine",
        "maryland",
        "massachusetts",
        "michigan",
        "minnesota",
        "mississippi",
        "missouri",
        "montana",
        "nebraska",
        "nevada",
        "new hampshire",
        "new jersey",
        "new mexico",
        "new york",
        "north carolina",
        "north dakota",
        "ohio",
        "oklahoma",
        "oregon",
        "pennsylvania",
        "rhode island",
        "south carolina",
        "south dakota",
        "tennessee",
        "texas",
        "utah",
        "vermont",
        "virginia",
        "washington",
        "west virginia",
        "wisconsin",
        "wyoming",
    ]
)


def _has_region_trip_token_us(spaced_norm: str, tokens_norm: set[str]) -> bool:
    if bool(_TRIP_IDEAS_US_RE.search(spaced_norm.strip())):
        return True
    states_hit = sum(1 for s in _US_STATE_NAMES if f" {s} " in spaced_norm)
    return states_hit >= 2


_THINGS_PHRASE_RE = re.compile(
    r"\b(things to do|what to do|stuff to do|fun things(\s+to\s+do)?)\b",
    re.I,
)

_FOOD_CULTURE_EVENTS_RE = re.compile(
    r"\b(food|foods|wine|wines|bbq|barbecue|gastronomy|culinary|cuisine|dishes|restaurants?|cafes?|cafés?|"
    r"eat in|eating in|drinks?|breakfast|brunch|dinner|lunch|markets?\b|"
    r"festival|festivals|carnival|culture|cultural|heritage|traditions?|"
    r"events?\b|concerts?|live music|shows?\b)\b",
    re.I,
)

_BLOCK_GETTING_AROUND_CITY = "Planning · Getting around - City PDP"
_BLOCK_GETTING_AROUND_COUNTRY = "Planning · Getting around"

_US_LANDMARK_ALT = "|".join(
    sorted(
        {
            re.escape(norm(p))
            for p in [
                "statue of liberty",
                "grand canyon",
                "yellowstone",
                "yosemite",
                "golden gate bridge",
                "times square",
                "national mall",
                "white house",
                "mount rushmore",
                "disney world",
                "disneyland",
            ]
            if p.strip()
        },
        key=len,
        reverse=True,
    )
)
_LANDMARK_US_RE = re.compile(_US_LANDMARK_ALT) if _US_LANDMARK_ALT else re.compile(r"$^")

_ATTRACTION_WORD_RE = re.compile(
    r"\b(attractions?\b|tourist attractions?|visitor attractions?|sightseeing|things to see|"
    r"must see|must-see|landmarks?|monuments?|historic sites|world heritage|unesco|tourist sites)\b",
    re.I,
)

_CITY_GUIDE_RE = re.compile(
    r"\b(things to do|what to do|places to visit|places to go|places to see|where to go in)\b",
    re.I,
)

_BEST_PLACES_WORD_RE = re.compile(
    r"\b(cities\b|city break\b|spots\b|vacation spots|best cities|towns\b|villages\b|beautiful towns)\b|"
    r"\b(places to visit|place to visit|places to go|place to go|places to travel|places to see|where to go|top places|best places)\b",
    re.I,
)


def things_to_do_block_label_usa() -> str:
    return "Things to do in United States"


def content_block_for_keyword_usa(keyword: str) -> str:
    raw_kw = keyword.strip()
    n = norm(raw_kw)
    spaced = f" {n} "
    tokens_norm = set(re.findall(r"[\w'-]+", n, flags=re.UNICODE))
    things_label = things_to_do_block_label_usa()

    if _QUICK_FACTS_US.search(raw_kw):
        return "Quick facts"
    if _FAQ_SHAPE_RE.search(raw_kw) and _USA_COUNTRY_ANCHOR_RE.search(raw_kw):
        return "FAQs"
    if _ITINERARY_US.search(raw_kw):
        return "Country itineraries"

    if _GETTING_AROUND_US.search(raw_kw):
        if keyword_has_us_place(spaced, tokens_norm) and not _USA_COUNTRY_ANCHOR_RE.search(raw_kw):
            return _BLOCK_GETTING_AROUND_CITY
        return _BLOCK_GETTING_AROUND_COUNTRY

    if _USA_COUNTRY_ANCHOR_RE.search(raw_kw) and (
        _THINGS_PHRASE_RE.search(raw_kw) or _FOOD_CULTURE_EVENTS_RE.search(raw_kw)
    ):
        return things_label

    if _SEASONS_RE.search(raw_kw):
        return "Planning · Seasons"
    if _has_region_trip_token_us(spaced, tokens_norm):
        return "Planning · Trip ideas"

    if keyword_has_us_place(spaced, tokens_norm) and _CITY_GUIDE_RE.search(raw_kw):
        return "Best places"

    if _LANDMARK_US_RE.search(n) or _ATTRACTION_WORD_RE.search(raw_kw):
        return "Tourist attractions"

    if _BEST_PLACES_WORD_RE.search(raw_kw) or keyword_has_us_place(spaced, tokens_norm):
        return "Best places"

    return "Country destinations (H1)"


def parse_planner_export(path: Path) -> tuple[list[str], list[list[str]]]:
    text = read_text_smart(path)
    lines = text.splitlines()
    if len(lines) < 4:
        raise ValueError("File too short")

    header_idx = None
    for i, line in enumerate(lines[:8]):
        if line.startswith("\ufeff"):
            line = line.lstrip("\ufeff")
        if line.startswith("Keyword\t") or line.split("\t", 1)[0].strip() == "Keyword":
            header_idx = i
            break
    if header_idx is None:
        raise ValueError("Could not locate Keyword header row")

    header_line = lines[header_idx].lstrip("\ufeff")
    header = next(csv.reader([header_line], delimiter="\t"))
    reader = csv.reader(lines[header_idx + 1 :], delimiter="\t")
    rows: list[list[str]] = []
    for row in reader:
        if row and any(cell.strip() for cell in row):
            rows.append(row)
    return header, rows


OUT_COLUMNS = [
    "Keyword",
    "Page type",
    "Location",
    "Tag",
    "content_block",
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
