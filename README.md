# VIA Chapter III — Ultima Thule Route Planner

A single-file web application for planning and compliance-checking routes for the **VIA Chapter III — Ultima Thule** ultra-distance cycling race (Amerongen, Netherlands → Volda, Norway, ~4,000km, 24 July–8 August 2026).

Built on [RideWithGPS](https://ridewithgps.com), [Leaflet.js](https://leafletjs.com), and [OSRM](https://project-osrm.org).

---

## Features

### 🗺 Live Map
- Interactive Leaflet map with all 26 waypoints (gates, ferries, refuge, start/finish) shown as labelled markers
- **🗺 Official Map** button overlays the official VIA Google My Maps for reference
- Map splits into a top/bottom view when a compliance report is open

### ⛅ Gate Weather
- **3-day forecast** for every gate, fetched automatically when you select a gate
- Shows daily high/low temperature, wind speed and direction, precipitation, and a weather condition summary
- Powered by [Open-Meteo](https://open-meteo.com) (free, no API key needed)
- Toggle the forecast on/off per gate with the **⛅ Weather** button
- 30-minute in-memory cache — forecasts stay fresh without hammering the API

### 🚴 My Routes — Compliance Inspector
- Loads all your RideWithGPS routes (paginated, handles large libraries)
- Fetches full track geometry via the RWGPS API and runs a compliance check against:
  - **15 banned tunnels** (Laerdalstunnelen, Gudvangatunnelen, Innfjordtunnelen, and 12 others)
  - **6 banned road sections** (E39 Vassenden–Skei, E6 Sel–Dombås, and others)
  - **17 banned ferries** (Øresund bridge, Hirtshals, Göteborg, Malmö, Oslo, Kiel, and others)
  - **18 mandatory gate proximity checks** (400–500m radius per gate)
  - **30 recommended corridor checkpoints** grouped by leg with efficiency notes
- Compliance report shows: violation count, gates missed/hit, routing advisories, full gate coverage grid
- Violations pinned on map with one-click "Reroute from here ↗" links to RideWithGPS
- **GPX upload fallback** — if the API blocks private route data, export from RWGPS and upload locally (nothing is sent anywhere)
- Manual route inspection by ID if route list fails to load

### ✚ Create — Ad-Hoc Road-Routed Planning
Use the Create tab as a **quick draft routing tool** — select legs, pick ferries, drop pins, preview on real roads, and export. The result is a solid rough draft you can refine in RideWithGPS, Komoot, Strava, or any other routing tool.

- Select any combination of the 9 race legs and toggle individual ferries on/off
- **Preview on Road Network** — routes each land segment via the OSRM public cycling API, showing actual cycling roads colour-coded by leg
- Ferry crossings shown as dashed lines (OSRM correctly skips water)
- Progress overlay with per-segment status during routing
- **Push directly to RideWithGPS** — opens immediately in the route editor for further refinement
- **Download as GPX** — import into Komoot, Strava, Garmin Connect, Wahoo, or any GPX-compatible tool
- Waypoints-only GPX also available for loading gate markers into a head unit

### 📌 Pins — Ad-Hoc Waypoints
Drop custom pins anywhere on the map to add personal waypoints to your route planning — a hotel, a detour point, a resupply stop, or an alternative road junction.

- Tap **📌 Add Pin** on the map to place a waypoint at any location
- Name each pin — it appears in the Pins tab with its distance to your loaded route
- Check **"Use as routing via-point"** on a pin in the Pins tab to include it in road-routed previews and GPX exports; unchecked pins are saved but not routed through
- Pins are included in routing in the order they appear in the Pins tab — drag to reorder
- Saved to your browser — pins persist between sessions
- Use pins to sketch detours or alternatives before committing to a full routing app

### ⛺ POIs — Drinking Water, Campgrounds and Restrooms
- Zoom in on the map and toggle the POI menu
- Water sources, campgrounds and restrooms populate and adjust based on zoom level
- POI popups include Google Maps links for further inspection

---

## Getting Started

Open the app directly in your browser — no install, no server, no dependencies.

---

## Login

Sign in with your **RideWithGPS** email and password. Credentials are sent directly to `ridewithgps.com/users/current.json` — this app never sees or stores them. Only the returned `auth_token` is saved in your browser's `localStorage` for the session.

---

## Race Rules Encoded

### Banned tunnels (15)
| Tunnel | Location | Alternative |
|---|---|---|
| Laerdalstunnelen | Near Borgund | Rv50 Filefjell mountain road |
| Gudvangatunnelen | Near Flåm | Stalheimskleiva old road |
| Innfjordtunnelen | Near Åndalsnes | Rv63 from north |
| Hellesylt tunnel | Sunnmøre | Southbound only permitted |
| Flenjatunnelen | Lærdal corridor | Overground roads |
| Eiksund tunnel | Volda/Ørsta | Lote–Anda, Festøya, Lauvstad–Volda ferries |
| Rotsethorntunnelen | Volda | Ferry chain |
| Hjartåbergtunnelen | Volda | Ferry chain |
| Oppljostunnelen | Strynefjellsveg | Gamle Strynefjellsveg |
| Kvivstunnelen | Gaularfjellet | Old mountain road |
| Fodnestunnelen | Urnes/Solvorn | Overground road via Gaupne |
| Amlatunnelen | Urnes/Solvorn | Overground roads |
| Morkaaastunnelen | Volda | Ferry chain |
| Selvågtunnelen | Ørsta/Volda | Lote–Anda → Festøya → Lauvstad–Volda |
| Tunnel near Dovre | Dombås | Rv15 or valley roads |

### Banned road sections (6)
- E39 Vassenden–Skei → use Fv13 (Gaularfjellet)
- E39 Sandane section → use Fv60/Fv615
- E6 Sel–Dombås → use Rv15 via Otta or Rv27
- E39 Ørstavegen (Volda) → arrive via Lauvstad–Volda ferry
- E39 Voldavegen section → arrive via ferry chain
- E39 from Festøya → use Festøya then Lauvstad–Volda ferry

### Banned crossings (17)
All DK→SE crossings except **Helsingør–Helsingborg ferry** are banned (Øresund bridge, Malmö, Trelleborg, Ystad, Göteborg, Hirtshals). Also banned: Rostock–Gedser, Travemünde, Kiel, Oslo, Strömstad–Sandefjord, Bergen fast boat, and several Norwegian fjord ferries.

### Mandatory gates (16 + start/finish)
S · I · II · III · IV · V · VI · VII · VIII · IX · X · XI · XII · XIII · XIV · XV · XVI · F

---

## Route Structure

| Leg | Section | Distance |
|---|---|---|
| L1 | Start (Amerongen) → Gate I (Brocken, 1,141m) | ~480km |
| L2 | Brocken → Gate II (Fredriksten) via Denmark & Sweden | ~620km |
| L3 | Gate II → Gate III (Suleskard, 1,050m) + Refuge | ~380km |
| L4 | Gate IV (Lysebotn) + Lysebotn–Forsand ferry | ~60km |
| L5 | Gate V (Vøringsfossen) · IX (Borgund) · X (Urnes) · XI (Lom) | ~420km |
| L6 | Gate VI (Sognefjellet, 1,434m) · VII (Gaularfjellet) · VIII (Strynefjellsveg) | ~280km |
| L7 | Gate XIV (Dalsnibba, 1,476m) · XIII (Trollstigen) · XII (Svøufallet) | ~310km |
| L8 | Gate XV (Atlantic Ocean Road) | ~80km |
| L9 | Gate XVI (Vestkapp) → Finish (Volda) via ferry chain | ~120km |

---

## Permitted Ferries

The full list of permitted and banned ferries — including Danish island crossings, Elbe crossings, Hardangerfjord, Sognefjord, and the Volda finish chain — is available in the **⛴ Ferries** panel of the Create tab in the tool. Green rows are permitted; red rows are banned.

---

## Key Dates

| Date | Event |
|---|---|
| 23 July 2026 | Sign-on 09:00–17:00, community meal 19:00 |
| 24 July 2026 | Race start 07:00, De Proloog, Amerongen NL |
| 8 August 2026 | Finish celebration 20:00, Volda NO |

---

## Technical Notes

### APIs used
- **RideWithGPS** — authentication, route library, route creation (`ridewithgps.com`)
- **OSRM public cycling API** — road-following routing between waypoints (`router.project-osrm.org`)
- **CartoDB Voyager tiles** — map background (via Leaflet)

### Routing logic
- Land segments: routed via OSRM cycling profile, polylines drawn in leg colours
- Ferry crossings: dashed lines (OSRM skips water; segments departing from a `ferry`-typed waypoint are always dashed)
- Fallback: if OSRM fails a land segment, a faint dashed straight line is drawn and counted in the fallback segment tally
- RWGPS route creation: track points are sampled to ≤2,000 points if the preview exceeds that limit

### Compliance detection
Track points are sampled every 3rd point for performance. Detection radii are 300m for tunnels, 400–500m for roads/ferries, and 400–500m for gates. Corridor advisories use larger radii (2–20km depending on the checkpoint).

### Privacy
- No data is sent to any server other than `ridewithgps.com` and `router.project-osrm.org`
- GPX upload for compliance checking runs entirely in-browser
- Only the RWGPS `auth_token` is persisted (in `localStorage`)

---

## File Structure

```
via_chapter3_planner.html   # entire app — HTML, CSS, JS in one file
README.md                   # this file
```

---

## Credits

Race organised by [VIA](https://via-race.com/). Route data sourced from the official race KML and compendium (October 2025). Routing powered by [OSRM](https://project-osrm.org) and [OpenStreetMap](https://www.openstreetmap.org) contributors.
