# VIA Race III — Ultima Thule: Project Context

## Project overview

Post-race analysis and results dashboard for **VIA Race Chapter III - Ultima Thule**
(`event_slug: via-race-26`), an ultra-distance cycling race from the Netherlands to
Norway (~4,000 km). Data exported 2026-09-02.

---

## Files

| File | Description |
|------|-------------|
| `via_race_26_export.json` | 63 MB post-race GPS export — **not committed to git** (add to `.gitignore`) |
| `via_race_26_export.zip` | Zipped version of the above |
| `VIA Chapter III - RACE Route & Locations.kml` | Race route KML — 19 mandatory gates, banned roads/tunnels/ferries |
| `via_race_dashboard.py` | Streamlit dashboard (see below) |
| `via_race_26_leaderboard.png` | Official 32-finisher leaderboard PNG |
| `.streamlit/config.toml` | Dark theme config for the dashboard |

---

## JSON data schema

Top-level keys: `event_slug`, `event_name`, `exported_at`, `participants`

### Participant object

```json
{
  "first_name": "Jason",
  "last_name":  "Vail",
  "bib":        "157",
  "variant":    "Race",      // "Race" or "Adventure"
  "category":   "M",         // "M", "F", or "Pair"
  "status":     "REGISTERED",
  "points":     [...]
}
```

> **Important**: The `status` field in the export is **unreliable / stale**.
> Many riders who completed the race are marked `REGISTERED`.
> Always derive status from gate compliance (see below).

### GPS point object

```json
{
  "ts":           "2026-07-24T05:30:59",
  "lat":          52.003672,
  "lon":          5.461571,
  "alt":          50.5,
  "speed":        0.0,         // km/h
  "azimuth":      0,
  "gps_accuracy": 1,
  "battery":      94,
  "temperature":  20.3,
  "odo":          4546.2       // cumulative device odometer (km) — NOT race distance
}
```

**Total distance** = `pts[-1]["odo"] - pts[0]["odo"]`

---

## KML gates

Parse with `xml.etree.ElementTree`, namespace `http://www.opengis.net/kml/2.2`.
Folder name: `"Mandatory Locations - Race"` — contains **19 mandatory gates**.

Gates (in route order):
1. De Proloog, Amerongen *(START)*
2. Brocken
3. Fredriksten fortress
4. Botn Fjellstue
5. Suleskard
6. Lysebotn
7. Vøringfossen
8. Sognefjellet
9. Gaularfjellet
10. Strynefjellsveg
11. Borgund Stavkyrkje
12. Urnes stavkyrkje
13. Lom Stavkyrkje
14. Svøufallet
15. Atlantic road
16. Trollstigen
17. Dalsnibba
18. Vestkapp
19. Volda *(FINISH)*

---

## Key conventions & decisions

### Language
**Python only.** pandas for tabular data, plotly for interactive charts, matplotlib for
exported PNGs, folium for standalone HTML maps.

### Gate detection radius
**1,000 m** (haversine). 500 m produced false negatives on legitimately-ridden gates.

### Derived status (use this, not the raw `status` field)
```
gates_hit == 19  AND  t_finish is not None  →  FINISHED
len(pts) >= 2    AND  gates_hit < 19        →  DNF
len(pts) < 2                                →  DNS
```
Filter to `variant == "Race"` for the main results table.

### Gate ordering rules
Not all gates have the same ordering constraint:

| Type | Gates | Rule |
|------|-------|------|
| **Ordered** | De Proloog → Brocken → Fredriksten → Suleskard (gates 1, 2, 3, 5) | Must be visited in this exact sequence |
| **Required refuge** | Botn Fjellstue (gate 4) | Must be visited, but at any point in the ride |
| **Free-order** | All remaining 14 gates | Must be visited, any order |

> **Note:** Botn Fjellstue is a refuge, not a checkpoint gate — it sits between
> Fredriksten and Suleskard in the KML list but riders are free to visit it whenever.
> Nearly all riders hit Suleskard before Botn, which is geographically natural and
> completely compliant. All 32 confirmed finishers respected the correct ordering.

### Race time
Compute `total_days` as **start gate → finish gate** using the first timestamp within
1,000 m of each endpoint — **not** raw first/last ping (trackers run before & after racing).

### Elevation gain
Clip altitude to `(-100, 2500)` m (valid range for NL→NO route), forward-fill outliers,
then sum only positive diffs `> 5 m` to suppress GPS noise.

### Moving speed threshold
Speed `> 2 km/h` counts as riding time.

### Plotly version
**Plotly 7** — use `go.Scattermap` (not `Scattermapbox`), `map_style=`, `map=dict()`
(not `mapbox_style=`, `mapbox=dict()`).

---

## Official finisher overrides

These riders missed the Volda finish gate by ~1,700 m but are confirmed official
finishers. They are hardcoded in `OFFICIAL_FINISHER_OVERRIDES` in `via_race_dashboard.py`.

| Rider | Rank | total_days | ride_time_hrs | avg_speed_kmh |
|-------|------|-----------|---------------|---------------|
| Adam Bialek | #1 | 8.62 | 162.1 | 21.5 |
| Bruno Wicht | #2 | 8.91 | — | — |
| Jair Hoogland | #3 | 9.49 | 175.1 | 19.6 |

To add another override, append to `OFFICIAL_FINISHER_OVERRIDES` in the dashboard.

---

## Streamlit dashboard

**Run:** `streamlit run via_race_dashboard.py --server.port 8501`

**Tabs:**

| Tab | Contents |
|-----|----------|
| 🏆 Leaderboard | Stacked bar (riding vs rest), sorted by elapsed race time, hover for full metrics |
| 🚴 Rider Profile | KPI cards, speed + elevation time-series (clipped to race window), gate compliance table |
| ✅ Gate Compliance | Heatmap matrix — all Race riders × 19 gates |
| 🗺️ Route Map | GPS tracks (up to 10 riders) + mandatory gate markers, `open-street-map` tiles |

**Sidebar controls:** status filter, rider selector (drives Profile + Map default), summary counts.

**Known gotcha:** The Route Map multiselect uses `key="map_riders_select"` with session-state
pre-cleaning to avoid `StreamlitDefaultNotInOptionsError` when the status filter changes.

---

## Race summary (as of 2026-09-02 export)

| | Count |
|---|---|
| Total participants | 104 |
| Race variant | 62 |
| Adventure variant | 42 |
| Confirmed Race finishers | 32 |
| Race DNF | 25 |
| Race DNS | 5 |

Race started: **2026-07-24 ~05:30 UTC** at De Proloog, Amerongen (NL)
