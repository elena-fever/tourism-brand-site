# Tabla de decisión: tipo de contenido → sección → plantilla de URL

Referencia compartida para **diseño, contenido y SEO**. Dominio de ejemplo: `tourism-tickets.com`.

**Convenciones**

- **`[place]`:** slug geográfico canónico (ciudad, región, país o macro-zona); un solo criterio por URL (p. ej. `scandinavia`, no mezclar `scandinavian` y `scandinavia` para el mismo destino).
- **`[duration]`:** duración en el slug (p. ej. `3-days`, `1-week`, `2-week`) — alinear con el H1 y el contenido.
- **`[geo]`** (solo travel guides): bucket editorial para agrupar hubs (continente, país o etiqueta transversal como `global`).
- **`[topic]`:** slug del tema / keyword principal (guías); estable en el tiempo.

`/destinations/` es solo **landing distributiva**; las URLs canónicas de destino son `/[country]/` y `/[country]/[city]/` (opción B).

---

## Tabla principal

| Tipo de contenido | Itineraries vs Travel guides | Plantilla de URL |
|-------------------|------------------------------|-------------------|
| Landing índice de destinos (solo enlaces) | Ninguna (página de hub) | `https://tourism-tickets.com/destinations/` |
| País (hub destino: introducción, enlaces a ciudades) | Ninguna | `https://tourism-tickets.com/[country]/` |
| Ciudad (hub destino: qué ver, enlaces a guías/itinerarios relacionados) | Ninguna | `https://tourism-tickets.com/[country]/[city]/` |
| Hub de itinerarios para un ámbito geográfico (lista o intro amplia sin día a día obligatorio en una sola URL larga) | **Itineraries** | `https://tourism-tickets.com/itineraries/[place]/` |
| Itinerario por días u orden temporal claro (día 1 → día N, ruta por etapas) | **Itineraries** | `https://tourism-tickets.com/itineraries/[place]-[duration]/` |
| Road trip o ruta multi-parada con orden de visita | **Itineraries** | `https://tourism-tickets.com/itineraries/[place]-[duration]/` (definir `[place]` como la ruta; p. ej. `usa-west-coast`) |
| Guía temática, listado o consejos **sin** cronología día a día como eje principal | **Travel guides** | `https://tourism-tickets.com/travel-guides/[geo]/[topic]/` |
| Comparativas, rankings o listados (“best…”, “cheap…”, “top…”) sin itinerario | **Travel guides** | `https://tourism-tickets.com/travel-guides/[geo]/[topic]/` |
| Consejos prácticos puntuales (presupuesto, transporte, equipaje, visados, seguros) | **Travel guides** | `https://tourism-tickets.com/travel-guides/[geo]/[topic]/` (`[geo]` = zona donde aplica; ver fila siguiente si es global) |
| Tema **no** anclado a una región (p. ej. jet lag, seguro de viaje genérico) | **Travel guides** | `https://tourism-tickets.com/travel-guides/global/[topic]/` |
| Página institucional | Ninguna | `https://tourism-tickets.com/about-us/` |

---

## Regla rápida (una línea)

Si el usuario puede seguir el contenido como **calendario o secuencia ordenada** → **Itineraries**. Si el valor está en **información, lista o tema** sin ese esqueleto → **Travel guides**.

---

## Casos límite

| Situación | Decisión |
|-----------|----------|
| Misma zona y duración: hub `[place]/` vs pieza `[place]-[duration]/` | El hub enlaza a los itinerarios por duración; no duplicar el mismo texto en ambas URL. |
| “3 días en Roma”: ¿itinerario o guía? | Si es **día 1 / día 2 / día 3** → itineraries (`…/itineraries/rome-3-days/` o `…/itineraries/lazio-rome-3-days/` según vuestra taxonomía). Si es **lista de ideas sin orden** → travel guides. |
| City pillar `/italy/rome/` vs guía “mejor época en Roma” | El pillar ciudad acoge resumen + enlaces; la guía temática vive en `travel-guides/europe/best-time-to-visit-rome/` (o `[geo]` coherente con vuestra regla). |
| Contenido transaccional futuro | Reservar rutas (`/tickets/`, checkout o subdominio) sin conflicto con `[country]` (p. ej. evitar `/us/` ambiguo; preferir `united-states`). |

---

## Changelog

| Fecha | Cambio |
|-------|--------|
| 2026-04-29 | Primera versión alineada con opción B en destinations y segmentos `[place]` / `[geo]` / `[topic]`. |
