#!/usr/bin/env python3
"""Merge Barcelona Keyword Planner exports → City PDP clustered CSV (Tag + content_block)."""

from __future__ import annotations

import csv
import json
import re
import sys
import unicodedata
from pathlib import Path

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


def norm_kw(s: str) -> str:
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.lower().strip()
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"\btransportation\b", "transport", s)
    s = s.replace("barcelone", "barcelona")
    s = re.sub(r"\bbarca\b", "barcelona", s)
    return s


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


def read_rows(path: Path) -> tuple[list[str], list[list[str]]]:
    text = read_text_smart(path)
    lines = text.splitlines()
    if len(lines) < 4:
        raise ValueError(f"CSV too short: {path}")
    header_line = lines[2]
    header = [c.strip().strip("\ufeff") for c in next(csv.reader([header_line], delimiter="\t"))]
    reader = csv.reader(lines[3:], delimiter="\t")
    rows: list[list[str]] = []
    for row in reader:
        if row and any(cell.strip() for cell in row):
            rows.append(row)
    return header, rows


def load_anchor_map(base: Path) -> dict[str, str]:
    rules_path = base / "keyword research" / "city_pdp_barcelona_content_block_rules.json"
    data = json.loads(rules_path.read_text(encoding="utf-8"))
    out: dict[str, str] = {}
    for k, v in data["anchor_keyword_to_block"].items():
        out[norm_kw(k)] = v
    return out


# Drop lodging/hotel intent + competitor / chain / OTA branded queries from City PDP lists
_HOTEL_RX = re.compile(
    r"\b("
    r"hotel|hotels|hostel|hostels|hostal|hostals|hostales|airbnb|air\s*bnb|"
    r"accommodation|accomodation|lodging|resort|resorts|motel|motels|"
    r"guest\s*house|guesthouse|bed\s+and\s+breakfast|\bb\s*&\s*b\b|where\s+to\s+stay|"
    r"places\s+to\s+stay|vacation\s+rental|holiday\s+rental|"
    r"apartments?\s+for\s+rent|apartment\s+rental|rent\s+an\s+apartment|"
    r"\bpension\b|\bpensions\b"
    r")\b",
    re.I,
)

_AIRPORT_LODGING_RX = re.compile(
    r"\b(hotel|hotels|hostel|hostels|stay|accommodation|lodging)\b.*\b(bcn|barcelona)\s+airport\b|"
    r"\b(bcn|barcelona)\s+airport\b.*\b(hotel|hotels|hostel|stay|accommodation)\b|"
    r"\bhotels?\s+near\b.*\bairport\b|\bnear\b.*\b(bcn|barcelona)\s+airport\b.*\b(hotel|hotels|stay)\b",
    re.I,
)

_BRAND_SUBSTRINGS: tuple[str, ...] = (
    "trip advisor",
    "tripadvisor",
    "viator",
    "booking.com",
    "hotels.com",
    "getyourguide",
    "get your guide",
    "klook",
    "reddit",
    "expedia",
    "priceline",
    "orbitz",
    "hotwire",
    "julia travel",
    "hotel arts",
    "hotelarts",
    "ritz carlton",
    "ritz-carlton",
    "ritzcarlton",
    "ritz barcelona",
    "marriott",
    "hilton",
    "hyatt",
    "novotel",
    "ibis hotel",
    "melia ",
    "melia hotel",
    "four seasons",
    "mandarin oriental",
    "sheraton",
    "westin",
    "holiday inn",
    "best western",
    "wyndham",
    "intercontinental",
    "radisson",
    "pullman",
    "nh collection",
    " nh hotel",
    "nh hotels",
    "w hotel",
    "brunch and cake",
    "honest greens",
    "circus pizza",
    "lugaris",
    "apple store",
    "world of banksy",
    "chanel ",
    "chanel shop",
    "starbucks",
    "mcdonald",
    "burger king",
)

_BRAND_TOKEN_RX = re.compile(
    r"\b("
    r"ryanair|easyjet|easy\s+jet|vueling|jet2\b|lufthansa|"
    r"iberia\s+(flight|airlines|airline)\b|"
    r"hertz|avis\b|europcar|sixt\b|enterprise\s+rent|budget\s+rent\s+a\s+car|\bibis\b"
    r")\b",
    re.I,
)


def should_exclude_keyword(keyword: str) -> tuple[bool, str]:
    """Returns (exclude, reason) for logging."""
    nk = norm_kw(keyword)
    if _HOTEL_RX.search(keyword) or _HOTEL_RX.search(nk):
        return True, "hotel"
    if _AIRPORT_LODGING_RX.search(keyword) or _AIRPORT_LODGING_RX.search(nk):
        return True, "hotel"
    if _BRAND_TOKEN_RX.search(keyword) or _BRAND_TOKEN_RX.search(nk):
        return True, "brand"
    for sub in _BRAND_SUBSTRINGS:
        if sub.strip().lower() in nk:
            return True, "brand"
    # Leading-brand OTAs / operators (substring without odd boundaries)
    if nk.startswith("viator ") or nk.endswith(" viator"):
        return True, "brand"
    return False, ""


# Tag clusters (Barcelona City PDP) — first regex match wins
_CLUSTER_RULES: list[tuple[str, re.Pattern[str]]] = [
    (
        "Budget & value",
        re.compile(
            r"\b(cheap|cheapest|budget|affordable|luxury|expensive|cost|costs|deal|free things)\b",
            re.I,
        ),
    ),
    (
        "Stay & accommodation",
        re.compile(
            r"\b(hotel|hotels|hostel|hostels|airbnb|accommodation|lodging|where to stay|"
            r"places to stay|apartment rental|near airport)\b",
            re.I,
        ),
    ),
    (
        "Nearby & day trips",
        re.compile(
            r"\b(day trip|day trips|day tour|day tours|excursion|nearby cities|cities nearby|"
            r"from barcelona to|trip from barcelona|tour from barcelona)\b",
            re.I,
        ),
    ),
    (
        "Getting there & local transport",
        re.compile(
            r"\b(flight|flights|fly to|airport|train to barcelona|bus to barcelona|renfe|"
            r"metro\b|public transport|transport pass|bus ticket|metro pass|bcn airport)\b",
            re.I,
        ),
    ),
    (
        "Food & drink",
        re.compile(
            r"\b(food|foods|restaurant|restaurants|tapas|paella|wine bar|gastronomy|culinary|"
            r"food tour|eat|eating|drink|drinks|brunch|coffee)\b",
            re.I,
        ),
    ),
    (
        "Nightlife",
        re.compile(r"\b(nightlife|night life|club|clubs|bar\b|bars\b|party)\b", re.I),
    ),
    (
        "Beaches & water",
        re.compile(
            r"\b(beach|beaches|seaside|coast|swim|snorkel|mediterranean)\b",
            re.I,
        ),
    ),
    (
        "Art & culture",
        re.compile(
            r"\b(museum|museums|gallery|galleries|art\b|culture|architecture|gaudi|gaudí|"
            r"opera|theatre|theater|concert)\b",
            re.I,
        ),
    ),
    (
        "Shopping",
        re.compile(r"\b(shopping|boutique|market\b|markets\b|mall)\b", re.I),
    ),
    (
        "Sports & events",
        re.compile(
            r"\b(stadium|football|soccer|f1|formula 1|marathon|marathons|match\b|fc barcelona|camp nou)\b",
            re.I,
        ),
    ),
    (
        "Nature & outdoors",
        re.compile(
            r"\b(hike|hiking|park\b|nature|mountain|montserrat|outdoor)\b",
            re.I,
        ),
    ),
    (
        "Itineraries & trip length",
        re.compile(
            r"\b(itinerary|itineraries|\d+\s*days in|weekend (trip )?to|how many days)\b",
            re.I,
        ),
    ),
    (
        "Neighbourhoods & areas",
        re.compile(
            r"\b(neighbourhood|neighborhood|neighbourhoods|neighborhoods|barrio|barrios|district|"
            r"gothic quarter|el born|eixample|gracia|gràcia|barceloneta|raval|areas to visit)\b",
            re.I,
        ),
    ),
    (
        "Sightseeing & landmarks",
        re.compile(
            r"\b(sightseeing|attractions|things to see|must see|must-see|must visit|landmarks|"
            r"places to visit|places to see|tourist attractions|iconic|walking tour|hop on hop off)\b",
            re.I,
        ),
    ),
    (
        "Activities & experiences",
        re.compile(
            r"\b(things to do|what to do|activities|experiences|fun things|to do in)\b",
            re.I,
        ),
    ),
    (
        "Trip planning & tips",
        re.compile(
            r"\b(guide|travel tips|first time|reddit|tripadvisor|viator|checklist|planning)\b",
            re.I,
        ),
    ),
]


def cluster_tag(keyword: str) -> str:
    for label, rx in _CLUSTER_RULES:
        if rx.search(keyword):
            return label
    return "Misc & branded queries"


def looks_like_question(nk: str) -> bool:
    """Natural-language question cues (keywords rarely include '?')."""
    nk = nk.strip()
    if not nk:
        return False
    if re.match(
        r"^(what|when|where|why|who|which|how|are|is|was|were|do|does|did|can|could|would|should|may)\b",
        nk,
        re.I,
    ):
        return True
    if re.match(r"^how\s+(much|many|long|far|often)\b", nk, re.I):
        return True
    if re.search(
        r"\b(is there|are there|is it|are they|can you|can i|should i|where is|where are|where can|where do|where should|"
        r"what time|what's the|what is the|what are the|do i need|does the|why is|who built|worth visiting)\b",
        nk,
        re.I,
    ):
        return True
    return False


def transport_block_match(nk: str) -> bool:
    """In-city transport fares / passes / operational detail (not generic getting-there)."""
    if not re.search(r"\b(barcelona|bcn)\b", nk, re.I):
        return False
    fare_rx = re.compile(
        r"\b(price|prices|cost|costs|fare|fares|how much|cheap(est)?|ticket|tickets|pass\b|passes|zones?\b|"
        r"t\-zone|top\s*up|reload)\b",
        re.I,
    )
    local_rx = re.compile(
        r"\b(metro|underground|bus\b|buses\b|t\-mob|tmob|tram\b|hola barcelona|rodalies|renfe\s+rodalies|tmb\b|"
        r"aero\s*bus|aerobus|nitbus|nit\s*bus)\b",
        re.I,
    )
    detail_rx = re.compile(
        r"\b(schedule|schedules|timetable|timetables|route\b|routes|lines?\b|map\b|maps\b|zones?\b|"
        r"operating hours|opening hours|frequency|zones\s+1\s*[–-]\s*6|zone\s+\d)\b",
        re.I,
    )
    if local_rx.search(nk) and (fare_rx.search(nk) or detail_rx.search(nk)):
        return True
    if re.search(
        r"\b(metro|underground)\s+(fare|fares)\b|\bunderground\s+tickets?\b|\bbus\s+(fare|fares)\b|"
        r"\bmetro\s+ticket\b|\bmetro\s+tickets\b|\bbus\s+ticket\b|\bbus\s+tickets\b",
        nk,
        re.I,
    ):
        return True
    if re.search(
        r"\b(barcelona|bcn)\b.*\b(metro|bus)\s+(ticket|tickets|pass|passes)\b|"
        r"\b(metro|bus)\s+(ticket|tickets|pass|passes)\b.*\b(barcelona|bcn)\b",
        nk,
        re.I,
    ):
        return True
    if re.search(r"\bpublic\s+transport\b.*\b(barcelona|bcn)\b.*\b(price|cost|fare|ticket|how much)\b", nk, re.I):
        return True
    return False


def content_block_for_keyword(keyword: str, anchors: dict[str, str]) -> str:
    nk = norm_kw(keyword)
    if nk in anchors:
        return anchors[nk]

    # Normalised synonym hooks for anchors
    nk2 = nk.replace("nightlife", "night life").replace("neighborhoods", "neighbourhoods")
    if nk2 in anchors:
        return anchors[nk2]

    # --- Ordered tiers (first match wins) ---

    # Neighbourhoods block (includes “areas to visit” wording)
    if re.search(
        r"\bareas to visit\b.*\bbarcelona\b|\bbarcelona\b.*\bareas to visit\b",
        nk,
        re.I,
    ):
        return "Neighbourhoods block"
    if re.search(
        r"\b(neighbourhoods?|neighborhoods?|barrios?)\b.*\bbarcelona\b|\bbarcelona\b.*\b(neighbourhoods?|neighborhoods?|barrios?|districts?)\b",
        nk,
        re.I,
    ):
        return "Neighbourhoods block"

    # Nearby block — outbound from Barcelona (excursions, nearby cities, beaches outside city)
    if re.search(
        r"\b(day trips?|day tours?|excursions?)\s+(from|near)\s+barcelona\b|\bfrom barcelona\b.*\b(day trip|tour|excursion)\b",
        nk,
        re.I,
    ):
        return "Nearby block"
    if re.search(
        r"\bbarcelona\s+day trips?\b|\bday tours?\s+from\s+barcelona\b|\bcities\s+nearby\s+barcelona\b|\bnearby\s+barcelona\b",
        nk,
        re.I,
    ):
        return "Nearby block"
    if re.search(
        r"\b(beaches|best beaches)\s+near\s+barcelona\b|\b(coastal\s+)?day\s+trip\b.*\bbarcelona\b.*\b(train|bus|tour)\b",
        nk,
        re.I,
    ):
        return "Nearby block"
    if re.search(
        r"\b(montserrat|sitges|girona|tarragona|costa brava|andorra)\b.*\b(from barcelona|barcelona day)\b|\b(from barcelona|day trip).*montserrat\b",
        nk,
        re.I,
    ):
        return "Nearby block"
    if re.search(r"\bbeaches from barcelona\b|\bcosta brava\b.*\bfrom barcelona\b", nk, re.I):
        return "Nearby block"
    if re.search(r"\bmontserrat\b.*\bbarcelona\b|\bbarcelona\b.*\bmontserrat\b", nk, re.I):
        return "Nearby block"

    # Questions about moving between another place and Barcelona → Nearby (not FAQ / How to get)
    if re.search(
        r"\bhow\s+(?:do\s+i|can\s+i|should\s+i|would\s+i|to)\s+(?:get|go|travel)\s+from\s+.+\s+to\s+barcelona\b",
        nk,
        re.I,
    ):
        return "Nearby block"
    if re.search(
        r"\bhow\s+(?:do\s+i|can\s+i|should\s+i|would\s+i|to)\s+(?:get|go|travel)\s+from\s+barcelona\s+to\b",
        nk,
        re.I,
    ):
        return "Nearby block"
    if re.search(
        r"\bhow\s+far\b.*\b(from|to)\s+barcelona\b|\bhow\s+far\b.*\bbarcelona\b.*\bfrom\b",
        nk,
        re.I,
    ):
        return "Nearby block"
    if not re.search(r"\bairport\b", nk, re.I) and (
        re.search(
            r"\b(?:is there|are there|can i)\b.*\b(train|flight)\b.*\b(from|to)\b.*\bbarcelona\b",
            nk,
            re.I,
        )
        or re.search(
            r"\b(?:is there|are there|can i)\b.*\bbarcelona\b.*\b(train|flight)\b.*\b(to|from)\b",
            nk,
            re.I,
        )
        or re.search(
            r"\b(?:is there|are there)\b.*\bbus\b.*\bfrom\b.*\bto\s+barcelona\b",
            nk,
            re.I,
        )
    ):
        return "Nearby block"

    # “how to get/go to … from Barcelona” / “from Barcelona to …” → Nearby (before generic How to get)
    if re.search(
        r"\bhow\s+to\s+(?:get|go)\s+to\s+[a-z][\w\-]*(?:\s+[a-z][\w\-]*){0,3}\s+from\s+barcelona\b",
        nk,
        re.I,
    ):
        return "Nearby block"
    if re.search(
        r"\bhow\s+to\s+(?:get|go)\s+from\s+barcelona\s+to\b",
        nk,
        re.I,
    ):
        return "Nearby block"
    if re.search(r"\bhow\s+to\s+(?:get|go)\s+to\s+barcelona\s+from\b", nk, re.I) and not re.search(
        r"\bto\s+barcelona\s+from\s+(?:the\s+)?airport\b|\bto\s+barcelona\s+from\s+bcn\s+airport\b",
        nk,
        re.I,
    ):
        return "Nearby block"

    # How to get block — airport → city & using public transport inside Barcelona (before inter-city logic)
    if re.search(
        r"\bhow to get to barcelona(\s+city)?\s+from\s+airport\b|\bhow to get to barcelona\s+from\s+airport\b",
        nk,
        re.I,
    ):
        return "How to get block"
    if re.search(r"\bhow to use public transport in barcelona\b", nk, re.I):
        return "How to get block"
    if re.search(
        r"\bhow\s+to\s+(?:get|go)\s+to\s+(?:bcn|barcelona)\s+airport\b|\bhow\s+to\s+(?:get|go)\s+to\s+bcn\s+airport\b",
        nk,
        re.I,
    ):
        return "How to get block"
    if re.search(
        r"\bhow\s+to\s+get\s+around\b(?:\s+in)?\s*(?:barcelona|bcn)\b|\bhow\s+to\s+get\s+around\b.*\b(barcelona|bcn)\b",
        nk,
        re.I,
    ):
        return "How to get block"
    if re.match(r"^how to get to barcelona\b", nk):
        if re.search(r"\bairport\b", nk):
            return "How to get block"
        if re.search(r"\bfrom\s+(?!the\s+airport\b)(?!airport\b)[a-z][a-z\-]{2,}\b", nk):
            return "Nearby block"
        return "How to get block"
    if re.search(r"\b(getting to|fly to)\s+barcelona\b", nk, re.I) and not re.search(
        r"\bfrom\s+[a-z]{3,}\s+to\s+barcelona\b", nk, re.I
    ):
        return "How to get block"
    if (
        re.match(r"^how\s+to\s+(?:get|go)\s+to\s+", nk, re.I)
        and re.search(r"\b(barcelona|bcn)\b", nk, re.I)
        and not re.search(
            r"\bhow\s+to\s+(?:get|go)\s+to\s+[a-z][\w\-]*(?:\s+[a-z][\w\-]*){0,3}\s+from\s+barcelona\b",
            nk,
            re.I,
        )
    ):
        return "How to get block"

    # Inter-city routes mentioning Barcelona → Nearby block (exclude airport ↔ centre hops)
    if re.search(
        r"\b(bus|train|flight)\s+from\s+[a-z][a-z\-]*\s+to\s+barcelona\b|\b(bus|train|flight)\s+from\s+barcelona\s+to\s+[a-z][a-z\-]*\b",
        nk,
        re.I,
    ) and not re.search(r"\bairport\b", nk, re.I):
        return "Nearby block"
    if re.search(
        r"\b(bus|train|flight)\s+from\s+(?:[\w\-]+\s+){1,5}to\s+barcelona\b|"
        r"\b(bus|train|flight)\s+from\s+barcelona\s+to\s+(?:[\w\-]+\s*){1,4}[\w\-]+",
        nk,
        re.I,
    ) and not re.search(r"\bairport\b", nk, re.I):
        return "Nearby block"

    # Inter-city without explicit “from/to” (e.g. valencia barcelona bus, barcelona granada bus)
    _non_place_lead = (
        r"(?:cheap|cheapest|best|free|top|low|cost|city|public|local|direct|international|domestic|"
        r"budget|luxury|night|day|airport|express|shuttle|tourist|sightseeing|hop|electric|"
        r"aero|inner|outer|first|business|economy|premium|moventis|sagales|hife|alsa)\b"
    )
    if re.search(
        rf"\b(?!{_non_place_lead})"
        r"[a-z][a-z\-]{3,}\s+barcelona\s+(bus|train|flight)\b",
        nk,
        re.I,
    ) and not re.search(r"\bairport\b", nk, re.I):
        return "Nearby block"
    if re.search(
        r"\bbarcelona\s+(?!airport\b)(?!city\b)"
        rf"(?!{_non_place_lead})"
        r"(?:[\w\-]+\s+){1,3}(bus|train|flight)\b",
        nk,
        re.I,
    ) and not re.search(r"\bairport\b", nk, re.I):
        return "Nearby block"
    if re.search(
        r"\b(bus|train)\s+(?!city\b)(?!public\b)(?!local\b)(?!airport\b)(?!express\b)(?!tourist\b)(?!the\b)"
        rf"(?!{_non_place_lead})"
        r"[a-z][a-z\-]{3,}\s+barcelona\b",
        nk,
        re.I,
    ) and not re.search(r"\bairport\b", nk, re.I):
        return "Nearby block"
    if re.search(
        r"\b(bus|train)\s+barcelona\s+to\s+(?:[\w\-]+\s*){1,4}[\w\-]+\b",
        nk,
        re.I,
    ) and not re.search(r"\bairport\b", nk, re.I):
        return "Nearby block"
    if re.search(
        r"\bbarcelona\s+to\s+(?:[\w\-]+\s+){0,5}(bus|train)\b",
        nk,
        re.I,
    ) and not re.search(r"\bairport\b", nk, re.I):
        return "Nearby block"

    if re.search(
        r"\b(from barcelona to|barcelona to)\s+(?!airport\b)[a-z][a-z\-]{3,}\b.*\b(bus|train|flight|renfe|drive|driving)\b",
        nk,
        re.I,
    ):
        return "Nearby block"
    if re.search(
        r"\b[a-z][a-z\-]{3,}\s+to\s+barcelona\s+(bus|train|flight)\b|\b[a-z][a-z\-]{3,}\s+(bus|train)\s+to\s+barcelona\b",
        nk,
        re.I,
    ) and not re.search(r"\bairport\b", nk, re.I):
        return "Nearby block"
    if (
        re.search(r"\bto barcelona from\b", nk, re.I)
        and re.search(r"\b(bus|train|flight)\b", nk, re.I)
        and not re.search(r"\bairport\b", nk, re.I)
    ):
        return "Nearby block"

    if re.search(
        r"\btransport in barcelona\b|\bpublic transport barcelona\b",
        nk,
        re.I,
    ):
        return "How to get block"
    if re.search(
        r"\bhola barcelona\b|\bbarcelona (city )?(travel )?card\b|\bbarcelona pass\b|\bt\-mob\b|\btmob\b",
        nk,
        re.I,
    ):
        if re.search(r"\b(price|prices|cost|costs|fare|how much|zones?\b|ticket)\b", nk, re.I):
            return "Transport block"
        return "How to get block"
    if re.search(r"\bbc[n]?\s+metro\b|\bmetro\s+bcn\b", nk, re.I):
        return "How to get block"

    # Itineraries block
    if re.search(
        r"\bbarcelona itineraries\b|\bitineraries in barcelona\b|\b\d+\s*days in barcelona\b|\bweekend (trip )?to barcelona\b",
        nk,
        re.I,
    ):
        return "Itineraries block"

    # H1-style trip framing (city as destination headline intent)
    if re.search(
        r"^(visit|travell?ing to|travel to)\s+barcelona\b|\btourism in barcelona\b|\btrips? to barcelona\b|\bholiday in barcelona\b|\bbarcelona vacation\b",
        nk,
        re.I,
    ):
        return "H1"

    # City attractions block — sights / landmarks / attraction wording
    if re.search(
        r"\b(top attractions|famous spots|tourist attractions)\b.*\bbarcelona\b|\bbarcelona\b.*\b(tourist attractions|top attractions)\b",
        nk,
        re.I,
    ):
        return "City attractions block"
    if re.search(
        r"\b(barcelona attractions|barcelona sightseeing|city sightseeing barcelona|must see in barcelona|must visit barcelona|places to visit in barcelona|places to see in barcelona|things to see in barcelona)\b",
        nk,
        re.I,
    ):
        return "City attractions block"
    if re.search(
        r"\btop\s+(10\s+)?things to see\b.*\bbarcelona\b|\bbarcelona\b.*\b(landmarks?|monuments?)\b",
        nk,
        re.I,
    ):
        return "City attractions block"
    if re.search(
        r"\b(barcelona what to see|what to see\b.*\bbarcelona)\b",
        nk,
        re.I,
    ):
        return "City attractions block"
    if re.search(
        r"\b(places to see|places to visit|places to go|places of interest|places in barcelona|places to explore|"
        r"sites to see|sites to visit|spots to visit|sites of interest|"
        r"tourist (places|spots|sights)|attractions to see|attraction places|attraction in\b|"
        r"barcelona places to go|barcelona places to see|barcelona tourist (places|spots|sights)|"
        r"barcelona city attractions|barcelona sites\b|spain tourist sites)\b.*\bbarcelona\b|"
        r"\bbarcelona\b.*\b(places to go|places to see|tourist places|tourist spots|sites to visit|spots to visit|places of interest)\b",
        nk,
        re.I,
    ):
        return "City attractions block"
    if re.search(
        r"\b(museum|museums|museu|mnac|macba|picasso|contemporani)\b.*\bbarcelona\b|\bbarcelona\b.*\b(museum|museums|museu|picasso|contemporani)\b",
        nk,
        re.I,
    ):
        return "City attractions block"

    # Things to do block — broad activities & thematic anchors from screenshot + close variants
    if re.search(
        r"\b(things to see and do)\b.*\bbarcelona\b",
        nk,
        re.I,
    ):
        return "Things to do block"
    if re.search(
        r"\b(things to in barcelona|barcelona things to\b|things to do in barca|whatto do in barcelona|barcelona to do\b)\b",
        nk,
        re.I,
    ):
        return "Things to do block"
    if re.search(
        r"\b(things to do|best things to do|top things to do|fun things to do|stuff to do|what to do)\b.*\bbarcelona\b|\bbarcelona\b.*\b(things to do|activities|to do)\b",
        nk,
        re.I,
    ):
        return "Things to do block"
    if re.search(
        r"\b(food|eating|gastronomy|drink)\s+in\s+barcelona\b|\bnight\s*life\b.*\bbarcelona\b|\bbarcelona\s+night\s*life\b|\bnightlife\b.*\bbarcelona\b|\bbarcelona\b.*\bnightlife\b",
        nk,
        re.I,
    ):
        return "Things to do block"
    if re.search(
        r"\bmust\s+(eat|try)\b.*\bbarcelona\b|\bbarcelona\b.*\bmust\s+(eat|try)\b",
        nk,
        re.I,
    ):
        return "Things to do block"
    if re.search(
        r"\b(art|culture|sport events)\s+in\s+barcelona\b|\bshopping in barcelona\b|\bbeaches in barcelona\b|\bnature in barcelona\b",
        nk,
        re.I,
    ):
        return "Things to do block"
    if re.search(
        r"\bbarcelona\s+(food|restaurants?|tapas|shopping|beaches)\b|\bbest restaurants\b.*\bbarcelona\b",
        nk,
        re.I,
    ):
        return "Things to do block"
    if re.search(
        r"\bbeach(es)?\b.*\bbarcelona\b|\bbarcelona\b.*\bbeach",
        nk,
        re.I,
    ):
        if not re.search(r"\bbeaches from barcelona\b|\bnear\b.*\bbarcelona\b", nk, re.I):
            return "Things to do block"
    if re.search(
        r"\b(restaurant|restaurants|tapas|steak|brunch|dining|meal|honest greens|paella|ramen|sushi|foodies|pizza|"
        r"recommended restaurants)\b.*\bbarcelona\b|\bbarcelona\b.*\b(restaurant|restaurants|tapas|steak|brunch|dining|stores|paella|ramen|food|meals|foodies|pizza)\b|\bbarcelona stores\b|\bshop(ping)? in barcelona\b|\bbc[n]?\s+shop\b|\b(apple|chanel)\s+store\b.*\bbarcelona\b",
        nk,
        re.I,
    ):
        return "Things to do block"
    if re.search(
        r"\b(to do in barcelona|must do in barcelona|must do things\b.*\bbarcelona\b)\b|\bmust do\b.*\bbarcelona\b",
        nk,
        re.I,
    ):
        return "Things to do block"

    # City attractions — phrases led by "Barcelona …" (sightseeing inventory)
    if re.search(
        r"^\bbarcelona\b\s+(city attractions|sites to see|sites of interest|tourist sights|spain tourist sites|best things to see|to see and do|tourist)\b|\b"
        r"barcelona city tourism\b|\btourist activities\b.*\bbarcelona\b|\btourist spot\b.*\bbarcelona\b|\bplaces in barcelona\b",
        nk,
        re.I,
    ):
        return "City attractions block"
    if re.search(
        r"\bmust see (things|and do)\b.*\bbarcelona\b|\bmust visit places\b.*\bbarcelona\b|\bbest (things to visit|attractions)\b.*\bbarcelona\b|\bbest activities to do\b.*\bbarcelona\b",
        nk,
        re.I,
    ):
        return "City attractions block"
    if re.search(
        r"\bbarcelona\s+(mnac|macba|cosmocaixa)\b|\bla boqueria\b.*\bbarcelona\b|\bbarcelona\b.*\bla boqueria\b|\bbarceloneta park\b",
        nk,
        re.I,
    ):
        return "City attractions block"

    # Nearby — tour phrasing variants
    if re.search(r"\bday trip tours from barcelona\b|\btours from barcelona\b", nk, re.I):
        return "Nearby block"

    if re.search(r"\bexplore barcelona\b|\bdiscover barcelona\b|\bexperience barcelona\b", nk, re.I):
        return "Things to do block"
    if re.search(r"\bwalking tour\b.*\bbarcelona\b|\bbarcelona\b.*\bwalking tour\b|\bbike tour\b.*\bbarcelona\b", nk, re.I):
        return "Things to do block"
    if re.search(r"\bbarcelona\b.*\b(visitor guide|travel guide|for first timers)\b|\btouring barcelona\b", nk, re.I):
        return "Things to do block"

    # Transport block — in-city fares, passes pricing & operational detail (after thematic Things to do tails)
    if transport_block_match(nk):
        return "Transport block"

    # FAQ block — remaining question-shaped queries (How to get to Barcelona / inter-city handled earlier)
    if looks_like_question(nk):
        return "FAQ block"

    return "Unclassified"


def apply_block_overrides(keyword: str, tag: str, block: str) -> str:
    """Tag-driven mapping + hard pin for areas wording (runs after regex tiers)."""
    nk = norm_kw(keyword)
    if re.search(r"\bareas to visit\b.*\bbarcelona\b|\bbarcelona\b.*\bareas to visit\b", nk, re.I):
        return "Neighbourhoods block"
    if tag == "Neighbourhoods & areas":
        return "Neighbourhoods block"
    if tag == "Sightseeing & landmarks":
        return "City attractions block"
    return block


def parse_volume(cell: str) -> int:
    cell = cell.strip().replace(",", "")
    if not cell or cell in {"-", "–"}:
        return 0
    try:
        return int(float(cell))
    except ValueError:
        return 0


def main() -> int:
    base = Path(__file__).resolve().parents[1]
    default_inputs = [
        Path(r"c:\Users\FEVER\Downloads\Keyword Stats 2026-05-08 at 16_17_29.csv"),
        Path(r"c:\Users\FEVER\Downloads\Keyword Stats 2026-05-08 at 16_18_03.csv"),
        Path(r"c:\Users\FEVER\Downloads\Keyword Stats 2026-05-08 at 16_18_32.csv"),
    ]
    argv_rest = sys.argv[1:]
    paths = [Path(p) for p in argv_rest if not p.startswith("--")]
    if not paths:
        paths = default_inputs

    out_arg = next((p for p in argv_rest if p.startswith("--out=")), None)
    out_path = Path(out_arg.split("=", 1)[1]) if out_arg else base / "keyword research" / "Barcelona_City_PDP_keywords_clustered.csv"

    anchors = load_anchor_map(base)

    merged: dict[str, list[str]] = {}
    merged_full: dict[str, list[str]] = {}
    header_ref: list[str] | None = None
    excluded_hotel_kw: set[str] = set()
    excluded_brand_kw: set[str] = set()

    def pad_row(row: list[str], n: int) -> list[str]:
        r = list(row[:n])
        while len(r) < n:
            r.append("")
        return r

    for path in paths:
        if not path.is_file():
            print(f"Skip missing: {path}", file=sys.stderr)
            continue
        header, rows = read_rows(path)
        header_ref = header

        def idx(name: str) -> int:
            return header.index(name)

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

        for row in rows:
            if len(row) <= max(pull):
                continue
            kw = row[i_kw].strip()
            if not kw:
                continue
            drop, reason = should_exclude_keyword(kw)
            if drop:
                if reason == "hotel":
                    excluded_hotel_kw.add(kw.strip())
                else:
                    excluded_brand_kw.add(kw.strip())
                continue
            vol = parse_volume(row[idx("Avg. monthly searches")])
            vals = [row[j] for j in pull]
            if kw not in merged or vol > parse_volume(merged[kw][1]):
                merged[kw] = vals
                merged_full[kw] = pad_row(row, len(header))

    if not merged or header_ref is None:
        print("No rows merged.", file=sys.stderr)
        return 1

    out_rows: list[list[str]] = []
    for kw, vals in sorted(merged.items(), key=lambda kv: (-parse_volume(kv[1][1]), norm_kw(kv[0]))):
        tag = cluster_tag(kw)
        block = apply_block_overrides(kw, tag, content_block_for_keyword(kw, anchors))
        out_rows.append(
            [
                vals[0],
                "City PDP",
                "Barcelona",
                tag,
                block,
                *vals[1:],
            ]
        )

    merged_raw_path = base / "keyword research" / "Keyword Stats 2026-05-08 Barcelona City PDP merged raw.csv"
    merged_raw_path.parent.mkdir(parents=True, exist_ok=True)
    with merged_raw_path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
        w.writerow(header_ref)
        for kw in sorted(merged_full.keys(), key=lambda k: (-parse_volume(merged[k][1]), norm_kw(k))):
            w.writerow(merged_full[kw])
    print(
        "Excluded unique keywords (hotel/lodging intent): "
        f"{len(excluded_hotel_kw)}; (brand/OTA/chain): {len(excluded_brand_kw)}"
    )
    print(f"Merged raw (deduped by Keyword, max volume) -> {merged_raw_path}")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
        w.writerow(OUT_COLUMNS)
        w.writerows(out_rows)

    print(f"Written {len(out_rows)} unique keywords -> {out_path}")
    blocks = {}
    for r in out_rows:
        blocks[r[4]] = blocks.get(r[4], 0) + 1
    print("content_block counts:", dict(sorted(blocks.items(), key=lambda x: -x[1])))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
