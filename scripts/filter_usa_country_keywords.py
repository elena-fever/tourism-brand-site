#!/usr/bin/env python3
"""Filter Keyword Planner export: USA country-level rows only (no city/state/park-specific)."""

from __future__ import annotations

import csv
import re
import sys
import unicodedata
from pathlib import Path


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


_USA_BAD_AMERICA = re.compile(
    r"\b(latin|south|central|north)\s+america\b",
    re.I,
)
_USA_ANCHOR_STRONG = re.compile(
    r"\b(united states|usa|u\.s\.a\.?)\b|\bu\.s\.(?![a-z])\b",
    re.I,
)
_USA_ANCHOR_AMERICA = re.compile(r"\bamerica\b", re.I)
_USA_ANCHOR_THE_US = re.compile(
    r"\b(in|to|across|around|throughout|from|within|outside|for)\s+the\s+us\b|\bthe\s+us\b",
    re.I,
)
_USA_ANCHOR_IN_US = re.compile(
    r"\b(in|to|across|around|throughout|within|outside|for)\s+us\b",
    re.I,
)
_USA_ANCHOR_STATES_INFORMAL = re.compile(
    r"\b(in|around|across|throughout|visit|visiting|travel|traveling|places)\s+the\s+states\b"
    r"|\bin\s+the\s+states\b|\baround\s+the\s+states\b"
    r"|\bstates\s+to\s+(visit|travel|see|explore)\b",
    re.I,
)


def has_usa_anchor(keyword: str) -> bool:
    nk = norm(keyword)
    if _USA_BAD_AMERICA.search(nk):
        return False
    if "canada" in nk:
        return False
    if "mexico" in nk and "new mexico" not in nk:
        return False
    if _USA_ANCHOR_STRONG.search(nk):
        return True
    if _USA_ANCHOR_AMERICA.search(nk):
        return True
    if _USA_ANCHOR_THE_US.search(nk):
        return True
    if _USA_ANCHOR_IN_US.search(nk):
        return True
    if _USA_ANCHOR_STATES_INFORMAL.search(nk):
        return True
    if nk.startswith("us ") or nk.endswith(" us") or " us " in nk:
        return True
    return False


_PHRASE_EXCLUDE = sorted(
    {
        # Multi-word states / fed district
        "new york",
        "new jersey",
        "new mexico",
        "new orleans",
        "north carolina",
        "south carolina",
        "north dakota",
        "south dakota",
        "rhode island",
        "west virginia",
        "district of columbia",
        "washington dc",
        "washington d.c.",
        "wall street",
        # Major metros / regions used as destinations (phrase)
        "los angeles",
        "las vegas",
        "san francisco",
        "san diego",
        "san antonio",
        "san jose",
        "santa fe",
        "salt lake city",
        "st louis",
        "st. louis",
        "kansas city",
        "oklahoma city",
        "salt lake",
        "new haven",
        "key west",
        "outer banks",
        "cape cod",
        "martha vineyard",
        "niagara falls",
        "lake tahoe",
        "big sur",
        "silicon valley",
        "times square",
        "grand canyon",
        "yellowstone",
        "yosemite",
        "zion national",
        "glacier national",
        "great smoky",
        "acadia national",
        "everglades",
        "arches national",
        "bryce canyon",
        "death valley",
        "sequoia",
        "rocky mountain national",
        "disney world",
        "disneyland",
        "universal studios",
        "statue of liberty",
        "golden gate",
        "waikiki",
        "mauna kea",
        "route 66",
        "blue ridge parkway",
        "going to the sun road",
        "el paso",
        "fort worth",
        "long beach",
        "fort lauderdale",
        "corpus christi",
        "des moines",
        "salt lake",
        "kansas city",
        "little rock",
        "colorado springs",
        "virginia beach",
        # Territories / neighbours when localized
        "puerto rico",
        "us virgin islands",
        "u.s. virgin islands",
    },
    key=len,
    reverse=True,
)

_PHRASE_EXCLUDE_N = [norm(p) for p in _PHRASE_EXCLUDE]

_STATE_TOKENS = {
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
    "ohio",
    "oklahoma",
    "oregon",
    "pennsylvania",
    "tennessee",
    "texas",
    "utah",
    "vermont",
    "virginia",
    "washington",
    "wisconsin",
    "wyoming",
}

_CITY_TOKENS = {
    "atlanta",
    "austin",
    "baltimore",
    "boston",
    "buffalo",
    "charlotte",
    "chicago",
    "cincinnati",
    "cleveland",
    "columbus",
    "dallas",
    "denver",
    "detroit",
    "duluth",
    "fresno",
    "honolulu",
    "houston",
    "indianapolis",
    "jacksonville",
    "louisville",
    "memphis",
    "mesa",
    "miami",
    "milwaukee",
    "minneapolis",
    "nashville",
    "omaha",
    "orlando",
    "philadelphia",
    "phoenix",
    "pittsburgh",
    "portland",
    "raleigh",
    "reno",
    "sacramento",
    "spokane",
    "tampa",
    "tucson",
    "wichita",
    "anchorage",
    "boise",
    "boulder",
    "charleston",
    "daytona",
    "durham",
    "erie",
    "eugene",
    "galveston",
    "greensboro",
    "knoxville",
    "lincoln",
    "mobile",
    "myrtle",
    "naples",
    "norfolk",
    "oakland",
    "oxnard",
    "pensacola",
    "providence",
    "richmond",
    "riverside",
    "rochester",
    "sarasota",
    "scottsdale",
    "shreveport",
    "stockton",
    "tallahassee",
    "tempe",
    "toledo",
    "tulsa",
    "ventura",
    "paso",
}

# "paso" catches el paso via phrase usually; token paso alone weak — remove paso from city tokens to reduce noise
_CITY_TOKENS.discard("paso")

_TOKEN_EXCLUDE = set(_STATE_TOKENS) | set(_CITY_TOKENS)

# Metro shorthand / airport codes sometimes spelled out
_TOKEN_EXCLUDE.update({"nyc", "sf"})

# Two-letter state codes that are unlikely to be common English words as standalone tokens
_ABBREV_CODES = (
    "ny|nj|nm|nv|nc|nd|ne|nh|fl|tx|ca|mi|il|ga|wa|co|az|tn|mo|md|mn|"
    "ms|ar|ks|ky|ut|ia|wv|wi|wy|sd|vt|ri|ak|hi|id|mt|dc|oh|pa|sc|al|de|ct|ma|la|va"
)
_ABBREV_RE = re.compile(rf"\b({_ABBREV_CODES})\b", re.I)


def _tokens_from_keyword(nk: str) -> list[str]:
    parts = re.findall(r"[\w']+", nk, flags=re.UNICODE)
    out: list[str] = []
    for p in parts:
        out.append(p)
        if "-" in p:
            out.extend(p.split("-"))
    return out


def is_excluded(keyword: str) -> bool:
    raw = keyword.strip()
    if not raw:
        return True
    if not has_usa_anchor(raw):
        return True
    n = norm(raw)
    spaced = f" {n} "

    for phrase in _PHRASE_EXCLUDE_N:
        if phrase and f" {phrase} " in spaced:
            return True

    for t in _tokens_from_keyword(n):
        if len(t) < 2:
            continue
        if t in _TOKEN_EXCLUDE:
            return True

    if _ABBREV_RE.search(n):
        return True

    return False


def main() -> int:
    inp = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(
        r"c:\Users\FEVER\Downloads\Keyword Stats 2026-05-07 at 13_24_24.csv"
    )
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else inp.with_name(inp.stem + "_usa-country-only" + inp.suffix)

    lines = read_text_smart(inp).splitlines()
    if len(lines) < 4:
        print("File too short", file=sys.stderr)
        return 1

    preamble = lines[:2]
    header_line = lines[2]
    data_lines = lines[3:]

    reader = csv.reader(data_lines, delimiter="\t")
    rows_out: list[list[str]] = []
    kept = dropped = 0
    for row in reader:
        if not row:
            continue
        kw = row[0].strip()
        if is_excluded(kw):
            dropped += 1
            continue
        rows_out.append(row)
        kept += 1

    with out.open("w", encoding="utf-8-sig", newline="") as f:
        for line in preamble:
            f.write(line + "\n")
        f.write(header_line + "\n")
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerows(rows_out)

    print(f"Written: {out}")
    print(f"Kept: {kept}, dropped: {dropped}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
