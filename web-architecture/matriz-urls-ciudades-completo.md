# Matriz de URLs — listado completo de ciudades

Archivo importable: **`matriz-urls-ciudades-completo.csv`** (400 filas: 100 ciudades × 4 tipos de página).

## Reglas (igual que la prueba de 6 ciudades)

- Orden por cada ciudad: **Country (PLP)** → **City (PDP)** → **Itineraries (PLP)** → **Travel guide (PLP)**.
- Columna **City**: `N/A` salvo en **City (PDP)**, solo cuando la URL incluye el segmento de ciudad.
- **URLs:** inglés, minúsculas, sin acentos ni caracteres especiales; palabras separadas con **guión medio** (nunca guión bajo).

## Plantillas

| Page type | Patrón |
|-----------|--------|
| Country (PLP) | `https://tourism-tickets.com/{country}/` |
| City (PDP) | `https://tourism-tickets.com/{country}/{city}/` |
| Itineraries (PLP) | `https://tourism-tickets.com/itineraries/{country}/` |
| Travel guide (PLP) | `https://tourism-tickets.com/travel-guides/{country}/` |

`{country}` y `{city}` son **slugs** (no los nombres mostrados en la columna Country).

## Mapeos destacados en URLs

| En el listado original | Slug ciudad en URL | País |
|------------------------|-------------------|------|
| Mexico DF | `mexico-city` | Mexico |
| Genova | `genoa` | Italy |
| Las Palmas de Gran Canaria | `las-palmas-de-gran-canaria` | Spain |
| Gijón | `gijon` | Spain |
| Córdoba | `cordoba` | Spain |

En **City (PDP)**, la columna **City** del CSV usa nombre en inglés cuando aplica (p. ej. listado "Mexico DF" → celda **Mexico City**; **Genoa**, **Gijon**, **Cordoba**).

## Países / slugs de país usados

`united-states`, `united-kingdom`, `australia`, `canada`, `netherlands`, `germany`, `spain`, `italy`, `france`, `united-arab-emirates`, `sweden`, `austria`, `brazil`, `mexico`, `denmark`, `belgium`, `switzerland`, `czech-republic`, `norway`, `finland`, `portugal`, `ireland`.

## Regenerar el CSV

Si cambias el listado en `_generate_city_url_matrix.py` (datos `ROWS_RAW`):

```bash
python web-architecture/_generate_city_url_matrix.py
```
