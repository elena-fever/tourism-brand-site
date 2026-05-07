#!/usr/bin/env python3
"""
Reusable Country PLP keyword classification rules (Spain-first defaults).

Import this module from country-specific runners (other countries: swap city tokens +
country regexes). See RULEBOOK_VERSION and exported helpers below.

This file is the single source of truth for regex priorities, exclusions, and block labels.
"""

from __future__ import annotations

import csv
import importlib.util
import re
import unicodedata
from pathlib import Path

RULEBOOK_VERSION = "2026-05-08"

# Ordered priority for content_block assignment (first logical branch wins in code).
RULEBOOK_BLOCK_PRIORITY: list[str] = [
    "Quick facts",
    "FAQs",
    "Country itineraries",
    "Planning · Getting around",
    "Planning · Getting around - City PDP",
    "Things to do in {country}",
    "Planning · Seasons",
    "Planning · Trip ideas",
    "Best places",
    "Tourist attractions",
    "Country destinations (H1)",
]

RULEBOOK_EXCLUSIONS: list[str] = [
    "Any 4-digit calendar year in keyword (19xx / 20xx)",
    "Inter-city transport legs (Spanish city↔city, explicit mode + A→B, or place+place+train/bus without ‘to’)",
    "Vacation packages (flight+hotel, villa+flight, all-inclusive, holiday packages)",
    "City/island + holidays / holidays-to-resort (non-country Spain)",
    "FAQ-shaped queries without Spain/España country anchor",
    "Hotel / hotels tokens",
    "City/island token + calendar month (EN/ES; includes “in may” for English May)",
]


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return s.lower()


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


def load_city_tokens_from_filter_script() -> frozenset[str]:
    """Spain: reuse TOKEN_EXCLUDE from filter_spain_country_keywords.py."""
    here = Path(__file__).resolve().parent / "filter_spain_country_keywords.py"
    spec = importlib.util.spec_from_file_location("filter_spain_country_keywords", here)
    if spec is None or spec.loader is None:
        return frozenset()
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return frozenset(getattr(mod, "TOKEN_EXCLUDE_N", set()))


_REGION_FOR_TRIP_IDEAS = frozenset(
    norm(x)
    for x in [
        "andalusia",
        "andalucia",
        "catalonia",
        "catalunya",
        "cataluna",
        "galicia",
        "basque country",
        "pais vasco",
        "navarra",
        "navarre",
        "aragon",
        "aragón",
        "extremadura",
        "cantabria",
        "asturias",
        "rioja",
        "la rioja",
        "castilla",
        "castile",
        "la mancha",
        "castilla la mancha",
        "castilla y leon",
        "castilla y león",
        "valencian community",
        "comunidad valenciana",
        "region de murcia",
        "región de murcia",
        "murcia region",
        "balearic",
        "balearics",
        "baleares",
        "canary islands",
        "canarias",
        "canaries",
        "mainland spain",
        "north spain",
        "south spain",
        "east spain",
        "west spain",
        "northern spain",
        "southern spain",
        "eastern spain",
        "western spain",
        "north of spain",
        "south of spain",
        "costa brava",
        "costa del sol",
        "costa blanca",
        "costa dorada",
        "costa verde",
        "costa tropical",
        "costa de la luz",
        "costa azahar",
        "costa calida",
        "pyrenees",
        "picos de europa",
        "iberian",
    ]
)

_ISLAND_RESORT_TOKENS = frozenset(
    norm(x)
    for x in [
        "tenerife",
        "lanzarote",
        "gran",
        "canaria",
        "canarias",
        "fuerteventura",
        "la palma",
        "la gomera",
        "el hierro",
        "mallorca",
        "majorca",
        "menorca",
        "formentera",
        "ibiza",
        "benidorm",
        "salou",
        "magaluf",
        "marbella",
        "torremolinos",
        "palma",
        "palmas",
    ]
)

_CITY_TOKENS_CACHE: frozenset[str] | None = None


def city_tokens() -> frozenset[str]:
    global _CITY_TOKENS_CACHE
    if _CITY_TOKENS_CACHE is None:
        raw = load_city_tokens_from_filter_script()
        _CITY_TOKENS_CACHE = frozenset(t for t in raw if t not in _REGION_FOR_TRIP_IDEAS and len(t) >= 3)
    return _CITY_TOKENS_CACHE


def things_to_do_block_label(country_display: str = "Spain") -> str:
    return f"Things to do in {country_display}"


_LANDMARK_PHRASES = [
    "sagrada familia",
    "park guell",
    "parc guell",
    "alhambra",
    "mezquita",
    "mezquita-catedral",
    "prado museum",
    "museo del prado",
    "museo thyssen",
    "reina sofia",
    "royal palace madrid",
    "alcazar",
    "alcázar",
    "camino de santiago",
    "teide",
    "montserrat",
    "guggenheim bilbao",
    "city of arts and sciences",
    "ciudad de las artes",
    "ibiza old town",
    "seville cathedral",
    "barcelona cathedral",
    "la pedrera",
    "casa batllo",
    "batlló",
    "camp nou",
    "bernabeu",
    "bernabéu",
    "burgos cathedral",
    "cuenca hanging houses",
]

_lm_alt = "|".join(
    sorted({re.escape(norm(p)) for p in _LANDMARK_PHRASES if p.strip()}, key=len, reverse=True)
)
_LANDMARK_RE = re.compile(_lm_alt) if _lm_alt else re.compile(r"$^")

_SPAIN_ANCHOR_RE = re.compile(
    r"\b(spain|spanish|espana|españa)\b",
    re.I | re.UNICODE,
)

_SPAIN_COUNTRY_ONLY_RE = _SPAIN_ANCHOR_RE

_YEAR_RE = re.compile(r"\b(19|20)\d{2}\b")

_HOTELS_RE = re.compile(r"\bhotels?\b", re.I)

_MONTH_MARKERS_RE = re.compile(
    r"\b(january|february|march|april|may|june|july|august|september|october|november|december|"
    r"enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|setiembre|octubre|noviembre|diciembre)\b",
    re.I,
)

_TRANSPORT_LEGS = re.compile(
    r"\b(train|trains|bus|buses|coach|coaches|flight|flights|plane|planes|renfe|ave\b|ferry|ferries|"
    r"railway|rail\b|metro\b|underground|subway|high[\s-]speed|transportation|transporting|transport\b|"
    r"transfers?\b|shuttle\b)\b",
    re.I,
)

_PAIR_ENDPOINT_SKIP = frozenset(
    norm(x)
    for x in [
        "spain",
        "spanish",
        "espana",
        "españa",
        "europe",
        "eu",
        "portugal",
        "france",
        "morocco",
        "uk",
        "england",
        "scotland",
        "ireland",
        "germany",
        "italy",
        "world",
        "home",
        "here",
        "there",
        "airport",
        "hotels",
        "hotel",
        "city",
        "town",
        "beach",
        "coast",
    ]
)


def _spanish_micro_destination_tokens() -> frozenset[str]:
    return city_tokens() | _ISLAND_RESORT_TOKENS


def _pair_endpoints_iter(normalized_keyword: str) -> list[tuple[str, str]]:
    n = normalized_keyword
    pairs: list[tuple[str, str]] = []
    pairs.extend(re.findall(r"\b([\w'-]{2,})\s+to\s+([\w'-]{2,})\b", n))
    pairs.extend(re.findall(r"\bfrom\s+([\w'-]{2,})\s+to\s+([\w'-]{2,})\b", n))
    return pairs


def _has_spanish_city_to_city_leg(keyword: str) -> bool:
    places = _spanish_micro_destination_tokens()
    for a, b in _pair_endpoints_iter(norm(keyword)):
        if a in _PAIR_ENDPOINT_SKIP or b in _PAIR_ENDPOINT_SKIP:
            continue
        if a in places and b in places:
            return True
    return False


def _has_inter_city_transport_leg(keyword: str) -> bool:
    if not _TRANSPORT_LEGS.search(keyword):
        return False
    for a, b in _pair_endpoints_iter(norm(keyword)):
        if a in _PAIR_ENDPOINT_SKIP or b in _PAIR_ENDPOINT_SKIP:
            continue
        return True
    return False


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
        "ferry",
        "ferries",
        "rail",
        "railway",
        "renfe",
        "ave",
    ]
)


def _has_spanish_place_pair_plus_transport_token(keyword: str) -> bool:
    """Catch 'granada seville bus', 'malaga ronda train' (no explicit 'to')."""
    toks = re.findall(r"[\w'-]+", norm(keyword))
    if len(toks) < 3:
        return False
    places = _spanish_micro_destination_tokens()
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


def _is_city_or_island_holidays_package(keyword: str, spaced_norm: str, tokens_norm: set[str]) -> bool:
    if "holidays" not in spaced_norm and "holiday" not in spaced_norm:
        return False

    n = norm(keyword)

    for m in re.finditer(r"\bholidays?\s+(?:in\s+)?to\s+([\w'-]+(?:\s+[\w'-]+){0,2})\b", n):
        tail = m.group(1).strip()
        tail_tokens = set(re.findall(r"[\w'-]+", tail))
        if tail_tokens & {"spain", "spanish", "espana", "españa"}:
            continue
        if tail_tokens & tokens_norm & (city_tokens() | _ISLAND_RESORT_TOKENS):
            return True
        if any(
            phrase in tail
            for phrase in (
                "gran canaria",
                "la palma",
                "la gomera",
                "el hierro",
                "palma de mallorca",
                "las palmas",
                "costa del sol",
                "costa brava",
                "costa blanca",
            )
        ):
            return True

    for m in re.finditer(r"\b([\w'-]+)\s+holidays?\b", n):
        head = m.group(1)
        if head in {"cheap", "luxury", "family", "summer", "winter", "last", "minute", "school", "package", "all"}:
            continue
        if head in city_tokens() or head in _ISLAND_RESORT_TOKENS:
            return True

    return False


_FAQ_SHAPE_RE = re.compile(
    r"(^|[\s,])(what|how|when|where|why|which|who|whom|whose|can i|could i|should i|do i|does |"
    r"is there|are there|qu[eé]|qui[eé]n|cu[aá]ndo|c[oó]mo|d[oó]nde|cu[aá]l|cu[aá]les|por qu[eé])(\s|$)|"
    r"[¿?]",
    re.I,
)

DAY_TRIP_PAGE = "City PDP - day trip"


def is_day_trip_keyword(keyword: str) -> bool:
    return bool(re.search(r"\bday\s+trips?\b", keyword, re.I))


def keyword_has_city_token(spaced_norm: str, tokens_norm: set[str]) -> bool:
    return bool(tokens_norm & city_tokens()) or bool(tokens_norm & _ISLAND_RESORT_TOKENS)


def should_drop_city_and_month(keyword: str, spaced_norm: str, tokens_norm: set[str]) -> bool:
    if not _MONTH_MARKERS_RE.search(keyword):
        return False
    return keyword_has_city_token(spaced_norm, tokens_norm)


def should_drop_keyword(keyword: str, spaced_norm: str, tokens_norm: set[str]) -> bool:
    raw = keyword.strip()
    if not raw:
        return True
    if _YEAR_RE.search(raw):
        return True
    if _HOTELS_RE.search(raw):
        return True
    if should_drop_city_and_month(raw, spaced_norm, tokens_norm):
        return True
    if _PACKAGE_OR_FLIGHT_HOTEL_RE.search(raw):
        return True
    if not is_day_trip_keyword(raw):
        if (
            _has_inter_city_transport_leg(raw)
            or _has_spanish_city_to_city_leg(raw)
            or _has_spanish_place_pair_plus_transport_token(raw)
        ):
            return True
    if _is_city_or_island_holidays_package(raw, spaced_norm, tokens_norm):
        return True
    if _FAQ_SHAPE_RE.search(raw) and not _SPAIN_COUNTRY_ONLY_RE.search(raw):
        return True
    return False


def has_spain_connection(keyword: str, spaced_norm: str) -> bool:
    if _SPAIN_ANCHOR_RE.search(keyword):
        return True
    if "spain" in spaced_norm or "spanish" in spaced_norm or "espana" in spaced_norm:
        return True
    toks = set(re.findall(r"[\w'-]+", spaced_norm))
    if toks & city_tokens():
        return True
    if any(r in spaced_norm for r in [f" {x} " for x in _REGION_FOR_TRIP_IDEAS if len(x) > 4]):
        return True
    islands = (
        "tenerife",
        "lanzarote",
        "gran canaria",
        "fuerteventura",
        "la palma",
        "la gomera",
        "el hierro",
        "mallorca",
        "majorca",
        "menorca",
        "formentera",
        "ibiza",
    )
    for isl in islands:
        if f" {isl} " in spaced_norm:
            return True
    return False


# --- Tag clusters (first match wins) ---
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
            r"\b(flight|flights|fly to|train|trains|renfe|high-speed rail|ferry|ferries|"
            r"car hire|hire car|rent a car|rental car|driving in|drive around|bus tour|public transport|transportation|"
            r"taxi|metro\b|railway)\b",
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
            r"\b(north spain|south spain|east spain|west spain|northern spain|southern spain|"
            r"eastern spain|western spain|north of spain|south of spain)\b",
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


def tag_for_keyword(keyword: str) -> str:
    for label, rx in _TAG_RULES:
        if rx.search(keyword):
            return label
    return "Places & destinations"


_FAQ_RE = _FAQ_SHAPE_RE

_QUICK_FACTS_RE = re.compile(
    r"\b(currency|currencies|exchange rate|money in spain|languages?\b|language in spain|language of spain|"
    r"official language|speak spanish|visa|schengen|passport|entry requirement)\b",
    re.I,
)

_ITINERARY_RE = re.compile(
    r"\b(itinerary|itineraries|road trip|roadtrip|multi.?city|route(s)?\b.*\b(spain|spanish)\b|"
    r"\b(spain|spanish)\b.*\broute(s)?\b|"
    r"\d+\s*days in spain|spain in \d+|one week in spain|two weeks in spain|"
    r"10 days in spain|14 days in spain|7 days in spain|north and south spain)\b",
    re.I,
)

_GETTING_AROUND_RE = re.compile(
    r"\b(train|trains|renfe|ave\b|high[\s-]speed|flight|flights|plane|airport|bus\b|buses|coach|"
    r"car hire|hire car|rent a car|rental car|driving in spain|drive spain|taxi|"
    r"metro\b|underground|subway|public transport|transportation|transport in spain|ferry|ferries|railway|rail\b)\b",
    re.I,
)

_SEASONS_RE = re.compile(
    r"\b(weather|climate|temperature|season(s)?\b|spring|summer|autumn|fall|winter|"
    r"january|february|march|april|may|june|july|august|september|october|november|december|"
    r"when to visit|when to go|best time to visit|best month)\b",
    re.I,
)

_TRIP_IDEAS_REGION_RE = re.compile(
    r"\b(north spain|south spain|east spain|west spain|northern spain|southern spain|"
    r"eastern spain|western spain|north of spain|south of spain|mainland spain|central spain|"
    r"multiple regions|combine regions|region(s)? of spain|from .* to .*\b(spain|spanish)\b)\b",
    re.I,
)


def _has_region_trip_token(spaced_norm: str, tokens_norm: set[str]) -> bool:
    if bool(_TRIP_IDEAS_REGION_RE.search(spaced_norm.strip())):
        return True
    for r in _REGION_FOR_TRIP_IDEAS:
        if len(r) < 5:
            continue
        if f" {r} " in spaced_norm:
            return True
    ccaa = {"andalusia", "andalucia", "catalonia", "galicia", "extremadura", "cantabria", "asturias", "aragon", "navarra"}
    return bool(ccaa & tokens_norm)


_THINGS_PHRASE_RE = re.compile(
    r"\b(things to do|what to do|stuff to do|fun things(\s+to\s+do)?)\b",
    re.I,
)

_FOOD_CULTURE_EVENTS_RE = re.compile(
    r"\b(food|foods|wine|wines|tapas|paella|gastronomy|culinary|cuisine|dishes|restaurants?|cafes?|cafés?|"
    r"eat in|eating in|drinks?|breakfast|brunch|dinner|lunch|markets?\b|"
    r"festival|festivals|fiesta|fiestas|carnival|culture|cultural|heritage|traditions?|"
    r"events?\b|concerts?|live music|shows?\b|bullfighting|flamenco)\b",
    re.I,
)

_BLOCK_GETTING_AROUND_CITY = "Planning · Getting around - City PDP"
_BLOCK_GETTING_AROUND_COUNTRY = "Planning · Getting around"

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


def content_block_for_keyword(keyword: str, *, country_display: str = "Spain") -> str:
    raw_kw = keyword.strip()
    n = norm(raw_kw)
    spaced = f" {n} "
    tokens_norm = set(re.findall(r"[\w'-]+", n, flags=re.UNICODE))
    things_label = things_to_do_block_label(country_display)

    if _QUICK_FACTS_RE.search(raw_kw):
        return "Quick facts"
    if _FAQ_RE.search(raw_kw) and _SPAIN_COUNTRY_ONLY_RE.search(raw_kw):
        return "FAQs"
    if _ITINERARY_RE.search(raw_kw):
        return "Country itineraries"

    if _GETTING_AROUND_RE.search(raw_kw):
        if keyword_has_city_token(spaced, tokens_norm) and not _SPAIN_COUNTRY_ONLY_RE.search(raw_kw):
            return _BLOCK_GETTING_AROUND_CITY
        return _BLOCK_GETTING_AROUND_COUNTRY

    # Country-scoped “things to do” + food/culture/events (requires Spain as country in keyword).
    if _SPAIN_COUNTRY_ONLY_RE.search(raw_kw) and (
        _THINGS_PHRASE_RE.search(raw_kw) or _FOOD_CULTURE_EVENTS_RE.search(raw_kw)
    ):
        return things_label

    if _SEASONS_RE.search(raw_kw):
        return "Planning · Seasons"
    if _has_region_trip_token(spaced, tokens_norm):
        return "Planning · Trip ideas"

    if keyword_has_city_token(spaced, tokens_norm) and _CITY_GUIDE_RE.search(raw_kw):
        return "Best places"

    if _LANDMARK_RE.search(n) or _ATTRACTION_WORD_RE.search(raw_kw):
        return "Tourist attractions"

    if _BEST_PLACES_WORD_RE.search(raw_kw) or keyword_has_city_token(spaced, tokens_norm):
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
