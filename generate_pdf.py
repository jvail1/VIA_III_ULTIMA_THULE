"""
Generate via_race_26_executive_summary.pdf
Run: python3 generate_pdf.py
Requires: reportlab (pip install reportlab)
"""
import json
import zipfile
import pathlib
import xml.etree.ElementTree as ET

import numpy as np
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable,
)

# ── Palette ───────────────────────────────────────────────────────────────────

INK      = colors.HexColor("#111111")
HDR_BG   = colors.HexColor("#0d1b2a")
HDR_FG   = colors.white
S1       = colors.white
S2       = colors.HexColor("#eef2f7")
ACCENT   = colors.HexColor("#c0392b")
GRN_BG   = colors.HexColor("#e9f7ef")
GRN_INK  = colors.HexColor("#1a5c2a")
YLW_BG   = colors.HexColor("#fef9e7")
RED_INK  = colors.HexColor("#922b21")
BLUE_INK = colors.HexColor("#1a3a6b")

# ── Styles ────────────────────────────────────────────────────────────────────

styles      = getSampleStyleSheet()
body_sty    = ParagraphStyle("body", parent=styles["Normal"], fontSize=8.5,
                              leading=12, textColor=INK)
head_sty    = ParagraphStyle("head", parent=styles["Heading1"], fontSize=14,
                              textColor=HDR_FG, spaceAfter=4)
sub_sty     = ParagraphStyle("sub", parent=styles["Heading2"], fontSize=10,
                              textColor=BLUE_INK, spaceBefore=8, spaceAfter=4)
note_sty    = ParagraphStyle("note", parent=styles["Normal"], fontSize=7.5,
                              leading=11, textColor=colors.HexColor("#444444"),
                              leftIndent=6)
callout_sty = ParagraphStyle("callout", parent=styles["Normal"], fontSize=8.5,
                              leading=12, textColor=INK, leftIndent=8, rightIndent=8)


def make_style(extra=None):
    base = [
        ("BACKGROUND",    (0, 0), (-1, 0),  HDR_BG),
        ("TEXTCOLOR",     (0, 0), (-1, 0),  HDR_FG),
        ("FONTNAME",      (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, 0),  7.5),
        ("FONTNAME",      (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE",      (0, 1), (-1, -1), 7.5),
        ("TEXTCOLOR",     (0, 1), (-1, -1), INK),
        ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
        ("ALIGN",         (1, 1), (1, -1),  "LEFT"),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUND", (0, 1), (-1, -1), [S1, S2]),
        ("GRID",          (0, 0), (-1, -1), 0.3, colors.HexColor("#cccccc")),
        ("TOPPADDING",    (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING",   (0, 0), (-1, -1), 4),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 4),
    ]
    if extra:
        base.extend(extra)
    return TableStyle(base)


def fmt_time(total_days):
    """Format decimal days as 'Xd YYh'."""
    if pd.isna(total_days):
        return "—"
    d = int(total_days)
    h = round((total_days - d) * 24)
    return f"{d}d {h:02d}h"


# ── Constants ─────────────────────────────────────────────────────────────────

RADIUS_M = 1000
R_EARTH  = 6_371_000

GATE_SHORT = {
    "De Proloog, Amerongen": "Start",      "Brocken": "Brocken",
    "Fredriksten fortress":  "Fredriksten", "Botn Fjellstue": "Botn",
    "Suleskard":             "Suleskard",   "Lysebotn": "Lysebotn",
    "Vøringfossen":          "Vøringfossen","Sognefjellet": "Sognefjellet",
    "Gaularfjellet":         "Gaularfjellet","Strynefjellsveg": "Strynefjell",
    "Borgund Stavkyrkje":    "Borgund",     "Urnes stavkyrkje": "Urnes",
    "Lom Stavkyrkje":        "Lom",         "Svøufallet": "Svøufallet",
    "Atlantic road":         "Atlantic Rd", "Trollstigen": "Trollstigen",
    "Dalsnibba":             "Dalsnibba",   "Vestkapp": "Vestkapp",
    "Volda":                 "Volda",
}

# Override riders: missed Volda gate but confirmed official finishers.
# race_finish is used as t_finish when GPS doesn't detect the gate.
OFFICIAL_OVERRIDES = {
    "Bruno Wicht":   {},
    "Adam Bialek":   {
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

def haversine_arr(lats, lons, glat, glon):
    dlat = np.radians(glat - lats)
    dlon = np.radians(glon - lons)
    a    = (np.sin(dlat / 2) ** 2
            + np.cos(np.radians(lats)) * np.cos(np.radians(glat)) * np.sin(dlon / 2) ** 2)
    return R_EARTH * 2 * np.arcsin(np.sqrt(a).clip(0, 1))


def first_gate_hit(lats, lons, ts, glat, glon):
    dists = haversine_arr(lats, lons, glat, glon)
    hits  = np.where(dists <= RADIUS_M)[0]
    return ts[hits[0]] if len(hits) else None


def first_gate_hit_odo(lats, lons, ts, odos, glat, glon):
    """Return (timestamp, odo) of first hit, or (None, None)."""
    dists = haversine_arr(lats, lons, glat, glon)
    hits  = np.where(dists <= RADIUS_M)[0]
    if len(hits):
        return ts[hits[0]], float(odos[hits[0]])
    return None, None


def compute_elev_gain(pts):
    alts = np.array([p["alt"] for p in pts], dtype=float)
    alts[(alts < -100) | (alts > 2500)] = np.nan
    alts = pd.Series(alts).ffill().bfill().values
    return float(np.diff(alts)[np.diff(alts) > 5].sum())


def detect_sleep(pts, t_start, t_finish, speed_thresh=3, min_dur_min=45):
    """Return (total_hrs, n_bouts, longest_bout_hrs)."""
    if t_start is None or t_finish is None or pd.isna(t_start) or pd.isna(t_finish) or len(pts) < 2:
        return 0.0, 0, 0.0
    ts_arr  = pd.to_datetime([p["ts"] for p in pts])
    spd_arr = np.array([p["speed"] for p in pts])
    in_race = (ts_arr >= t_start) & (ts_arr <= t_finish)
    ts_r    = ts_arr[in_race]
    spd_r   = spd_arr[in_race]
    if len(ts_r) < 2:
        return 0.0, 0, 0.0
    stopped = spd_r < speed_thresh
    total_hrs, n_bouts, longest_hrs, in_bout = 0.0, 0, 0.0, False
    for i, s in enumerate(stopped):
        if s and not in_bout:
            bout_start = i; in_bout = True
        elif not s and in_bout:
            dur = (ts_r[i - 1] - ts_r[bout_start]).total_seconds() / 60
            if dur >= min_dur_min:
                hrs = dur / 60
                total_hrs += hrs
                n_bouts   += 1
                longest_hrs = max(longest_hrs, hrs)
            in_bout = False
    if in_bout:
        dur = (ts_r[-1] - ts_r[bout_start]).total_seconds() / 60
        if dur >= min_dur_min:
            hrs = dur / 60
            total_hrs += hrs
            n_bouts   += 1
            longest_hrs = max(longest_hrs, hrs)
    return round(total_hrs, 1), n_bouts, round(longest_hrs, 1)


# ── Data loaders ──────────────────────────────────────────────────────────────

def load_data():
    if not pathlib.Path("via_race_26_export.json").exists():
        with zipfile.ZipFile("via_race_26_export.zip") as zf:
            zf.extractall(".")
    with open("via_race_26_export.json") as f:
        return json.load(f)


def load_gates():
    tree = ET.parse("VIA Chapter III - RACE Route & Locations.kml")
    root = tree.getroot()
    ns   = {"kml": "http://www.opengis.net/kml/2.2"}
    gates = []
    for folder in root.findall(".//kml:Folder", ns):
        if "Mandatory" in (folder.findtext("kml:name", namespaces=ns) or ""):
            for pm in folder.findall("kml:Placemark", ns):
                nm     = pm.findtext("kml:name", namespaces=ns)
                coords = pm.findtext(".//kml:coordinates", namespaces=ns)
                if coords:
                    lon, lat, *_ = map(float, coords.strip().split(","))
                    gates.append({"gate": nm, "lat": lat, "lon": lon})
    return pd.DataFrame(gates)


def build_race_df(raw, gates_df):
    start_g     = gates_df[gates_df["gate"] == "De Proloog, Amerongen"].iloc[0]
    finish_g    = gates_df[gates_df["gate"] == "Volda"].iloc[0]
    other_gates = gates_df[gates_df["gate"] != "Volda"]

    rows = []
    for rider in raw["participants"]:
        if rider["variant"] != "Race":
            continue
        pts  = rider["points"]
        name = f"{rider['first_name']} {rider['last_name']}"
        cat  = rider.get("category", "M")

        if len(pts) < 2:
            rows.append({"name": name, "category": cat, "status": "DNS",
                         "gates_hit": 0, "total_dist_km": None, "total_days": None,
                         "ride_time_hrs": None, "avg_speed_kmh": None,
                         "elev_gain_m": None, "sleep_hrs": 0.0, "n_sleeps": 0,
                         "longest_stop_hrs": 0.0, "t_start": None, "t_finish": None})
            continue

        lats   = np.array([p["lat"] for p in pts])
        lons   = np.array([p["lon"] for p in pts])
        ts     = pd.to_datetime([p["ts"] for p in pts])
        speeds = np.array([p["speed"] for p in pts])
        odos   = np.array([p["odo"] for p in pts])

        gate_dists = {
            g["gate"]: haversine_arr(lats, lons, g["lat"], g["lon"]).min()
            for _, g in gates_df.iterrows()
        }
        gates_hit = sum(1 for d in gate_dists.values() if d <= RADIUS_M)

        t_start = first_gate_hit(lats, lons, ts, start_g["lat"], start_g["lon"])

        last_other = None
        for _, og in other_gates.iterrows():
            t_og = first_gate_hit(lats, lons, ts, og["lat"], og["lon"])
            if t_og and (last_other is None or t_og > last_other):
                last_other = t_og
        t_finish = None
        if last_other:
            mask     = ts >= last_other
            t_finish = first_gate_hit(lats[mask], lons[mask], ts[mask],
                                      finish_g["lat"], finish_g["lon"])

        # For official override riders who missed the Volda gate: use override finish time
        ovr_finish = OFFICIAL_OVERRIDES.get(name, {}).get("race_finish")
        if t_finish is None and ovr_finish is not None:
            t_finish = ovr_finish

        if t_start and t_finish:
            in_race    = (ts >= t_start) & (ts <= t_finish)
            odos_r     = odos[in_race]
            spd_r      = speeds[in_race]
            ts_r       = ts[in_race]
            total_dist = round(float(odos_r[-1] - odos_r[0]), 1) if len(odos_r) >= 2 else None
            total_days = (t_finish - t_start).total_seconds() / 86400
            elev_gain  = round(compute_elev_gain([p for p, m in zip(pts, in_race) if m]))
            if len(ts_r) >= 2:
                dt_sec   = np.diff(ts_r).astype("timedelta64[s]").astype(float)
                ride_hrs = round(dt_sec[spd_r[:-1] > 2].sum() / 3600, 1)
            else:
                ride_hrs = None
            avg_speed = round(total_dist / ride_hrs, 1) if (total_dist and ride_hrs) else None
        else:
            total_dist = total_days = elev_gain = ride_hrs = avg_speed = None

        sleep_hrs, n_sleeps, longest_stop = detect_sleep(pts, t_start, t_finish)
        status = "FINISHED" if gates_hit == 19 and t_finish else "DNF"

        rows.append({
            "name": name, "category": cat, "status": status,
            "gates_hit": gates_hit,
            "total_dist_km":    total_dist,  "total_days":      total_days,
            "ride_time_hrs":    ride_hrs,    "avg_speed_kmh":   avg_speed,
            "elev_gain_m":      elev_gain,   "sleep_hrs":       sleep_hrs,
            "n_sleeps":         n_sleeps,    "longest_stop_hrs": longest_stop,
            "t_start":          t_start,     "t_finish":        t_finish,
        })

    df = pd.DataFrame(rows)

    for nm, ovr in OFFICIAL_OVERRIDES.items():
        mask = df["name"] == nm
        if mask.any():
            df.loc[mask, "status"]    = "FINISHED"
            df.loc[mask, "gates_hit"] = 19
            for col, val in ovr.items():
                if col in df.columns and val is not None:
                    df.loc[mask, col] = val

    return df


def build_segment_variation(raw, gates_df, finisher_names):
    """Distance spread between consecutive KML gates for finishers who rode A→B in order."""
    gate_list = gates_df["gate"].tolist()
    seg_rows  = []

    for rider in raw["participants"]:
        name = f"{rider['first_name']} {rider['last_name']}"
        if name not in finisher_names or len(rider["points"]) < 2:
            continue
        pts  = rider["points"]
        lats = np.array([p["lat"] for p in pts])
        lons = np.array([p["lon"] for p in pts])
        ts   = pd.to_datetime([p["ts"] for p in pts])
        odos = np.array([p["odo"] for p in pts])

        gate_hits = {}
        for _, gate in gates_df.iterrows():
            t_hit, odo_hit = first_gate_hit_odo(lats, lons, ts, odos,
                                                 gate["lat"], gate["lon"])
            if t_hit is not None:
                gate_hits[gate["gate"]] = (t_hit, odo_hit)

        for i in range(len(gate_list) - 1):
            g_from, g_to = gate_list[i], gate_list[i + 1]
            if g_from not in gate_hits or g_to not in gate_hits:
                continue
            t_from, odo_from = gate_hits[g_from]
            t_to,   odo_to   = gate_hits[g_to]
            if t_from >= t_to:
                continue  # didn't ride this pair in KML order
            seg_km = round(odo_to - odo_from, 1)
            if seg_km <= 0:
                continue
            seg_rows.append({
                "segment": (GATE_SHORT.get(g_from, g_from)
                            + " → " + GATE_SHORT.get(g_to, g_to)),
                "rider":   name,
                "seg_km":  seg_km,
            })

    if not seg_rows:
        return pd.DataFrame()

    df = pd.DataFrame(seg_rows)
    agg = (df.groupby("segment")["seg_km"]
             .agg(N="count", min_km="min", median_km="median", max_km="max")
             .reset_index())
    agg["spread"] = (agg["max_km"] - agg["min_km"]).round(0).astype(int)
    agg["min_km"]    = agg["min_km"].round(0).astype(int)
    agg["median_km"] = agg["median_km"].round(0).astype(int)
    agg["max_km"]    = agg["max_km"].round(0).astype(int)

    shortest = (df.sort_values("seg_km").groupby("segment", as_index=False).first()
                  [["segment", "rider"]].rename(columns={"rider": "shortest"}))
    longest  = (df.sort_values("seg_km", ascending=False).groupby("segment", as_index=False).first()
                  [["segment", "rider"]].rename(columns={"rider": "longest"}))
    # Use last name only for brevity
    shortest["shortest"] = shortest["shortest"].apply(lambda n: n.split()[-1])
    longest["longest"]   = longest["longest"].apply(lambda n: n.split()[-1])

    agg = agg.merge(shortest, on="segment").merge(longest, on="segment")

    # Sort by KML gate order
    seg_order = [
        GATE_SHORT.get(gate_list[i], gate_list[i])
        + " → " + GATE_SHORT.get(gate_list[i + 1], gate_list[i + 1])
        for i in range(len(gate_list) - 1)
    ]
    agg["_order"] = agg["segment"].apply(
        lambda s: seg_order.index(s) if s in seg_order else 99
    )
    return agg.sort_values("_order").drop(columns="_order").reset_index(drop=True)


def build_fastest_legs(raw, gates_df, finisher_names):
    """Fastest elapsed time gate-to-gate (KML order) among finishers."""
    gate_list = gates_df["gate"].tolist()
    seg_rows  = []

    for rider in raw["participants"]:
        name = f"{rider['first_name']} {rider['last_name']}"
        if name not in finisher_names or len(rider["points"]) < 2:
            continue
        pts  = rider["points"]
        lats = np.array([p["lat"] for p in pts])
        lons = np.array([p["lon"] for p in pts])
        ts   = pd.to_datetime([p["ts"] for p in pts])
        odos = np.array([p["odo"] for p in pts])

        gate_hits = {}
        for _, gate in gates_df.iterrows():
            t_hit, _ = first_gate_hit_odo(lats, lons, ts, odos, gate["lat"], gate["lon"])
            if t_hit is not None:
                gate_hits[gate["gate"]] = t_hit

        for i in range(len(gate_list) - 1):
            g_from, g_to = gate_list[i], gate_list[i + 1]
            if g_from not in gate_hits or g_to not in gate_hits:
                continue
            t_from, t_to = gate_hits[g_from], gate_hits[g_to]
            if t_from >= t_to:
                continue
            elapsed_hrs = (t_to - t_from).total_seconds() / 3600
            seg_rows.append({
                "segment":     (GATE_SHORT.get(g_from, g_from)
                                + " → " + GATE_SHORT.get(g_to, g_to)),
                "rider":       name,
                "elapsed_hrs": round(elapsed_hrs, 1),
            })

    if not seg_rows:
        return pd.DataFrame()

    df = pd.DataFrame(seg_rows)
    fastest = (df.sort_values("elapsed_hrs")
                 .groupby("segment", as_index=False).first()
                 [["segment", "rider", "elapsed_hrs"]])

    seg_order = [
        GATE_SHORT.get(gate_list[i], gate_list[i])
        + " → " + GATE_SHORT.get(gate_list[i + 1], gate_list[i + 1])
        for i in range(len(gate_list) - 1)
    ]
    fastest["_order"] = fastest["segment"].apply(
        lambda s: seg_order.index(s) if s in seg_order else 99
    )
    return fastest.sort_values("_order").drop(columns="_order").reset_index(drop=True)


def build_segments_speed(raw, gates_df, finisher_names):
    """Avg moving speed per common leg (≥20 finishers), for the spotlight section."""
    seg_rows = []
    for rider in raw["participants"]:
        name = f"{rider['first_name']} {rider['last_name']}"
        if name not in finisher_names or len(rider["points"]) < 2:
            continue
        pts    = rider["points"]
        lats   = np.array([p["lat"] for p in pts])
        lons   = np.array([p["lon"] for p in pts])
        ts     = pd.to_datetime([p["ts"] for p in pts])
        speeds = np.array([p["speed"] for p in pts])

        visits = []
        for _, gate in gates_df.iterrows():
            dists  = haversine_arr(lats, lons, gate["lat"], gate["lon"])
            within = np.where(dists <= RADIUS_M)[0]
            if len(within):
                visits.append({"gate": gate["gate"], "visited_at": ts[within[0]]})
        visits = sorted(visits, key=lambda x: x["visited_at"])

        for i in range(len(visits) - 1):
            t0, t1 = visits[i]["visited_at"], visits[i + 1]["visited_at"]
            g0, g1 = visits[i]["gate"],       visits[i + 1]["gate"]
            in_seg = (ts >= t0) & (ts <= t1)
            moving = speeds[in_seg]; moving = moving[moving > 2]
            avg_spd = round(float(moving.mean()), 1) if len(moving) else None
            seg_rows.append({
                "rider": name, "from_gate": g0, "to_gate": g1,
                "elapsed_hrs": round((t1 - t0).total_seconds() / 3600, 2),
                "avg_speed": avg_spd,
            })

    df = pd.DataFrame(seg_rows)
    df["leg"] = (df["from_gate"].map(lambda g: GATE_SHORT.get(g, g))
                 + " → " + df["to_gate"].map(lambda g: GATE_SHORT.get(g, g)))

    counts      = df.groupby(["from_gate", "to_gate"]).size().reset_index(name="n")
    common      = counts[counts["n"] >= 20]
    common_keys = set(zip(common["from_gate"], common["to_gate"]))
    df          = df[df.apply(lambda r: (r["from_gate"], r["to_gate"]) in common_keys, axis=1)].copy()

    stats   = df.groupby("leg").agg(n_riders=("rider","count"),
                                     median_speed=("avg_speed","median")).reset_index()
    fastest = (df.dropna(subset=["avg_speed"])
                 .sort_values("avg_speed", ascending=False)
                 .groupby("leg", as_index=False).first()
                 [["leg","rider","avg_speed","elapsed_hrs"]]
                 .rename(columns={"rider":"fast_rider","avg_speed":"fast_kmh",
                                  "elapsed_hrs":"fast_time_hrs"}))
    fast_time = (df.dropna(subset=["elapsed_hrs"])
                   .sort_values("elapsed_hrs")
                   .groupby("leg", as_index=False).first()
                   [["leg","rider","elapsed_hrs"]]
                   .rename(columns={"rider":"fast_time_rider","elapsed_hrs":"fastest_elapsed_hrs"}))

    summary = stats.merge(fastest, on="leg").merge(fast_time, on="leg")

    gate_pos = {}
    for rider in raw["participants"]:
        name = f"{rider['first_name']} {rider['last_name']}"
        if name not in finisher_names or len(rider["points"]) < 2: continue
        pts  = rider["points"]
        lats = np.array([p["lat"] for p in pts])
        lons = np.array([p["lon"] for p in pts])
        ts   = pd.to_datetime([p["ts"] for p in pts])
        for oi, (_, gate) in enumerate(gates_df.iterrows()):
            dists  = haversine_arr(lats, lons, gate["lat"], gate["lon"])
            within = np.where(dists <= RADIUS_M)[0]
            if len(within):
                gate_pos.setdefault(gate["gate"], []).append(oi)
    gpos = {g: np.mean(v) for g, v in gate_pos.items()}
    summary["_sort"] = summary["leg"].apply(lambda l: gpos.get(l.split(" → ")[0], 99))
    summary = summary.sort_values("_sort").drop(columns="_sort").reset_index(drop=True)
    summary["spread"] = summary["fast_kmh"] - summary["median_speed"]
    return summary


# ── PDF builder ───────────────────────────────────────────────────────────────

def build_pdf(out_path="via_race_26_executive_summary.pdf"):
    print("Loading data...")
    raw      = load_data()
    gates_df = load_gates()
    race_df  = build_race_df(raw, gates_df)

    finishers = (race_df[race_df["status"] == "FINISHED"]
                 .dropna(subset=["total_days"])
                 .sort_values("total_days")
                 .reset_index(drop=True))
    finishers["rank"]        = range(1, len(finishers) + 1)
    finishers["elapsed_hrs"] = finishers["total_days"] * 24
    # Rest% = detected sleep / elapsed (ref methodology — not (elapsed-ride)/elapsed)
    finishers["rest_pct"]    = (finishers["sleep_hrs"] / finishers["elapsed_hrs"] * 100).round(0)

    finisher_names = set(finishers["name"].tolist())

    print("Computing segments...")
    seg_speed   = build_segments_speed(raw, gates_df, finisher_names)
    seg_var     = build_segment_variation(raw, gates_df, finisher_names)
    fastest_legs = build_fastest_legs(raw, gates_df, finisher_names)

    # ── Summary stats ─────────────────────────────────────────────────────────
    n_finished  = (race_df["status"] == "FINISHED").sum()
    n_dnf       = (race_df["status"] == "DNF").sum()
    n_dns       = (race_df["status"] == "DNS").sum()
    n_starters  = n_finished + n_dnf + n_dns
    finish_rate = round(n_finished / n_starters * 100)
    med_dist    = finishers["total_dist_km"].dropna().median()
    min_dist    = finishers["total_dist_km"].dropna().min()
    max_dist    = finishers["total_dist_km"].dropna().max()
    winner      = finishers.iloc[0]
    last_fin    = finishers.iloc[-1]
    spread_days = round(last_fin["total_days"] - winner["total_days"], 2)
    med_days    = round(finishers["total_days"].median(), 2)
    speed_range = (f"{finishers['avg_speed_kmh'].dropna().min():.1f} – "
                   f"{finishers['avg_speed_kmh'].dropna().max():.1f} km/h")

    # ── Route highlights (Juhani) ─────────────────────────────────────────────
    juhani_row  = finishers[finishers["name"] == "Juhani Saario"].iloc[0]
    becker_row  = finishers[finishers["name"] == "Lucas Becker"].iloc[0]
    mücke_row   = finishers[finishers["name"] == "Mathias Mücke"].iloc[0]
    halix_row   = finishers[finishers["name"].str.contains("Halix")].iloc[0]
    juhani_gap_s = abs((juhani_row["total_days"] - becker_row["total_days"]) * 86400)
    juhani_vs_med = med_dist - juhani_row["total_dist_km"]

    # ── Matthew Downie segment dominance ──────────────────────────────────────
    downie_legs  = seg_speed[seg_speed["fast_rider"] == "Matthew Downie"]
    n_downie     = len(downie_legs)
    n_total_legs = len(seg_speed)
    downie_rank  = int(finishers[finishers["name"] == "Matthew Downie"]["rank"].iloc[0])

    # ── Category breakdown ────────────────────────────────────────────────────
    cat_rows = []
    for cat in ("F", "M", "Pair"):
        sub = race_df[race_df["category"] == cat]
        starters  = len(sub)
        fins      = (sub["status"] == "FINISHED").sum()
        rate      = round(fins / starters * 100) if starters else 0
        cat_rows.append([cat, str(starters), str(fins), f"{rate}%"])

    # ── DNF table ─────────────────────────────────────────────────────────────
    dnf_df = (race_df[race_df["status"] == "DNF"]
              .assign(gates_str=lambda d: d["gates_hit"].astype(str) + "/19")
              .sort_values("gates_hit", ascending=False)
              .reset_index(drop=True))

    # ── Document ──────────────────────────────────────────────────────────────
    doc = SimpleDocTemplate(
        out_path,
        pagesize=A4,
        rightMargin=18 * mm, leftMargin=18 * mm,
        topMargin=14 * mm,   bottomMargin=14 * mm,
    )
    W     = A4[0] - 36 * mm
    story = []

    # ── Title banner ──────────────────────────────────────────────────────────
    title_tbl = Table(
        [[Paragraph("VIA Race III — Ultima Thule", head_sty)],
         [Paragraph("Executive Summary · Netherlands → Norway · ~4,000 km · "
                    "July 24 – August 13, 2026", body_sty)]],
        colWidths=[W],
    )
    title_tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), ACCENT),
        ("TEXTCOLOR",     (0, 1), (-1, 1),  colors.HexColor("#f5c6bc")),
        ("TOPPADDING",    (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("LEFTPADDING",   (0, 0), (-1, -1), 10),
    ]))
    story.append(title_tbl)
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        "Distance note: All distances and speeds are clipped to each rider's verified race "
        "window (start gate → Volda finish gate). Post-finish tracker movement is excluded; "
        "four riders had their raw odometer corrected as a result.",
        note_sty,
    ))
    story.append(Spacer(1, 6))

    # ── Field Overview ────────────────────────────────────────────────────────
    story.append(Paragraph("Field Overview", sub_sty))
    ov_data = [
        ["Starters", "Finishers", "DNF", "DNS", "Finish Rate", "Race Window"],
        [str(n_starters), str(n_finished), str(n_dnf), str(n_dns),
         f"{finish_rate}%", "Jul 24 – Aug 13, 2026"],
    ]
    ov_tbl = Table(ov_data, colWidths=[W / 6] * 6)
    ov_tbl.setStyle(make_style())
    story.append(ov_tbl)

    # ── Key Metrics ───────────────────────────────────────────────────────────
    story.append(Spacer(1, 6))
    story.append(Paragraph("Key Metrics", sub_sty))
    km_data = [
        ["Metric", "Value"],
        ["Winning time",             f"{fmt_time(winner['total_days'])} — {winner['name']}"],
        ["Last finisher",            f"{fmt_time(last_fin['total_days'])} — {last_fin['name']}"],
        ["Spread (1st to last)",     f"{spread_days:.2f} days"],
        ["Median finish time",       f"{med_days:.2f} days"],
        ["Distance range (finishers)", f"{int(min_dist):,} – {int(max_dist):,} km "
                                       f"({int(max_dist - min_dist):,} km spread)"],
        ["Moving speed range",       speed_range],
    ]
    km_col_w = [W * 0.38, W * 0.62]
    km_tbl   = Table(km_data, colWidths=km_col_w)
    km_tbl.setStyle(make_style(extra=[("ALIGN", (0, 1), (-1, -1), "LEFT")]))
    story.append(km_tbl)

    # ── Full Results ──────────────────────────────────────────────────────────
    story.append(Spacer(1, 8))
    story.append(Paragraph("Full Results — 32 Finishers", sub_sty))
    story.append(Paragraph(
        "Rest% = proportion of elapsed time spent in detected rest stops "
        "(GPS speed < 3 km/h for ≥ 45 min).",
        note_sty,
    ))
    story.append(Spacer(1, 3))

    res_hdr  = ["#", "Rider", "Time", "km", "km/h", "Rest%"]
    res_rows = [res_hdr]
    podium_rows = []
    for _, row in finishers.iterrows():
        rank     = int(row["rank"])
        rest_pct = row["rest_pct"]
        res_rows.append([
            str(rank),
            row["name"],
            fmt_time(row["total_days"]),
            f"{int(row['total_dist_km']):,}" if pd.notna(row["total_dist_km"]) else "—",
            f"{row['avg_speed_kmh']:.1f}"     if pd.notna(row["avg_speed_kmh"]) else "—",
            f"{int(rest_pct)}%"               if pd.notna(rest_pct) else "—",
        ])
        if rank <= 3:
            podium_rows.append(rank)

    extra_res = []
    for r in podium_rows:
        extra_res += [("BACKGROUND", (0, r), (-1, r), GRN_BG),
                      ("TEXTCOLOR",  (0, r), (-1, r), GRN_INK),
                      ("FONTNAME",   (0, r), (-1, r), "Helvetica-Bold")]

    res_col_w = [W * f for f in [0.05, 0.38, 0.13, 0.12, 0.10, 0.10]]
    res_tbl   = Table(res_rows, colWidths=res_col_w, repeatRows=1)
    res_tbl.setStyle(make_style(extra=extra_res))
    story.append(res_tbl)

    # ── Route Highlights ──────────────────────────────────────────────────────
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width=W, thickness=0.5, color=colors.HexColor("#cccccc")))
    story.append(Spacer(1, 4))
    story.append(Paragraph("Route Highlights", sub_sty))

    hi_data = [
        ["Rider", "Rank", "Route", "Note"],
        ["Juhani Saario",
         f"#{int(juhani_row['rank'])}",
         f"{int(juhani_row['total_dist_km']):,} km",
         (f"{juhani_vs_med:.0f} km shorter than field median ({int(med_dist):,} km). "
          f"Matched #{int(becker_row['rank'])} Lucas Becker's finish time within "
          f"{juhani_gap_s / 60:.0f} min while riding "
          f"{int(becker_row['total_dist_km'] - juhani_row['total_dist_km'])} km less.")],
        ["Mathias Mücke",
         f"#{int(mücke_row['rank'])}",
         f"{int(mücke_row['total_dist_km']):,} km",
         "Shortest route among all finishers."],
        ["Enrico Halix & Malte Weise",
         f"#{int(halix_row['rank'])}",
         f"{int(halix_row['total_dist_km']):,} km",
         (f"Longest route — {int(halix_row['total_dist_km'] - med_dist)} km above median, "
          "via strategic loops through Strynefjell and Sognefjord circuits.")],
    ]
    hi_col_w = [W * f for f in [0.22, 0.07, 0.11, 0.60]]
    hi_tbl   = Table(hi_data, colWidths=hi_col_w)
    hi_tbl.setStyle(make_style(extra=[
        ("ALIGN",     (3, 1), (3, -1), "LEFT"),
        ("BACKGROUND",(0, 1), (-1, 1), YLW_BG),
        ("FONTNAME",  (0, 1), (-1, 1), "Helvetica-Bold"),
    ]))
    story.append(hi_tbl)

    # ── Fastest Segment Spotlights (avg speed) ────────────────────────────────
    story.append(Spacer(1, 10))
    story.append(Paragraph("Fastest Segment Spotlights — Average Moving Speed", sub_sty))

    LEG_CHAR = {
        "Sognefjellet → Lom":       "~1,400 m descent off Norway's highest road",
        "Suleskard → Lysebotn":     "High-alpine traverse to fjord bottom",
        "Start → Brocken":          "Opening flat blast across Germany",
        "Svøufallet → Atlantic Rd": "Norwegian coastal rollers",
        "Lysebotn → Botn":          "Long valley exit from Lysefjord",
        "Brocken → Fredriksten":    "Germany–Denmark–Norway push",
        "Fredriksten → Suleskard":  "Norway entry — fjord and valley climb",
        "Vøringfossen → Borgund":   "Hardangerfjord rim to inner valleys",
        "Botn → Vøringfossen":      "Fjord valley to Hardanger plateau",
        "Urnes → Gaularfjellet":    "Sognefjord ferry and mountain pass",
        "Vestkapp → Volda":         "Final coastal dash to the finish",
    }

    seg_speed["spread"] = seg_speed["fast_kmh"] - seg_speed["median_speed"]
    top5 = seg_speed.nlargest(5, "spread")

    spot_rows = [["Leg", "Character", "Fastest rider", "Best km/h", "Median km/h"]]
    top5_rows = []
    for pos, (_, row) in enumerate(top5.iterrows(), start=1):
        spot_rows.append([
            row["leg"],
            LEG_CHAR.get(row["leg"], ""),
            row["fast_rider"],
            f"{row['fast_kmh']:.1f}",
            f"{row['median_speed']:.1f}",
        ])
        if row["spread"] == seg_speed["spread"].max():
            top5_rows.append(pos)

    spot_col_w = [W * f for f in [0.22, 0.34, 0.22, 0.11, 0.11]]
    spot_tbl   = Table(spot_rows, colWidths=spot_col_w, repeatRows=1)
    extra_spot = [("ALIGN", (1, 1), (1, -1), "LEFT"), ("ALIGN", (2, 1), (2, -1), "LEFT")]
    for r in top5_rows:
        extra_spot.append(("BACKGROUND", (0, r), (-1, r), YLW_BG))
    spot_tbl.setStyle(make_style(extra=extra_spot))
    story.append(spot_tbl)

    # Suleskard→Lysebotn speed-vs-time note
    sul_row = seg_speed[seg_speed["leg"] == "Suleskard → Lysebotn"]
    if not sul_row.empty:
        sr = sul_row.iloc[0]
        if pd.notna(sr["fast_time_rider"]) and sr["fast_time_rider"] != sr["fast_rider"]:
            story.append(Spacer(1, 3))
            story.append(Paragraph(
                f"⏱ On Suleskard → Lysebotn, {sr['fast_rider']} recorded the highest moving "
                f"speed ({sr['fast_kmh']:.1f} km/h), but {sr['fast_time_rider']} completed "
                f"the leg gate-to-gate fastest ({sr['fastest_elapsed_hrs']:.1f} hrs) with fewer stops.",
                note_sty,
            ))

    # ── Matthew Downie callout ────────────────────────────────────────────────
    if n_downie >= 2:
        leg_list = ", ".join(
            f"{row['leg']} ({row['fast_kmh']:.1f} km/h)"
            for _, row in downie_legs.iterrows()
        )
        callout_text = (
            f"<b>Matthew Downie — fastest moving speed on {n_downie} of {n_total_legs} "
            f"common legs:</b> {leg_list}. "
            f"He finished #{downie_rank} overall, demonstrating elite segment pace across "
            "the full length of the route."
        )
        callout_tbl = Table([[Paragraph(callout_text, callout_sty)]], colWidths=[W])
        callout_tbl.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, -1), YLW_BG),
            ("BOX",           (0, 0), (-1, -1), 0.8, colors.HexColor("#e6b800")),
            ("TOPPADDING",    (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING",   (0, 0), (-1, -1), 8),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
        ]))
        story.append(Spacer(1, 6))
        story.append(callout_tbl)

    # ── All-leg speed summary ─────────────────────────────────────────────────
    story.append(Spacer(1, 8))
    story.append(Paragraph("Gate-to-Gate Segment Analysis — All Common Legs", sub_sty))
    story.append(Paragraph(
        f"Legs shared by ≥ 20 of the {n_finished} finishers. "
        "Avg moving speed excludes time below 2 km/h. ★ = Matthew Downie fastest.",
        note_sty,
    ))
    story.append(Spacer(1, 3))

    downie_leg_names = set(downie_legs["leg"].tolist())
    spd_hdr      = ["Leg", "Riders", "Median km/h", "Fastest rider", "Best km/h"]
    spd_rows     = [spd_hdr]
    hi_spd_rows  = []
    downie_rows  = []
    for pos, (_, row) in enumerate(seg_speed.iterrows(), start=1):
        leg_label = ("★ " + row["leg"]) if row["leg"] in downie_leg_names else row["leg"]
        spd_rows.append([
            leg_label,
            str(int(row["n_riders"])),
            f"{row['median_speed']:.1f}" if pd.notna(row["median_speed"]) else "—",
            row["fast_rider"],
            f"{row['fast_kmh']:.1f}"     if pd.notna(row["fast_kmh"])     else "—",
        ])
        if row.get("spread", 0) >= 8:
            hi_spd_rows.append(pos)
        if row["leg"] in downie_leg_names:
            downie_rows.append(pos)

    extra_spd = []
    for r in hi_spd_rows:
        extra_spd += [("BACKGROUND", (0, r), (-1, r), YLW_BG)]
    for r in downie_rows:
        extra_spd += [("FONTNAME", (3, r), (3, r), "Helvetica-Bold")]

    spd_col_w = [W * f for f in [0.30, 0.09, 0.14, 0.33, 0.12]]
    spd_tbl   = Table(spd_rows, colWidths=spd_col_w, repeatRows=1)
    spd_tbl.setStyle(make_style(extra=extra_spd + [
        ("ALIGN", (0, 1), (0, -1), "LEFT"),
        ("ALIGN", (3, 1), (3, -1), "LEFT"),
    ]))
    story.append(spd_tbl)
    story.append(Spacer(1, 3))
    story.append(Paragraph("Yellow = fastest beat median by ≥ 8 km/h.", note_sty))

    # ── Sleep & Rest ──────────────────────────────────────────────────────────
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width=W, thickness=0.5, color=colors.HexColor("#cccccc")))
    story.append(Spacer(1, 4))
    story.append(Paragraph("Sleep & Rest Analysis", sub_sty))
    story.append(Paragraph(
        "Rest periods: GPS speed < 3 km/h for 45+ consecutive minutes. "
        "Top 4 finishers rested under 15% of race time; field average "
        f"~{int(finishers['rest_pct'].mean())}%.",
        note_sty,
    ))
    story.append(Spacer(1, 3))

    slp_hdr  = ["Rider", "Stops", "Total rest", "Rest%", "Longest stop"]
    slp_rows = [slp_hdr]
    hi_rest  = []
    for _, row in finishers.iterrows():
        rp = row["rest_pct"]
        slp_rows.append([
            row["name"],
            str(int(row["n_sleeps"])),
            f"{row['sleep_hrs']:.1f}h",
            f"{int(rp)}%" if pd.notna(rp) else "—",
            f"{row['longest_stop_hrs']:.1f}h",
        ])
        if pd.notna(rp) and rp >= 35:
            hi_rest.append(int(row["rank"]))

    extra_slp = [("ALIGN", (0, 1), (0, -1), "LEFT")]
    for r in range(1, 4):
        extra_slp += [("BACKGROUND", (0, r), (-1, r), GRN_BG),
                      ("TEXTCOLOR",  (0, r), (-1, r), GRN_INK),
                      ("FONTNAME",   (0, r), (-1, r), "Helvetica-Bold")]
    for r in hi_rest:
        extra_slp += [("TEXTCOLOR",  (3, r), (3, r), RED_INK),
                      ("FONTNAME",   (3, r), (3, r), "Helvetica-Bold")]

    slp_col_w = [W * f for f in [0.38, 0.12, 0.16, 0.14, 0.20]]
    slp_tbl   = Table(slp_rows, colWidths=slp_col_w, repeatRows=1)
    slp_tbl.setStyle(make_style(extra=extra_slp))
    story.append(slp_tbl)

    # ── DNF Riders ────────────────────────────────────────────────────────────
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width=W, thickness=0.5, color=colors.HexColor("#cccccc")))
    story.append(Spacer(1, 4))
    story.append(Paragraph("DNF Riders — Gates Reached", sub_sty))

    dnf_hdr  = ["Rider", "Gates hit", "Distance"]
    dnf_rows = [dnf_hdr]
    for _, row in dnf_df.iterrows():
        dnf_rows.append([
            row["name"],
            row["gates_str"],
            f"{int(row['total_dist_km']):,} km" if pd.notna(row["total_dist_km"]) else "—",
        ])

    dnf_col_w = [W * f for f in [0.52, 0.20, 0.28]]
    dnf_tbl   = Table(dnf_rows, colWidths=dnf_col_w, repeatRows=1)
    dnf_tbl.setStyle(make_style(extra=[("ALIGN", (0, 1), (0, -1), "LEFT")]))
    story.append(dnf_tbl)

    # ── Category Breakdown ────────────────────────────────────────────────────
    story.append(Spacer(1, 10))
    story.append(Paragraph("Category Breakdown", sub_sty))
    cat_hdr  = ["Category", "Starters", "Finishers", "Finish rate"]
    cat_data = [cat_hdr] + cat_rows
    cat_col_w = [W * f for f in [0.25, 0.25, 0.25, 0.25]]
    cat_tbl   = Table(cat_data, colWidths=cat_col_w)
    cat_tbl.setStyle(make_style())
    story.append(cat_tbl)

    # ── Route Variation by Segment ────────────────────────────────────────────
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width=W, thickness=0.5, color=colors.HexColor("#cccccc")))
    story.append(Spacer(1, 4))
    story.append(Paragraph("Route Variation by Segment", sub_sty))
    story.append(Paragraph(
        "Distance spread between finishers gate-to-gate. Tight through Germany/Scandinavia, "
        "then explodes in the Norwegian fjords. Rows with ≥ 500 km spread are highlighted.",
        note_sty,
    ))
    story.append(Spacer(1, 3))

    var_hdr  = ["Segment", "N", "Min km", "Median", "Max km", "Spread", "Shortest", "Longest"]
    var_rows = [var_hdr]
    hi_var   = []
    for pos, (_, row) in enumerate(seg_var.iterrows(), start=1):
        var_rows.append([
            row["segment"],
            str(int(row["N"])),
            str(int(row["min_km"])),
            str(int(row["median_km"])),
            str(int(row["max_km"])),
            str(int(row["spread"])),
            row["shortest"],
            row["longest"],
        ])
        if row["spread"] >= 500:
            hi_var.append(pos)

    extra_var = [("ALIGN", (0, 1), (0, -1), "LEFT")]
    for r in hi_var:
        extra_var += [("BACKGROUND", (0, r), (-1, r), YLW_BG)]

    var_col_w = [W * f for f in [0.26, 0.05, 0.09, 0.09, 0.09, 0.09, 0.14, 0.14]]
    # Adjust so name cols are wider
    var_col_w = [W * f for f in [0.24, 0.05, 0.10, 0.10, 0.10, 0.10, 0.14, 0.17]]
    var_tbl   = Table(var_rows, colWidths=var_col_w, repeatRows=1)
    var_tbl.setStyle(make_style(extra=extra_var))
    story.append(var_tbl)

    # ── Fastest Segment Leaders ───────────────────────────────────────────────
    story.append(Spacer(1, 10))
    story.append(Paragraph("Fastest Segment Leaders", sub_sty))
    story.append(Paragraph(
        "Best elapsed time gate-to-gate among finishers.",
        note_sty,
    ))
    story.append(Spacer(1, 3))

    fl_hdr  = ["Segment", "Fastest rider", "Time"]
    fl_rows = [fl_hdr]
    for _, row in fastest_legs.iterrows():
        fl_rows.append([
            row["segment"],
            row["rider"],
            f"{row['elapsed_hrs']:.1f}h",
        ])

    fl_col_w = [W * f for f in [0.38, 0.44, 0.18]]
    fl_tbl   = Table(fl_rows, colWidths=fl_col_w, repeatRows=1)
    fl_tbl.setStyle(make_style(extra=[
        ("ALIGN", (0, 1), (0, -1), "LEFT"),
        ("ALIGN", (1, 1), (1, -1), "LEFT"),
    ]))
    story.append(fl_tbl)

    # ── Footer note ───────────────────────────────────────────────────────────
    story.append(Spacer(1, 8))
    story.append(HRFlowable(width=W, thickness=0.5, color=colors.HexColor("#cccccc")))
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        "Data: VIA Race III GPS export (via-race-26), exported 2026-09-02. "
        "Gate detection radius 1,000 m haversine. Status derived from gate compliance. "
        "Three riders are confirmed as official finishers by race organisers via override, "
        "independent of gate detection.",
        note_sty,
    ))

    print(f"Building PDF → {out_path}")
    doc.build(story)
    print("Done.")


if __name__ == "__main__":
    build_pdf()
