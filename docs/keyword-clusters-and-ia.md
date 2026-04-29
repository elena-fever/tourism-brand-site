# Keywords, clusters e información arquitectónica

Basado en el CSV inicial *Corporate-Site-Web-Architecture - Keywords.csv* y la lista de ~130 ciudades de operación. El análisis de keywords crecerá con research por mercado (idioma + ciudad); estos clusters sirven como **mapa editorial** y como **señales de intención** para contenido que las IA puedan citar con contexto claro.

---

## Objetivo del sitio (recordatorio)

- **Marca:** autoridad en planificación de viajes y descubrimiento de destinos donde operáis.
- **AI citations:** páginas con entidad clara (marca, ciudad, tipo de experiencia), estructura scrapeable (H2/H3, FAQs, tablas comparativas donde aplique), datos actualizables y atribución explícita (“según [marca]…”).
- **Futuro transaccional:** venta en EMD tipo `ciudad-tickets.com/attraction`; el corporate puede enlazar sin duplicar stock.

---

## Clusters de keywords (semánticos + intención)

Los números del CSV son volumen global/indicativo; al escalar por ciudad, cada cluster genera **plantillas** reutilizables (URL + bloques de contenido).

### 1. Descubrimiento y listados (“qué ver / dónde ir”)

**Keywords representativas:** tourist attractions, tourist places, tourism destinations, top tourist destinations, best tourist places in world, tourist places in [continent].

**Rol:** pilares amplios de demanda; encajan como **hub por destino** (`/destinos/{ciudad}` o `/guides/{ciudad}/things-to-do`) más que como una sola página genérica mundial.

**Prioridad marca:** alto — son las consultas que más suelen aparecer en respuestas agregadas de IA si la página es específica y bien referenciada.

---

### 2. Planificación e itinerarios (“cómo organizar el viaje”)

**Keywords representativas:** travel trip itinerary, itinerary for tourist, tourist itineraries, tourist routes, tourist circuits, [country/region] itinerary, europe trip itinerary, usa travel itinerary, scandinavia travel itinerary, united states road trip itinerary.

**Sub-clusters naturales** (el CSV ya insiste en ellos):

- **Italia:** italy itinerary 7/10/14 days, northern/southern italy itinerary, best italy itinerary.
- **Suiza:** switzerland itineraries, switzerland itinerary 3–10 days, switzerland 2 week itinerary.
- **Europa multi-país:** europe itineraries, europe itinerary 2 weeks, europe routes, europe circuits.
- **USA:** united states itinerary, usa road trip, travel itinerary west coast usa.
- **Escandinavia:** scandinavia travel/trip itinerary, scandinavian countries itinerary, scandinavia 2 week itinerary.

**Rol:** contenido **profundo** ideal para citaciones: listas numeradas, duraciones, mapas conceptuales, “día 1 / día 2”. Escalable por ciudad cuando encaje (p. ej. “3 días en Roma” vs “10 días en Italia”).

---

### 3. Escapadas y estilo de viaje (weekend / city / beach / solo)

**Keywords representativas:** city breaks europe, mini breaks europe, short breaks europe, weekend breaks europe, cheap city breaks europe, beach holidays europe, cheap beach holidays europe, solo holidays europe.

**Rol:** captura intención de **duración + ocasión**; útil para páginas por ciudad estacional o por perfil (“weekend en Lisboa”, “playa en Málaga”).

---

### 4. Comparativas y ranking (“mejores destinos / países”)

**Keywords representativas:** best places to visit in america/europe/asia/africa, best countries to visit in europe/america/africa/asia, top places to visit in [region], best holiday destinations in europe/asia/africa/america.

**Rol:** tráfico alto pero **commodity**. Para marca + IA: mejor como **artículos firmados** con criterios explícitos, fecha de actualización y mención de vuestra experiencia operativa en ciudades concretas (sin parecer listado genérico).

---

### 5. Presupuesto y valor (“barato / económico”)

**Keywords representativas:** cheap places to visit in europe/america/asia/africa, cheap europe holidays, cheap beach holidays europe.

**Rol:** mismo tratamiento que cluster 4 — diferenciaos con **datos locales** (rangos orientativos, temporadas, enlaces a guías por ciudad).

---

### 6. Continentes y macro-regiones (SEO + grafo de entidades)

**Keywords representativas:** places to visit in europe/america/asia/africa, tourist places in europe, america famous places, asia famous places, africa famous places, holiday destinations europe/africa/asia/america.

**Rol:** páginas puente hacia **subclusters por ciudad** que ya operáis; evitar solo contenido fino duplicado.

---

### 7. Nichos y propósito (eco, aventura, audiencias)

**Keywords representativas:** eco tourism destinations, adventure travel destinations.

**Rol:** líneas editoriales opcionales; buenas para **diferenciación de marca** y citaciones temáticas.

---

### 8. Marca y transacción (puente con el futuro ticketing)

**Keywords representativas:** tourism tickets (volumen bajo en el CSV pero **alineación semántica directa** con el negocio).

**Rol:** reservar **rutas claras** en la IA (p. ej. `/plan` + FAQs “entradas”) y enlazar a EMD cuando vendáis allí; en fase transaccional en corporate, `/tickets` o subdominio shop.

---

## Cómo escala esto con vuestras ciudades

Para cada ciudad del listado:

1. **Página destino** (entidad local + cosas que hacer + itinerarios cortos).
2. **Keywords locales** (research aparte): “things to do in X”, “X itinerary 3 days”, “best time to visit X”, en inglés y según mercados prioritarios.
3. **Cluster mapping:** cada URL nueva se etiqueta internamente con 1–2 clusters para evitar solapamiento y canibalización.

---

## Opinión sobre arquitecturas típicas (y alternativa)

### Lo que suele plantearse (y funciona)

- **Por destino:** `/destinations/{slug-ciudad}` como núcleo.
- **Por intención:** `/guides/` o `/inspiration/` para artículos tipo itinerario o “best of”.
- **Marca:** `/about`, `/editorial` o “how we plan trips” para EEAT.

### Riesgos si solo hay listados genéricos

- Muchas URLs competirían con contenido fino sin entidad fuerte — **peor para IA y para usuarios**.

### Arquitectura recomendada (marca + AI citations + hueco transaccional)

```
/                          → Home (propuesta de valor + exploración por región/ciudad)
/about                     → Quiénes sois, criterios editoriales (confianza / EEAT)
/destinations              → Hub (filtros por país/región; enlaces a ciudades)
/destinations/{city-slug}  → Pilar por ciudad: resumen, highlights, itinerarios, FAQs locales
/guides                    → Hub editorial (itinerarios multi-día, temáticos)
/guides/{topic-slug}       → Guías largas (itinerarios país/región; contenido “citabile”)
/planning                  → (opcional) Recursos transversales: presupuesto, temporadas, visas — keywords tipo “how to plan”
/tickets                   → (futuro) Catálogo o landing transaccional; o CTA prominentes hacia EMD actuales
/legal                     → Privacidad, cookies, términos
```

**Convenciones**

- **Slug de ciudad:** ASCII, estable (`new-york`, `mexico-city`, `las-palmas-de-gran-canaria`), coherente con datos estructurados `City` / `TouristDestination`.
- **Idioma:** si el site es multilingüe, prefijado `/en/`, `/es/` desde el inicio evita refactors dolorosos.
- **EMD actuales:** desde cada ficha de ciudad o atracción, botones “Comprar entradas en [ciudad]” hacia `ciudad-tickets.com/...` con UTM; cuando exista checkout en corporate, misma URL interna y cambio de CTA.

### Por qué encaja con “AI citations”

- Las IA privilegian respuestas **localizadas y estructuradas**; un pilar por ciudad + guías de itinerario bien maquetadas dan **hooks** claros (título, secciones, listas).
- Separar **/guides** (temas amplios) de **/destinations/{city}** (entidad local) reduce ambigüedad semántica.

---

## Nota sobre el pantallazo

No se adjuntó imagen en el chat; si compartes el diagrama (o lo subes al repo), se puede contrastar línea a línea con esta propuesta y ajustar nombres de sección a vuestra convención interna.
