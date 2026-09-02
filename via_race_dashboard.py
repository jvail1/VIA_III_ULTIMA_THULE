"""
VIA Race III — Ultima Thule Dashboard
Streamlit app for exploring race GPS data, gate compliance, and rider profiles.
"""

import json
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
import pandas as pd  # noqa: E402 — must precede OFFICIAL_FINISHER_OVERRIDES constant
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ── Page config ───────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="VIA Race III Dashboard",
    page_icon="🚴",
    layout="wide",
)

# ── Constants ─────────────────────────────────────────────────────────────────

DATA_PATH  = "via_race_26_export.json"
KML_PATH   = "VIA Chapter III - RACE Route & Locations.kml"
RADIUS_M   = 1000

STATUS_COLORS = {
    "FINISHED": "#2ecc71",
    "DNF":      "#e74c3c",
    "DNS":      "#95a5a6",
}

# Riders confirmed as official finishers by race organisers, overriding gate check.
# Values are column overrides applied after build_race_df().
OFFICIAL_FINISHER_OVERRIDES = {
    "Bruno Wicht":  {},
    "Adam Bialek":  {
        "total_days":    8.62,
        "race_finish":   pd.Timestamp("2026-08-01 20:23:29"),
        "ride_time_hrs": 162.1,
        "avg_speed_kmh": 21.5,
    },
    "Jair Hoogland": {
        "total_days":    9.49,
        "race_finish":   pd.Timestamp("2026-08-02 17:11:02"),
        "ride_time_hrs": 175.1,
        "avg_speed_kmh": 19.6,
    },
}

# ── Helpers ───────────────────────────────────────────────────────────────────

def haversine_min(lats, lons, gate_lat, gate_lon):
    R = 6_371_000
    dlat = np.radians(gate_lat - lats)
    dlon = np.radians(gate_lon - lons)
    a = (np.sin(dlat / 2) ** 2
         + np.cos(np.radians(lats)) * np.cos(np.radians(gate_lat)) * np.sin(dlon / 2) ** 2)
    return R * 2 * np.arcsin(np.sqrt(a).clip(0, 1)).min()


def first_gate_hit(lats, lons, ts, gate_lat, gate_lon, radius=RADIUS_M):
    R = 6_371_000
    dlat = np.radians(gate_lat - lats)
    dlon = np.radians(gate_lon - lons)
    a = (np.sin(dlat / 2) ** 2
         + np.cos(np.radians(lats)) * np.cos(np.radians(gate_lat)) * np.sin(dlon / 2) ** 2)
    dists = R * 2 * np.arcsin(np.sqrt(a).clip(0, 1))
    hits = np.where(dists <= radius)[0]
    return ts[hits[0]] if len(hits) else None


def compute_elev_gain(pts, valid_range=(-100, 2500), step_threshold=5):
    alts = np.array([p["alt"] for p in pts], dtype=float)
    alts[(alts < valid_range[0]) | (alts > valid_range[1])] = np.nan
    alts = pd.Series(alts).ffill().bfill().values
    return float(np.diff(alts)[np.diff(alts) > step_threshold].sum())


# ── Cached data loaders ───────────────────────────────────────────────────────

@st.cache_data
def load_raw():
    with open(DATA_PATH) as f:
        return json.load(f)


@st.cache_data
def load_gates():
    tree = ET.parse(KML_PATH)
    root = tree.getroot()
    ns = {"kml": "http://www.opengis.net/kml/2.2"}
    gates = []
    for folder in root.findall(".//kml:Folder", ns):
        if "Mandatory" in (folder.findtext("kml:name", namespaces=ns) or ""):
            for pm in folder.findall("kml:Placemark", ns):
                name = pm.findtext("kml:name", namespaces=ns)
                coords = pm.findtext(".//kml:coordinates", namespaces=ns)
                if coords:
                    lon, lat, *_ = map(float, coords.strip().split(","))
                    gates.append({"gate": name, "lat": lat, "lon": lon})
    return pd.DataFrame(gates)


@st.cache_data
def build_race_df(_raw, _gates):
    gate_list = _gates["gate"].tolist()
    start_g   = _gates[_gates["gate"] == "De Proloog, Amerongen"].iloc[0]
    finish_g  = _gates[_gates["gate"] == "Volda"].iloc[0]

    rows = []
    for rider in _raw["participants"]:
        if rider["variant"] != "Race":
            continue

        pts  = rider["points"]
        name = f"{rider['first_name']} {rider['last_name']}"
        base = {"name": name, "bib": rider["bib"]}

        if len(pts) < 2:
            row = {**base, "status": "DNS", "gates_hit": 0,
                   "total_dist_km": None, "elev_gain_m": None,
                   "avg_speed_kmh": None, "total_days": None,
                   "ride_time_hrs": None, "race_start": None, "race_finish": None}
            for g in gate_list:
                row[g] = None
            rows.append(row)
            continue

        lats   = np.array([p["lat"] for p in pts])
        lons   = np.array([p["lon"] for p in pts])
        ts     = pd.to_datetime([p["ts"] for p in pts])
        speeds = np.array([p["speed"] for p in pts])

        # Gate distances & hit count
        gate_dists = {
            g["gate"]: round(haversine_min(lats, lons, g["lat"], g["lon"]))
            for _, g in _gates.iterrows()
        }
        gates_hit = sum(1 for d in gate_dists.values() if d <= RADIUS_M)

        # Race window from start → finish gate
        t_start  = first_gate_hit(lats, lons, ts, start_g["lat"], start_g["lon"])
        t_finish = first_gate_hit(lats, lons, ts, finish_g["lat"], finish_g["lon"])

        # Distance & elevation (full track)
        total_dist = round(pts[-1]["odo"] - pts[0]["odo"], 1)
        elev_gain  = round(compute_elev_gain(pts))

        # Time metrics clipped to race window
        if t_start and t_finish:
            in_race    = (ts >= t_start) & (ts <= t_finish)
            ts_r, spd_r = ts[in_race], speeds[in_race]
            total_days  = (t_finish - t_start).total_seconds() / 86400
            if len(ts_r) >= 2:
                dt_sec   = np.diff(ts_r).astype("timedelta64[s]").astype(float)
                ride_hrs = dt_sec[spd_r[:-1] > 2].sum() / 3600
            else:
                ride_hrs = None
            avg_speed = round(total_dist / ride_hrs, 1) if ride_hrs else None
        else:
            total_days = ride_hrs = avg_speed = None

        status = (
            "FINISHED" if gates_hit == 19 and t_finish is not None
            else "DNF"
        )

        row = {
            **base,
            "status":        status,
            "gates_hit":     gates_hit,
            "total_dist_km": total_dist,
            "elev_gain_m":   elev_gain,
            "avg_speed_kmh": avg_speed,
            "total_days":    round(total_days, 2) if total_days else None,
            "ride_time_hrs": round(ride_hrs, 1) if ride_hrs else None,
            "race_start":    t_start,
            "race_finish":   t_finish,
        }
        row.update(gate_dists)
        rows.append(row)

    df = pd.DataFrame(rows)

    # Apply official finisher overrides
    for name, extras in OFFICIAL_FINISHER_OVERRIDES.items():
        mask = df["name"] == name
        if mask.any():
            df.loc[mask, "status"]    = "FINISHED"
            df.loc[mask, "gates_hit"] = 19
            for col, val in extras.items():
                df.loc[mask, col] = val

    return df, gate_list


GATE_SHORT = {
    "De Proloog, Amerongen": "Start",
    "Brocken":               "Brocken",
    "Fredriksten fortress":  "Fredriksten",
    "Botn Fjellstue":        "Botn",
    "Suleskard":             "Suleskard",
    "Lysebotn":              "Lysebotn",
    "Vøringfossen":          "Vøringfossen",
    "Sognefjellet":          "Sognefjellet",
    "Gaularfjellet":         "Gaularfjellet",
    "Strynefjellsveg":       "Strynefjell",
    "Borgund Stavkyrkje":    "Borgund",
    "Urnes stavkyrkje":      "Urnes",
    "Lom Stavkyrkje":        "Lom",
    "Svøufallet":            "Svøufallet",
    "Atlantic road":         "Atlantic Rd",
    "Trollstigen":           "Trollstigen",
    "Dalsnibba":             "Dalsnibba",
    "Vestkapp":              "Vestkapp",
    "Volda":                 "Volda",
}

ORDERED_GATES = [
    "De Proloog, Amerongen",
    "Brocken",
    "Fredriksten fortress",
    "Suleskard",
    "Lysebotn",          # gate 5 — ordered, not free
]
REFUGE_GATE = "Botn Fjellstue"

GATE_TYPE = {}  # populated after gate_cols is known


def gate_type_label(gate):
    if gate in ORDERED_GATES:
        return "🔵 Ordered"
    if gate == REFUGE_GATE:
        return "🟡 Refuge"
    return "⚪ Free"


@st.cache_data
def build_gate_visit_order(_raw, _gates, radius=RADIUS_M):
    """For every Race rider, return each gate's first-hit timestamp."""
    gate_list = _gates["gate"].tolist()
    rows = []
    for rider in _raw["participants"]:
        if rider["variant"] != "Race":
            continue
        pts = rider["points"]
        name = f"{rider['first_name']} {rider['last_name']}"
        if len(pts) < 2:
            continue
        lats   = np.array([p["lat"] for p in pts])
        lons   = np.array([p["lon"] for p in pts])
        ts     = pd.to_datetime([p["ts"] for p in pts])
        R_m    = 6_371_000
        for _, gate in _gates.iterrows():
            dlat  = np.radians(gate["lat"] - lats)
            dlon  = np.radians(gate["lon"] - lons)
            a     = (np.sin(dlat / 2) ** 2
                     + np.cos(np.radians(lats)) * np.cos(np.radians(gate["lat"]))
                     * np.sin(dlon / 2) ** 2)
            dists = R_m * 2 * np.arcsin(np.sqrt(a).clip(0, 1))
            within = np.where(dists <= radius)[0]
            if len(within):
                rows.append({
                    "name":       name,
                    "gate":       gate["gate"],
                    "visited_at": ts[within[0]],
                })

    df = pd.DataFrame(rows)
    if df.empty:
        return df

    # Add visit order per rider (1 = first gate hit)
    df = df.sort_values(["name", "visited_at"])
    df["visit_order"] = df.groupby("name").cumcount() + 1
    return df


@st.cache_data
def build_gate_popularity(_visit_df, finisher_names, all_gate_cols, short_map):
    """For each stop position 1-19, count how many finishers visited each gate."""
    fin_visits = _visit_df[_visit_df["name"].isin(finisher_names)].copy()
    n = len(finisher_names)

    pop = (fin_visits
           .groupby(["visit_order", "gate"])
           .size()
           .reset_index(name="count")
           .rename(columns={"visit_order": "stop"}))

    # Consensus: most common gate per stop
    consensus = (pop.sort_values("count", ascending=False)
                    .groupby("stop", as_index=False)
                    .first()[["stop", "gate", "count"]]
                    .sort_values("stop")
                    .reset_index(drop=True))
    consensus["pct"] = (consensus["count"] / n * 100).round(0).astype(int)

    # Popularity pivot: stop × gate → rider count
    # Order columns by mean visit position across finishers
    col_mean_order = (fin_visits.groupby("gate")["visit_order"]
                      .mean()
                      .reindex(all_gate_cols)
                      .sort_values()
                      .index.tolist())

    pop_pivot = (pop.pivot(index="stop", columns="gate", values="count")
                    .fillna(0).astype(int)
                    .reindex(columns=all_gate_cols, fill_value=0))
    pop_pivot.columns = [short_map.get(c, c) for c in pop_pivot.columns]
    col_order_short = [short_map.get(g, g) for g in col_mean_order]
    pop_pivot = pop_pivot.reindex(columns=col_order_short, fill_value=0)

    return consensus, pop_pivot, n


@st.cache_data
def build_segments(_raw, _visit_df, _gates, finisher_names, radius=RADIUS_M):
    """Gate-to-gate elapsed time and avg moving speed for each finisher."""
    seg_rows = []
    for rname in finisher_names:
        rider_raw = next(
            r for r in _raw["participants"]
            if f"{r['first_name']} {r['last_name']}" == rname
        )
        pts     = rider_raw["points"]
        ts_all  = pd.to_datetime([p["ts"] for p in pts])
        spd_all = np.array([p["speed"] for p in pts])

        visits = (
            _visit_df[_visit_df["name"] == rname]
            .sort_values("visit_order")
            .reset_index(drop=True)
        )
        for i in range(len(visits) - 1):
            t_from  = visits.loc[i,   "visited_at"]
            t_to    = visits.loc[i+1, "visited_at"]
            g_from  = visits.loc[i,   "gate"]
            g_to    = visits.loc[i+1, "gate"]
            elapsed = (t_to - t_from).total_seconds() / 3600
            in_seg  = (ts_all >= t_from) & (ts_all <= t_to)
            moving  = spd_all[in_seg]
            moving  = moving[moving > 2]
            avg_spd = round(float(moving.mean()), 1) if len(moving) > 0 else None
            seg_rows.append({
                "rider":         rname,
                "from_gate":     g_from,
                "to_gate":       g_to,
                "elapsed_hrs":   round(elapsed, 2),
                "avg_speed_kmh": avg_spd,
            })

    df = pd.DataFrame(seg_rows)
    df["leg"] = df["from_gate"].map(lambda g: GATE_SHORT.get(g, g)) + \
                " → " + \
                df["to_gate"].map(lambda g: GATE_SHORT.get(g, g))

    # Keep only legs shared by ≥20 finishers
    counts = df.groupby(["from_gate", "to_gate"]).size().reset_index(name="n")
    common = counts[counts["n"] >= 20]
    common_keys = set(zip(common["from_gate"], common["to_gate"]))
    df = df[df.apply(lambda r: (r["from_gate"], r["to_gate"]) in common_keys, axis=1)].copy()

    # Per-leg summary
    stats = (df.groupby("leg").agg(
        n_riders     =("rider",         "count"),
        median_speed =("avg_speed_kmh", "median"),
        min_speed    =("avg_speed_kmh", "min"),
        max_speed    =("avg_speed_kmh", "max"),
        median_hrs   =("elapsed_hrs",   "median"),
    ).reset_index())

    fastest = (df.dropna(subset=["avg_speed_kmh"])
               .sort_values("avg_speed_kmh", ascending=False)
               .groupby("leg", as_index=False).first()
               [["leg","rider","avg_speed_kmh","elapsed_hrs"]]
               .rename(columns={"rider":"fast_rider","avg_speed_kmh":"fast_kmh","elapsed_hrs":"fast_hrs"}))
    slowest = (df.dropna(subset=["avg_speed_kmh"])
               .sort_values("avg_speed_kmh")
               .groupby("leg", as_index=False).first()
               [["leg","rider","avg_speed_kmh","elapsed_hrs"]]
               .rename(columns={"rider":"slow_rider","avg_speed_kmh":"slow_kmh","elapsed_hrs":"slow_hrs"}))

    summary = stats.merge(fastest, on="leg").merge(slowest, on="leg")

    # Order legs by median visit position of the from_gate
    gate_pos = (_visit_df[_visit_df["name"].isin(finisher_names)]
                .groupby("gate")["visit_order"].median())
    summary["_sort"] = summary["leg"].apply(
        lambda l: gate_pos.get(l.split(" → ")[0], 99)
    )
    summary = summary.sort_values("_sort").drop(columns="_sort").reset_index(drop=True)

    return df, summary


@st.cache_data
def get_rider_track(_raw, rider_name):
    for r in _raw["participants"]:
        if f"{r['first_name']} {r['last_name']}" == rider_name:
            if not r["points"]:
                return pd.DataFrame()
            df = pd.DataFrame(r["points"])
            df["ts"] = pd.to_datetime(df["ts"])
            return df.sort_values("ts").reset_index(drop=True)
    return pd.DataFrame()


# ── Load data ─────────────────────────────────────────────────────────────────

raw                = load_raw()
gates              = load_gates()
race_df, gate_cols = build_race_df(raw, gates)
visit_order_df     = build_gate_visit_order(raw, gates)

# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    hero = Path("assets/gate-photos/via-race.png")
    if hero.exists():
        st.image(str(hero), use_container_width=True)
    elif Path("icon-192.png").exists():
        st.image("icon-192.png", width=72)
    st.title("VIA Race III")
    st.caption("Ultima Thule · NL → NO · ~4,000 km")
    st.divider()

    status_filter = st.multiselect(
        "Status filter",
        options=["FINISHED", "DNF", "DNS"],
        default=["FINISHED", "DNF"],
    )

    all_riders = sorted(race_df["name"].tolist())
    default_idx = all_riders.index("Jason Vail") if "Jason Vail" in all_riders else 0
    selected_rider = st.selectbox("Rider (detail / map)", all_riders, index=default_idx)

    st.divider()
    col_a, col_b = st.columns(2)
    col_a.metric("Riders", len(race_df))
    col_b.metric("Finishers", (race_df["status"] == "FINISHED").sum())
    col_a.metric("DNF", (race_df["status"] == "DNF").sum())
    col_b.metric("DNS", (race_df["status"] == "DNS").sum())

filtered_df = race_df[race_df["status"].isin(status_filter)]

# ── Tabs ──────────────────────────────────────────────────────────────────────

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "🏆 Leaderboard",
    "🚴 Rider Profile",
    "✅ Gate Compliance",
    "🗺️ Route Map",
    "📋 Gate Order",
    "⚡ Segments",
])

# ── TAB 1: Leaderboard ────────────────────────────────────────────────────────

with tab1:
    st.subheader("Finisher Leaderboard — Elapsed Race Time")

    finishers = race_df[race_df["status"] == "FINISHED"].copy()
    finishers["elapsed_hrs"] = finishers["total_days"] * 24
    finishers["rest_hrs"]    = finishers["elapsed_hrs"] - finishers["ride_time_hrs"]
    finishers = finishers.sort_values("elapsed_hrs", ascending=True).reset_index(drop=True)
    finishers["rank"]  = range(1, len(finishers) + 1)
    finishers["label"] = finishers.apply(lambda r: f"#{int(r['rank'])}  {r['name']}", axis=1)

    fig_lb = go.Figure()
    fig_lb.add_trace(go.Bar(
        y=finishers["label"],
        x=finishers["ride_time_hrs"],
        orientation="h",
        name="Riding",
        marker_color="#3498db",
        customdata=finishers[[
            "name", "total_days", "ride_time_hrs",
            "total_dist_km", "elev_gain_m", "avg_speed_kmh",
        ]].values,
        hovertemplate=(
            "<b>%{customdata[0]}</b><br>"
            "Elapsed: %{customdata[1]:.1f} days<br>"
            "Riding: %{customdata[2]:.1f} hrs<br>"
            "Distance: %{customdata[3]:,.0f} km<br>"
            "Elevation gain: %{customdata[4]:,.0f} m<br>"
            "Avg speed: %{customdata[5]:.1f} km/h"
            "<extra></extra>"
        ),
    ))
    fig_lb.add_trace(go.Bar(
        y=finishers["label"],
        x=finishers["rest_hrs"],
        orientation="h",
        name="Rest / Sleep",
        marker_color="#5d6d7e",
        hovertemplate="Rest: %{x:.1f} hrs<extra></extra>",
    ))

    for _, row in finishers.iterrows():
        fig_lb.add_annotation(
            y=row["label"], x=row["elapsed_hrs"] + 1.5,
            text=f"{row['total_days']:.1f}d",
            showarrow=False, xanchor="left",
            font=dict(size=10, color="#cccccc"),
        )

    max_hrs = finishers["elapsed_hrs"].max()
    fig_lb.update_layout(
        barmode="stack",
        xaxis=dict(
            tickvals=list(range(0, int(max_hrs) + 50, 48)),
            ticktext=[f"{v // 24}d" for v in range(0, int(max_hrs) + 50, 48)],
            title="Elapsed Time",
        ),
        yaxis=dict(
            categoryorder="array",
            categoryarray=finishers["label"].tolist()[::-1],
        ),
        legend=dict(orientation="h", x=0.4, xanchor="center", y=-0.06),
        height=750,
        template="plotly_dark",
        margin=dict(l=220, r=80, t=20, b=40),
    )
    st.plotly_chart(fig_lb, use_container_width=True)

# ── TAB 2: Rider Profile ──────────────────────────────────────────────────────

with tab2:
    rider_row = race_df[race_df["name"] == selected_rider].iloc[0]
    track     = get_rider_track(raw, selected_rider)

    st.subheader(f"{selected_rider}  ·  Bib {rider_row['bib']}")

    # KPI cards
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    status_label = rider_row["status"]
    c1.metric("Status", status_label)
    c2.metric("Gates Hit", f"{int(rider_row['gates_hit'])}/19")
    c3.metric("Distance", f"{rider_row['total_dist_km']:,.0f} km" if rider_row["total_dist_km"] else "—")
    c4.metric("Elevation", f"{rider_row['elev_gain_m']:,.0f} m" if rider_row["elev_gain_m"] else "—")
    c5.metric("Elapsed", f"{rider_row['total_days']:.1f} d" if rider_row["total_days"] else "—")
    c6.metric("Avg Speed", f"{rider_row['avg_speed_kmh']:.1f} km/h" if rider_row["avg_speed_kmh"] else "—")

    st.divider()

    if not track.empty:
        # Clip to race window
        t_start  = rider_row["race_start"]
        t_finish = rider_row["race_finish"]
        if pd.notna(t_start) and pd.notna(t_finish):
            track_race = track[(track["ts"] >= t_start) & (track["ts"] <= t_finish)].copy()
        else:
            track_race = track.copy()

        # Downsample for chart performance
        if len(track_race) > 600:
            idx = np.round(np.linspace(0, len(track_race) - 1, 600)).astype(int)
            track_plot = track_race.iloc[idx].copy()
        else:
            track_plot = track_race.copy()

        track_plot["speed_smooth"] = track_plot["speed"].rolling(8, min_periods=1).mean()
        track_plot["alt_clean"]    = track_plot["alt"].clip(-100, 2500)
        track_plot["alt_smooth"]   = track_plot["alt_clean"].rolling(8, min_periods=1).mean()

        col_spd, col_alt = st.columns(2)

        with col_spd:
            fig_spd = px.line(
                track_plot, x="ts", y="speed_smooth",
                title="Speed (km/h)",
                labels={"ts": "", "speed_smooth": "km/h"},
                template="plotly_dark",
            )
            fig_spd.update_traces(line_color="#3498db", line_width=1.5)
            fig_spd.update_layout(margin=dict(t=40, b=20))
            st.plotly_chart(fig_spd, use_container_width=True)

        with col_alt:
            fig_alt = px.area(
                track_plot, x="ts", y="alt_smooth",
                title="Elevation (m)",
                labels={"ts": "", "alt_smooth": "m"},
                template="plotly_dark",
            )
            fig_alt.update_traces(line_color="#2ecc71", fillcolor="rgba(46,204,113,0.15)")
            fig_alt.update_layout(margin=dict(t=40, b=20))
            st.plotly_chart(fig_alt, use_container_width=True)

        # Gate table
        st.subheader("Gate Compliance")
        gate_rows = []
        for g in gate_cols:
            dist = rider_row.get(g)
            hit  = dist is not None and dist <= RADIUS_M
            gate_rows.append({
                "Gate":             g,
                "Closest Approach": f"{dist:,.0f} m" if dist is not None else "—",
                "Result":           "✅  Hit" if hit else "❌  Missed",
            })
        st.dataframe(
            pd.DataFrame(gate_rows),
            hide_index=True,
            use_container_width=True,
            column_config={"Result": st.column_config.TextColumn(width="small")},
        )

    else:
        st.info("No GPS tracking data available for this rider.")

# ── TAB 3: Gate Compliance ────────────────────────────────────────────────────

with tab3:
    st.subheader("Gate Compliance Matrix — All Race Riders")
    st.caption(f"Detection radius: {RADIUS_M:,} m  ·  Green = hit, Red = missed, Grey = no data")

    # Sort by gates_hit desc, then name
    matrix_df = filtered_df.sort_values(
        ["gates_hit", "status"], ascending=[False, True]
    ).reset_index(drop=True)

    # Build numeric matrix: 1=hit, 0=miss, NaN=no data
    hit_matrix = pd.DataFrame(index=matrix_df["name"])
    for g in gate_cols:
        hit_matrix[g] = matrix_df[g].apply(
            lambda d: 1.0 if (d is not None and d <= RADIUS_M)
            else (np.nan if d is None else 0.0)
        ).values

    # Row labels with status
    hit_matrix.index = (
        matrix_df["name"] + "  [" + matrix_df["status"] + "]  "
        + matrix_df["gates_hit"].astype(str) + "/19"
    )

    fig_heat = px.imshow(
        hit_matrix,
        color_continuous_scale=[
            [0.0, "#c0392b"],
            [0.5, "#c0392b"],
            [0.5, "#27ae60"],
            [1.0, "#27ae60"],
        ],
        range_color=[0, 1],
        aspect="auto",
        template="plotly_dark",
    )
    fig_heat.update_coloraxes(showscale=False)
    fig_heat.update_layout(
        height=max(500, len(hit_matrix) * 20 + 120),
        xaxis=dict(tickangle=-40, tickfont=dict(size=10)),
        yaxis=dict(tickfont=dict(size=9)),
        margin=dict(l=220, t=20, b=120),
    )
    fig_heat.update_traces(
        hovertemplate="Rider: %{y}<br>Gate: %{x}<br>Result: %{z}<extra></extra>"
    )
    st.plotly_chart(fig_heat, use_container_width=True)

# ── TAB 4: Route Map ──────────────────────────────────────────────────────────

with tab4:
    st.subheader("GPS Route Map")

    map_col1, map_col2 = st.columns([3, 1])
    with map_col2:
        map_options = sorted(filtered_df["name"].tolist())

        # Purge stale session state values whenever the options list changes
        # (e.g. user changes the status filter, removing a previously-selected rider)
        _MAP_KEY = "map_riders_select"
        if _MAP_KEY in st.session_state:
            clean = [r for r in st.session_state[_MAP_KEY] if r in map_options]
            if clean != st.session_state[_MAP_KEY]:
                st.session_state[_MAP_KEY] = clean

        map_riders = st.multiselect(
            "Riders to display (max 10)",
            options=map_options,
            default=[selected_rider] if selected_rider in map_options else map_options[:1],
            key=_MAP_KEY,
            max_selections=10,
        )
        show_gates = st.toggle("Show mandatory gates", value=True)
        max_pts    = st.slider("Track resolution (points per rider)", 100, 500, 250, step=50)

    with map_col1:
        fig_map = go.Figure()

        for rname in map_riders:
            track = get_rider_track(raw, rname)
            if track.empty:
                continue
            r_status = race_df[race_df["name"] == rname]["status"].values[0]
            color    = STATUS_COLORS.get(r_status, "#aaaaaa")

            if len(track) > max_pts:
                idx   = np.round(np.linspace(0, len(track) - 1, max_pts)).astype(int)
                track = track.iloc[idx]

            fig_map.add_trace(go.Scattermap(
                lat=track["lat"], lon=track["lon"],
                mode="lines",
                line=dict(color=color, width=2),
                name=f"{rname} ({r_status})",
                hoverinfo="name",
            ))

        if show_gates:
            fig_map.add_trace(go.Scattermap(
                lat=gates["lat"], lon=gates["lon"],
                mode="markers+text",
                marker=dict(size=10, color="#f39c12"),
                text=gates["gate"],
                textposition="top right",
                name="Mandatory Gates",
                hovertext=gates["gate"],
                hoverinfo="text",
            ))

        fig_map.update_layout(
            map_style="open-street-map",
            map=dict(center=dict(lat=58, lon=9), zoom=4),
            height=580,
            template="plotly_dark",
            margin=dict(l=0, r=0, t=0, b=0),
            legend=dict(
                bgcolor="rgba(20,20,20,0.7)",
                bordercolor="#444",
                borderwidth=1,
                font=dict(size=10),
            ),
        )
        st.plotly_chart(fig_map, use_container_width=True)

# ── TAB 5: Gate Order ─────────────────────────────────────────────────────────

with tab5:
    st.subheader("Gate Visit Order")
    st.caption(
        "🔵 Ordered — must be visited in sequence (Start → Brocken → Fredriksten → Suleskard)  "
        "·  🟡 Refuge — required, any time (Botn Fjellstue)  "
        "·  ⚪ Free — any order"
    )

    # ── Per-rider sequence ────────────────────────────────────────────────────
    st.markdown(f"#### {selected_rider} — Gate Sequence")

    rider_visits = visit_order_df[visit_order_df["name"] == selected_rider].copy()

    if rider_visits.empty:
        st.info("No gate visit data available for this rider.")
    else:
        rider_visits = rider_visits.sort_values("visit_order").reset_index(drop=True)

        # Leg time = time since previous gate
        rider_visits["leg_time"] = rider_visits["visited_at"].diff()
        rider_visits["leg_hrs"]  = rider_visits["leg_time"].dt.total_seconds() / 3600

        table_rows = []
        for _, r in rider_visits.iterrows():
            leg_str = (
                f"{int(r['leg_hrs'] // 24)}d {int(r['leg_hrs'] % 24)}h"
                if pd.notna(r["leg_hrs"]) and r["leg_hrs"] >= 24
                else f"{r['leg_hrs']:.1f} hrs"
                if pd.notna(r["leg_hrs"])
                else "—"
            )
            table_rows.append({
                "Stop #":      int(r["visit_order"]),
                "Gate":        r["gate"],
                "Type":        gate_type_label(r["gate"]),
                "Visited At":  r["visited_at"].strftime("%d %b  %H:%M"),
                "Leg Time":    leg_str,
            })

        st.dataframe(
            pd.DataFrame(table_rows),
            hide_index=True,
            use_container_width=True,
            column_config={
                "Stop #":     st.column_config.NumberColumn(width="small"),
                "Type":       st.column_config.TextColumn(width="small"),
                "Leg Time":   st.column_config.TextColumn(width="small"),
                "Visited At": st.column_config.TextColumn(width="medium"),
            },
        )

    st.divider()

    # ── Gate order popularity ─────────────────────────────────────────────────
    gate_short = {
        "De Proloog, Amerongen": "Start",
        "Brocken":               "Brocken",
        "Fredriksten fortress":  "Fredriksten",
        "Botn Fjellstue":        "Botn 🟡",
        "Suleskard":             "Suleskard",
        "Lysebotn":              "Lysebotn",
        "Vøringfossen":          "Vøringfossen",
        "Sognefjellet":          "Sognefjellet",
        "Gaularfjellet":         "Gaularfjellet",
        "Strynefjellsveg":       "Strynefjell",
        "Borgund Stavkyrkje":    "Borgund",
        "Urnes stavkyrkje":      "Urnes",
        "Lom Stavkyrkje":        "Lom",
        "Svøufallet":            "Svøufallet",
        "Atlantic road":         "Atlantic Rd",
        "Trollstigen":           "Trollstigen",
        "Dalsnibba":             "Dalsnibba",
        "Vestkapp":              "Vestkapp",
        "Volda":                 "Volda",
    }

    finisher_names_ordered = (
        race_df[race_df["status"] == "FINISHED"]
        .sort_values("total_days")["name"]
        .tolist()
    )

    consensus, pop_pivot, n_fin = build_gate_popularity(
        visit_order_df, finisher_names_ordered, gate_cols, gate_short
    )

    col_left, col_right = st.columns([1, 2])

    # Consensus table
    with col_left:
        st.markdown("#### Consensus Route")
        st.caption("Most common gate visited at each stop across all finishers.")

        def gate_type_tag(gate):
            if gate in ORDERED_GATES:
                return "🔵"
            if gate == REFUGE_GATE:
                return "🟡"
            return "⚪"

        con_rows = []
        for _, r in consensus.iterrows():
            con_rows.append({
                "Stop": int(r["stop"]),
                " ":    gate_type_tag(r["gate"]),
                "Gate": gate_short.get(r["gate"], r["gate"]),
                "Riders": f"{int(r['count'])}/{n_fin}",
                "%": f"{r['pct']}%",
            })
        st.dataframe(
            pd.DataFrame(con_rows),
            hide_index=True,
            use_container_width=True,
            column_config={
                "Stop":   st.column_config.NumberColumn(width="small"),
                " ":      st.column_config.TextColumn(width="small"),
                "Riders": st.column_config.TextColumn(width="small"),
                "%":      st.column_config.TextColumn(width="small"),
            },
        )

    # Popularity heatmap
    with col_right:
        st.markdown("#### Stop × Gate Popularity")
        st.caption(
            "How many of the 32 finishers visited each gate at each stop. "
            "Darker = more riders. Bright diagonal = high consensus."
        )
        fig_pop = px.imshow(
            pop_pivot,
            text_auto=True,
            color_continuous_scale="Blues",
            range_color=[0, n_fin],
            aspect="auto",
            labels=dict(x="Gate", y="Stop #", color="Riders"),
            template="plotly_dark",
        )
        fig_pop.update_coloraxes(showscale=False)
        fig_pop.update_traces(
            textfont=dict(size=8),
            hovertemplate="Stop %{y} · %{x}<br>%{z} riders<extra></extra>",
        )
        fig_pop.update_layout(
            height=560,
            xaxis=dict(tickangle=-40, tickfont=dict(size=9), side="top"),
            yaxis=dict(tickfont=dict(size=9), autorange="reversed"),
            margin=dict(l=40, r=20, t=120, b=20),
        )
        st.plotly_chart(fig_pop, use_container_width=True)

    st.divider()

    # ── All-finisher visit order comparison ───────────────────────────────────
    st.markdown("#### All Finishers — Individual Gate Visit Order")
    st.caption("Numbers show each rider's visit sequence (1 = first gate reached). Colour = position — earlier is darker.")

    pivot = (
        visit_order_df[visit_order_df["name"].isin(finisher_names_ordered)]
        .pivot(index="name", columns="gate", values="visit_order")
        .reindex(index=finisher_names_ordered, columns=gate_cols)
    )
    pivot.columns = [gate_short.get(c, c) for c in pivot.columns]
    pivot.index   = [f"#{i+1}  {n}" for i, n in enumerate(finisher_names_ordered)]

    fig_ord = px.imshow(
        pivot,
        text_auto=True,
        color_continuous_scale="Blues",
        range_color=[1, 19],
        aspect="auto",
        template="plotly_dark",
    )
    fig_ord.update_coloraxes(showscale=False)
    fig_ord.update_traces(
        textfont=dict(size=9),
        hovertemplate="Rider: %{y}<br>Gate: %{x}<br>Visit order: %{z}<extra></extra>",
    )
    fig_ord.update_layout(
        height=max(500, len(finisher_names_ordered) * 22 + 140),
        xaxis=dict(tickangle=-40, tickfont=dict(size=10), side="top"),
        yaxis=dict(tickfont=dict(size=9)),
        margin=dict(l=200, t=120, b=20),
    )
    st.plotly_chart(fig_ord, use_container_width=True)

# ── TAB 6: Segments ───────────────────────────────────────────────────────────

with tab6:
    st.subheader("Gate-to-Gate Segment Analysis")
    st.caption("Avg moving speed (km/h) per leg · legs shared by ≥20 of 32 finishers · hover for rider details")

    finisher_names_seg = (
        race_df[race_df["status"] == "FINISHED"]
        .sort_values("total_days")["name"]
        .tolist()
    )
    df_segs, leg_summary = build_segments(raw, visit_order_df, gates, finisher_names_seg)

    leg_order = leg_summary["leg"].tolist()

    # ── Interactive strip chart ───────────────────────────────────────────────
    fast_map = dict(zip(leg_summary["leg"], leg_summary["fast_rider"]))
    slow_map = dict(zip(leg_summary["leg"], leg_summary["slow_rider"]))
    med_map  = dict(zip(leg_summary["leg"], leg_summary["median_speed"]))

    fig_seg = go.Figure()

    for _, row in df_segs.dropna(subset=["avg_speed_kmh"]).iterrows():
        is_fast = row["rider"] == fast_map.get(row["leg"])
        is_slow = row["rider"] == slow_map.get(row["leg"])
        color   = "#e74c3c" if is_fast else ("#3498db" if is_slow else "rgba(160,160,160,0.5)")
        size    = 12 if (is_fast or is_slow) else 7
        symbol  = "star" if is_fast else ("square" if is_slow else "circle")

        fig_seg.add_trace(go.Scatter(
            x=[row["avg_speed_kmh"]],
            y=[row["leg"]],
            mode="markers",
            marker=dict(color=color, size=size, symbol=symbol,
                        line=dict(width=1, color="rgba(255,255,255,0.2)")),
            showlegend=False,
            hovertemplate=(
                f"<b>{row['rider']}</b><br>"
                f"Leg: {row['leg']}<br>"
                f"Avg speed: {row['avg_speed_kmh']} km/h<br>"
                f"Elapsed: {row['elapsed_hrs']:.1f} h"
                "<extra></extra>"
            ),
        ))

    # Median ticks
    for leg, med in med_map.items():
        fig_seg.add_trace(go.Scatter(
            x=[med], y=[leg], mode="markers",
            marker=dict(color="#f39c12", size=14, symbol="line-ns",
                        line=dict(width=3, color="#f39c12")),
            showlegend=False,
            hovertemplate=f"Median: {med:.1f} km/h<extra></extra>",
        ))

    # Legend traces
    fig_seg.add_trace(go.Scatter(x=[None], y=[None], mode="markers",
        marker=dict(color="#e74c3c", size=10, symbol="star"), name="Fastest on leg"))
    fig_seg.add_trace(go.Scatter(x=[None], y=[None], mode="markers",
        marker=dict(color="#3498db", size=10, symbol="square"), name="Slowest on leg"))
    fig_seg.add_trace(go.Scatter(x=[None], y=[None], mode="markers",
        marker=dict(color="#f39c12", size=12, symbol="line-ns",
                    line=dict(width=3, color="#f39c12")), name="Median"))

    fig_seg.update_layout(
        xaxis_title="Avg Moving Speed (km/h)",
        yaxis=dict(
            categoryorder="array",
            categoryarray=leg_order[::-1],
            tickfont=dict(size=11),
        ),
        legend=dict(orientation="h", y=-0.12, x=0.5, xanchor="center"),
        height=520,
        template="plotly_dark",
        margin=dict(l=180, r=40, t=20, b=60),
    )
    st.plotly_chart(fig_seg, use_container_width=True)

    # ── Summary table ─────────────────────────────────────────────────────────
    st.subheader("Leg Summary")
    tbl = leg_summary[[
        "leg", "n_riders", "median_speed", "min_speed", "max_speed",
        "fast_rider", "fast_kmh", "slow_rider", "slow_kmh",
    ]].copy()
    tbl.columns = [
        "Leg", "Riders", "Median (km/h)", "Min (km/h)", "Max (km/h)",
        "Fastest Rider", "Fast (km/h)", "Slowest Rider", "Slow (km/h)",
    ]
    tbl["Median (km/h)"] = tbl["Median (km/h)"].round(1)
    st.dataframe(tbl, hide_index=True, use_container_width=True)
