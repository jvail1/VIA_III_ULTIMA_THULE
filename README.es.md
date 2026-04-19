# VIA Capítulo III — Planificador de ruta Ultima Thule

Una aplicación web de archivo único para planificar y verificar la conformidad de rutas para la carrera ciclista de ultra distancia **VIA Capítulo III — Ultima Thule** (Amerongen, Países Bajos → Volda, Noruega, ~4.000 km, 24 de julio–8 de agosto de 2026).

Desarrollado con [RideWithGPS](https://ridewithgps.com), [Leaflet.js](https://leafletjs.com) y [OSRM](https://project-osrm.org).

---

## Funcionalidades

### 🗺 Mapa en vivo
- Mapa interactivo Leaflet con los 26 puntos de paso (puertas, ferris, refugio, salida/llegada) mostrados como marcadores etiquetados
- Superposición de **ruta recomendada** en naranja discontinuo para las 9 etapas, activable/desactivable desde la leyenda del mapa
- El mapa se divide en vista superior/inferior cuando se abre un informe de conformidad

### 🚴 Mis rutas — Inspector de conformidad
- Carga todas sus rutas de RideWithGPS (paginado, gestiona bibliotecas grandes)
- Obtiene la geometría completa del trazado a través de la API de RWGPS y ejecuta una verificación de conformidad frente a:
  - **15 túneles prohibidos** (Laerdalstunnelen, Gudvangatunnelen, Innfjordtunnelen y 12 más)
  - **6 secciones de carretera prohibidas** (E39 Vassenden–Skei, E6 Sel–Dombås y otras)
  - **17 ferris prohibidos** (puente de Øresund, Hirtshals, Göteborg, Malmö, Oslo, Kiel y otros)
  - **18 verificaciones de proximidad de puertas obligatorias** (radio de 400–500 m por puerta)
  - **30 puntos de control de corredor recomendados** agrupados por etapa con notas de eficiencia
- El informe de conformidad muestra: número de infracciones, puertas omitidas/alcanzadas, recomendaciones de rutas, cuadrícula completa de cobertura de puertas
- Infracciones marcadas en el mapa con enlaces de un clic «Recalcular desde aquí ↗» a RideWithGPS
- **Carga GPX de respaldo** — si la API bloquea datos de rutas privadas, exporte desde RWGPS y cargue localmente (no se envía nada a ningún servidor)
- Inspección manual de ruta por ID si la lista de rutas no se carga

### ✚ Crear — Planificación con rutas en red vial
- Seleccione cualquier combinación de las 9 etapas de la carrera
- **Vista previa en la red vial** — traza cada segmento terrestre a través de la API pública de ciclismo OSRM, mostrando las carreteras reales codificadas por color según la etapa
- Los cruces en ferri se muestran como líneas discontinuas (OSRM omite el agua correctamente)
- Superposición de progreso con estado por segmento durante el cálculo de la ruta
- Envío directo de la ruta completada a su cuenta de RideWithGPS (hasta 2.000 puntos de trazado)
- Descarga como **GPX con ruta vial** (trazado `<trk>` completo + waypoints `<wpt>`) o solo waypoints en GPX

### ✚ Visualización de PDI: agua potable, campings y aseos
- Acerque el zoom en el mapa y active el menú de PDI.
- Las fuentes de agua, campings y aseos se mostrarán y ajustarán según el nivel de zoom. Las ventanas emergentes de PDI incluyen enlaces a Google Maps para una inspección más detallada.

---

## Primeros pasos

Abra la aplicación directamente en su navegador — sin instalación, sin servidor, sin dependencias.

---

## Inicio de sesión

Inicie sesión con su correo electrónico y contraseña de **RideWithGPS**. Las credenciales se envían directamente a `ridewithgps.com/users/current.json` — esta aplicación nunca las ve ni las almacena. Solo el `auth_token` devuelto se guarda en el `localStorage` de su navegador durante la sesión.

---

## Reglas de carrera codificadas

### Túneles prohibidos (15)
| Túnel | Ubicación | Alternativa |
|---|---|---|
| Laerdalstunnelen | Cerca de Borgund | Carretera de montaña Rv50 Filefjell |
| Gudvangatunnelen | Cerca de Flåm | Carretera antigua Stalheimskleiva |
| Innfjordtunnelen | Cerca de Åndalsnes | Rv63 desde el norte |
| Túnel de Hellesylt | Sunnmøre | Solo permitido en dirección sur |
| Flenjatunnelen | Corredor de Lærdal | Carreteras en superficie |
| Túnel de Eiksund | Volda/Ørsta | Ferris Lote–Anda, Festøya, Lauvstad–Volda |
| Rotsethorntunnelen | Volda | Cadena de ferris |
| Hjartåbergtunnelen | Volda | Cadena de ferris |
| Oppljostunnelen | Strynefjellsveg | Gamle Strynefjellsveg |
| Kvivstunnelen | Gaularfjellet | Carretera de montaña antigua |
| Fodnestunnelen | Urnes/Solvorn | Carretera en superficie vía Gaupne |
| Amlatunnelen | Urnes/Solvorn | Carreteras en superficie |
| Morkaaastunnelen | Volda | Cadena de ferris |
| Selvågtunnelen | Ørsta/Volda | Lote–Anda → Festøya → Lauvstad–Volda |
| Túnel cerca de Dovre | Dombås | Rv15 o carreteras de valle |

### Secciones de carretera prohibidas (6)
- E39 Vassenden–Skei → usar Fv13 (Gaularfjellet)
- Sección E39 Sandane → usar Fv60/Fv615
- E6 Sel–Dombås → usar Rv15 vía Otta o Rv27
- E39 Ørstavegen (Volda) → llegar vía ferri Lauvstad–Volda
- Sección E39 Voldavegen → llegar vía cadena de ferris
- E39 desde Festøya → usar Festøya y luego ferri Lauvstad–Volda

### Cruces prohibidos (17)
Todos los cruces DK→SE excepto el **ferri Helsingør–Helsingborg** están prohibidos (puente de Øresund, Malmö, Trelleborg, Ystad, Göteborg, Hirtshals). También prohibidos: Rostock–Gedser, Travemünde, Kiel, Oslo, Strömstad–Sandefjord, barco rápido de Bergen y varios ferris de fiordos noruegos.

### Puertas obligatorias (16 + salida/llegada)
S · I · II · III · IV · V · VI · VII · VIII · IX · X · XI · XII · XIII · XIV · XV · XVI · F

---

## Estructura de la ruta

| Etapa | Sección | Distancia |
|---|---|---|
| L1 | Salida (Amerongen) → Puerta I (Brocken, 1.141 m) | ~480 km |
| L2 | Brocken → Puerta II (Fredriksten) vía Dinamarca y Suecia | ~620 km |
| L3 | Puerta II → Puerta III (Suleskard, 1.050 m) + Refugio | ~380 km |
| L4 | Puerta IV (Lysebotn) + ferri Lysebotn–Forsand | ~60 km |
| L5 | Puerta V (Vøringsfossen) · IX (Borgund) · X (Urnes) · XI (Lom) | ~420 km |
| L6 | Puerta VI (Sognefjellet, 1.434 m) · VII (Gaularfjellet) · VIII (Strynefjellsveg) | ~280 km |
| L7 | Puerta XIV (Dalsnibba, 1.476 m) · XIII (Trollstigen) · XII (Svøufallet) | ~310 km |
| L8 | Puerta XV (Carretera del Océano Atlántico) | ~80 km |
| L9 | Puerta XVI (Vestkapp) → Llegada (Volda) vía cadena de ferris | ~120 km |

---

## Ferris permitidos

La lista completa de ferris permitidos y prohibidos — incluidos los cruces entre islas danesas, los cruces del Elba, el Hardangerfjord, el Sognefjord y la cadena de ferris hasta Volda — está disponible en el panel **⛴ Ferris** de la pestaña Crear. Las filas verdes están permitidas; las rojas están prohibidas.

---

## Fechas clave

| Fecha | Evento |
|---|---|
| 23 de julio de 2026 | Registro 09:00–17:00, comida comunitaria 19:00 |
| 24 de julio de 2026 | Salida de la carrera 07:00, De Proloog, Amerongen NL |
| 8 de agosto de 2026 | Celebración de la llegada 20:00, Volda NO |

---

## Notas técnicas

### APIs utilizadas
- **RideWithGPS** — autenticación, biblioteca de rutas, creación de rutas (`ridewithgps.com`)
- **API pública de ciclismo OSRM** — enrutamiento siguiendo carreteras entre waypoints (`router.project-osrm.org`)
- **Tiles CartoDB Voyager** — fondo de mapa (vía Leaflet)

### Lógica de enrutamiento
- Segmentos terrestres: enrutados mediante el perfil ciclista de OSRM, polilíneas dibujadas en colores de etapa
- Cruces en ferri: líneas discontinuas (OSRM omite el agua; los segmentos que parten de un waypoint de tipo `ferry` son siempre discontinuos)
- Alternativa: si OSRM falla en un segmento terrestre, se dibuja una línea recta discontinua tenue y se contabiliza en el recuento de segmentos alternativos
- Creación de ruta RWGPS: los puntos de trazado se muestrean a ≤2.000 puntos si la vista previa supera ese límite

### Detección de conformidad
Los puntos de trazado se muestrean cada 3 puntos por rendimiento. Los radios de detección son 300 m para túneles, 400–500 m para carreteras/ferris y 400–500 m para puertas. Los avisos de corredor usan radios mayores (2–20 km según el punto de control).

### Privacidad
- No se envían datos a ningún servidor que no sea `ridewithgps.com` y `router.project-osrm.org`
- La carga de GPX para la verificación de conformidad se ejecuta completamente en el navegador
- Solo el `auth_token` de RWGPS se conserva (en `localStorage`)

---

## Estructura de archivos

```
via_chapter3_planner.html   # aplicación completa — HTML, CSS, JS en un solo archivo
README.md                   # este archivo
```

---

## Créditos

Carrera organizada por [VIA](https://via-race.com/). Datos de ruta procedentes del KML oficial de la carrera y el compendium (octubre de 2025). Enrutamiento impulsado por [OSRM](https://project-osrm.org) y los colaboradores de [OpenStreetMap](https://www.openstreetmap.org).
