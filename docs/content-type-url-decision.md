# Decision table: content type → section → URL template

Shared reference for **design, content, and SEO**. Example domain: `tourism-tickets.com`.

**Conventions**

- **`[place]`:** canonical geographic slug (city, region, country, or macro-area); one criterion per URL (e.g. `scandinavia`, do not mix `scandinavian` and `scandinavia` for the same destination).
- **`[duration]`:** duration in the slug (e.g. `3-days`, `1-week`, `2-week`) — align with the H1 and the body copy.
- **`[geo]`** (travel guides only): editorial bucket for grouping hubs (continent, country, or cross-cutting tag such as `global`).
- **`[topic]`:** slug for the theme / primary keyword (guides); stable over time.

`/destinations/` is **distributive landing only**; canonical destination URLs are `/[country]/` and `/[country]/[city]/` (option B).

---

## Main table

| Content type | Itineraries vs Travel guides | URL template |
|-------------------|------------------------------|-------------------|
| Destinations index landing (links only) | None (hub page) | `https://tourism-tickets.com/destinations/` |
| Country (destination hub: intro, links to cities) | None | `https://tourism-tickets.com/[country]/` |
| City (destination hub: what to see, links to related guides/itineraries) | None | `https://tourism-tickets.com/[country]/[city]/` |
| Itinerary hub for a geographic scope (list or broad intro without mandatory day-by-day in one long URL) | **Itineraries** | `https://tourism-tickets.com/itineraries/[place]/` |
| Day-by-day or clearly temporal itinerary (day 1 → day N, staged route) | **Itineraries** | `https://tourism-tickets.com/itineraries/[place]-[duration]/` |
| Road trip or multi-stop route with visit order | **Itineraries** | `https://tourism-tickets.com/itineraries/[place]-[duration]/` (define `[place]` as the route; e.g. `usa-west-coast`) |
| Thematic guide, list, or tips **without** day-by-day chronology as the main axis | **Travel guides** | `https://tourism-tickets.com/travel-guides/[geo]/[topic]/` |
| Comparisons, rankings, or lists (“best…”, “cheap…”, “top…”) without an itinerary | **Travel guides** | `https://tourism-tickets.com/travel-guides/[geo]/[topic]/` |
| Practical tips (budget, transport, luggage, visas, insurance) | **Travel guides** | `https://tourism-tickets.com/travel-guides/[geo]/[topic]/` (`[geo]` = region where it applies; see next row if global) |
| Topic **not** tied to a region (e.g. jet lag, generic travel insurance) | **Travel guides** | `https://tourism-tickets.com/travel-guides/global/[topic]/` |
| Institutional page | None | `https://tourism-tickets.com/about-us/` |

---

## Quick rule (one line)

If the reader can follow the content as a **calendar or ordered sequence** → **Itineraries**. If the value is **information, list, or topic** without that skeleton → **Travel guides**.

---

## Edge cases

| Situation | Decision |
|-----------|----------|
| Same area and duration: hub `[place]/` vs piece `[place]-[duration]/` | The hub links to itineraries by duration; do not duplicate the same copy across both URLs. |
| “3 days in Rome”: itinerary or guide? | If it is **day 1 / day 2 / day 3** → itineraries (`…/itineraries/rome-3-days/` or `…/itineraries/lazio-rome-3-days/` per your taxonomy). If it is **an unordered list of ideas** → travel guides. |
| City pillar `/italy/rome/` vs guide “best time in Rome” | The city pillar holds summary + links; the thematic guide lives at `travel-guides/europe/best-time-to-visit-rome/` (or `[geo]` consistent with your rule). |
| Future transactional content | Reserve routes (`/tickets/`, checkout, or subdomain) without clashing with `[country]` (e.g. avoid ambiguous `/us/`; prefer `united-states`). |

---

## Changelog

| Date | Change |
|-------|--------|
| 2026-04-29 | First version aligned with option B for destinations and `[place]` / `[geo]` / `[topic]` segments. |
