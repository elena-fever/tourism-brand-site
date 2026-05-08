#!/usr/bin/env python3
"""Keep only NYC-focused Keyword Planner rows; drop upstate / non-city trips."""

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


# Outside NYC core tourism — exclude even if "New York" appears as state wording
_BLACKLIST_PHRASES = sorted(
    {
        "thousand islands",
        "1000 islands",
        "finger lakes",
        "watkins glen",
        "lake placid",
        "adirondack",
        "adirondacks",
        "catskill mountains",
        "catskills",
        "niagara falls",
        "niagara fall",
        # Common upstate / western NY trip hubs (City PDP scope = NYC metro)
        "montauk",
        "hamptons",
        "fire island",
        "the finger lakes",
        "cooperstown",
        "howe caverns",
        "bear mountain",
        "storm king",
        "woodstock ny",
        "ithaca",
        "binghamton",
        "rochester ny",
        "syracuse ny",
        "albany ny",
        "buffalo ny",
    },
    key=len,
    reverse=True,
)

_BLACKLIST_PHRASES_N = [norm(p) for p in _BLACKLIST_PHRASES]

_BOROUGH_PHRASES = {"staten island"}

_BOROUGH_TOKENS = {"manhattan", "brooklyn", "queens", "bronx", "staten"}

_NEIGHBORHOOD_PHRASES = sorted(
    {
        "lower east side",
        "upper east side",
        "upper west side",
        "east village",
        "west village",
        "greenwich village",
        "financial district",
        "little italy",
        "murray hill",
        "long island city",
        "williamsburg brooklyn",
        "dyker heights",
        "prospect park",
        "park slope",
        "coney island",
        "flushing queens",
        "jackson heights",
        "bedford stuyvesant",
        "bed stuy",
        "times square",
        "rockefeller center",
        "battery park",
        "meatpacking district",
        "lincoln center",
        "high line",
        "highline",
        "grand central",
        "brooklyn bridge",
        "washington heights",
        "red hook",
        "inwood",
        "kips bay",
    },
    key=len,
    reverse=True,
)

_NEIGHBORHOOD_PHRASES_N = [norm(p) for p in _NEIGHBORHOOD_PHRASES]

_NEIGHBORHOOD_TOKENS = {
    "harlem",
    "soho",
    "tribeca",
    "chelsea",
    "williamsburg",
    "bushwick",
    "astoria",
    "dumbo",
    "midtown",
    "chinatown",
    "gramercy",
    "noho",
    "nolita",
    "flatiron",
    "uptown",
    "nomad",
    "ridgewood",
    "flushing",
}


def _tokens(nk: str) -> list[str]:
    parts = re.findall(r"[\w']+", nk, flags=re.UNICODE)
    out: list[str] = []
    for p in parts:
        out.append(p)
        if "-" in p:
            out.extend(p.split("-"))
    return out


def hits_blacklist(spaced: str) -> bool:
    for bad in _BLACKLIST_PHRASES_N:
        if bad and f" {bad} " in spaced:
            return True
    if re.search(r"\bniagara\b", spaced):
        return True
    return False


def has_nyc_anchor(keyword: str) -> bool:
    nk = norm(keyword)
    compact = nk.replace(" ", "")
    spaced = f" {nk} "

    if hits_blacklist(spaced):
        return False

    if "newyork" in compact or "newyorkcity" in compact:
        return True
    if "newyorkcity" in nk.replace(" ", ""):
        return True
    if re.search(r"\b(new york city)\b", nk):
        return True
    if re.search(r"\b(new york)\b", nk):
        return True
    if re.search(r"\bnyc\b", nk):
        return True
    if re.search(r"\b(big apple)\b", nk):
        return True

    for phrase in _NEIGHBORHOOD_PHRASES_N:
        if phrase and f" {phrase} " in spaced:
            return True

    for phrase in _BOROUGH_PHRASES:
        p = norm(phrase)
        if f" {p} " in spaced:
            return True

    for t in _tokens(nk):
        if t in _BOROUGH_TOKENS:
            return True
        if t in _NEIGHBORHOOD_TOKENS:
            return True

    return False


def is_kept(keyword: str) -> bool:
    kw = keyword.strip()
    if not kw:
        return False
    return has_nyc_anchor(kw)


def main() -> int:
    inp = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(
        r"c:\Users\FEVER\Downloads\Keyword Stats 2026-05-07 at 13_33_59.csv"
    )
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else inp.with_name(inp.stem + "_nyc-city-only" + inp.suffix)

    lines = read_text_smart(inp).splitlines()
    if len(lines) < 4:
        print("File too short", file=sys.stderr)
        return 1

    preamble = lines[:2]
    header_line = lines[2]
    data_lines = lines[3:]

    rows_out: list[list[str]] = []
    kept = dropped = 0
    for row in csv.reader(data_lines, delimiter="\t"):
        if not row:
            continue
        kw = row[0].strip()
        if not is_kept(kw):
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
