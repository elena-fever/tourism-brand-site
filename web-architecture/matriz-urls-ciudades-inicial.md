# Matriz de URLs (prueba 6 ciudades)

Formato **una URL por fila** para importar en Google Sheets u otras herramientas. Alineado con la estructura por **país** y **ciudad** (sin hubs regionales tipo `europe` en esta fase).

**Plantillas** (sustituye `country` y `city` por el slug en inglés, minúsculas y guiones)

| Page type | Patrón |
|-----------|--------|
| Country (PLP) | `https://tourism-tickets.com/{country}/` |
| City (PDP) | `https://tourism-tickets.com/{country}/{city}/` |
| Itineraries (PLP) | `https://tourism-tickets.com/itineraries/{country}/` |
| Travel guide (PLP) | `https://tourism-tickets.com/travel-guides/{country}/` |

**Regla columna City:** solo se rellena si la **URL** incluye el segmento de ciudad; si no, `N/A` (páginas de ámbito país).

**Tabla** (misma información que `matriz-urls-ciudades-inicial.csv`)

| Page type | Country | City | URLs |
|-----------|---------|------|------|
| Country (PLP) | Spain | N/A | https://tourism-tickets.com/spain/ |
| City (PDP) | Spain | Benidorm | https://tourism-tickets.com/spain/benidorm/ |
| Itineraries (PLP) | Spain | N/A | https://tourism-tickets.com/itineraries/spain/ |
| Travel guide (PLP) | Spain | N/A | https://tourism-tickets.com/travel-guides/spain/ |
| Country (PLP) | United Kingdom | N/A | https://tourism-tickets.com/united-kingdom/ |
| City (PDP) | United Kingdom | Edinburgh | https://tourism-tickets.com/united-kingdom/edinburgh/ |
| Itineraries (PLP) | United Kingdom | N/A | https://tourism-tickets.com/itineraries/united-kingdom/ |
| Travel guide (PLP) | United Kingdom | N/A | https://tourism-tickets.com/travel-guides/united-kingdom/ |
| Country (PLP) | Netherlands | N/A | https://tourism-tickets.com/netherlands/ |
| City (PDP) | Netherlands | Rotterdam | https://tourism-tickets.com/netherlands/rotterdam/ |
| Itineraries (PLP) | Netherlands | N/A | https://tourism-tickets.com/itineraries/netherlands/ |
| Travel guide (PLP) | Netherlands | N/A | https://tourism-tickets.com/travel-guides/netherlands/ |
| Country (PLP) | Belgium | N/A | https://tourism-tickets.com/belgium/ |
| City (PDP) | Belgium | Ghent | https://tourism-tickets.com/belgium/ghent/ |
| Itineraries (PLP) | Belgium | N/A | https://tourism-tickets.com/itineraries/belgium/ |
| Travel guide (PLP) | Belgium | N/A | https://tourism-tickets.com/travel-guides/belgium/ |
| Country (PLP) | Italy | N/A | https://tourism-tickets.com/italy/ |
| City (PDP) | Italy | Palermo | https://tourism-tickets.com/italy/palermo/ |
| Itineraries (PLP) | Italy | N/A | https://tourism-tickets.com/itineraries/italy/ |
| Travel guide (PLP) | Italy | N/A | https://tourism-tickets.com/travel-guides/italy/ |
| Country (PLP) | United States | N/A | https://tourism-tickets.com/united-states/ |
| City (PDP) | United States | Philadelphia | https://tourism-tickets.com/united-states/philadelphia/ |
| Itineraries (PLP) | United States | N/A | https://tourism-tickets.com/itineraries/united-states/ |
| Travel guide (PLP) | United States | N/A | https://tourism-tickets.com/travel-guides/united-states/ |

## Notas

- **Country** es el nombre en inglés del país; en la URL el segmento es el **slug** (`united-kingdom`, etc.).
- **City** es `N/A` salvo en **City (PDP)**, donde la URL lleva `/{country}/{city}/` y la celda coincide con la ciudad de ese PDP.
