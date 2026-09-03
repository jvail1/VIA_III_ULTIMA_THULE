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

INK     = colors.HexColor("#111111")
HDR_BG  = colors.HexColor("#0d1b2a")
HDR_FG  = colors.white
S1      = colors.white
S2      = colors.HexColor("#eef2f7")
ACCENT  = colors.HexColor("#c0392b")
GRN_BG  = colors.HexColor("#e9f7ef")
GRN_INK = colors.HexColor("#1a5c2a")
YLW_BG  = colors.HexColor("#fef9e7")
LGRY_BG = colors.HexColor("#f5f5f5")
BLUE_INK = colors.HexColor("#1a3a6b")

# ── Styles ────────────────────────────────────────────────────────────────────

styles   = getSampleStyleSheet()
body_sty = ParagraphStyle("body", parent=styles["Normal"], fontSize=8.5,
                           leading=12, textColor=INK)
head_sty = ParagraphStyle("head", parent=styles["Heading1"], fontSize=14,
                           textColor=HDR_FG, spaceAfter=4)
sub_sty  = ParagraphStyle("sub", parent=styles["Heading2"], fontSize=10,
                           textColor=BLUE_INK, spaceBefore=8, spaceAfter=4)
note_sty = ParagraphStyle("note", parent=styles["Normal"], fontSize=7.5,
                           leading=11, textColor=colors.HexColor("#444444"),
                           leftIndent=6)
callout_sty = ParagraphStyle("callout", parent=styles["Normal"], fontSize=8.5,
                              leading=12, textColor=INK, leftIndent=8, rightIndent=8)

def make_style(extra=None):
    base = [
        ("BACKGROUND",  (0, 0), (-1, 0), HDR_BG),
        ("TEXTCOLOR",   (0, 0), (-1, 0), HDR_FG),
        ("FONTNAME",    (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",    (0, 0), (-1, 0), 7.5),
        ("FONTNAME",    (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE",    (0, 1), (-1, -1), 7.5),
        ("TEXTCOLOR",   (0, 1), (-1, -1), INK),
        ("ALIGN",       (0, 0), (-1, -1), "CENTER"),
        ("ALIGN",       (1, 1), (1, -1), "LEFT"),
        ("VALIGN",      (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUND", (0, 1), (-1, -1), [S1, S2]),
        ("GRID",        (0, 0), (-1, -1), 0.3, colors.HexColor("#cccccc")),
        ("TOPPADDING",  (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING",(0, 0), (-1, -1), 4),
    ]
    if extra:
        base.extend(extra)
    return TableStyle(base)


# ── Data loading ──────────────────────────────────────────────────────────────

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


GATE_SHORT = {
    "De Proloog, Amerongen": "Start", "Brocken": "Brocken",
    "Fredriksten fortress": "Fredriksten", "Botn Fjellstue": "Botn",
    "Suleskard": "Suleskard", "Lysebotn": "Lysebotn",
    "Vøringfossen": "Vøringfossen", "Sognefjellet": "Sognefjellet",
    "Gaularfjellet": "Gaularfjellet", "Strynefjellsveg": "Strynefjell",
    "Borgund Stavkyrkje": "Borgund", "Urnes stavkyrkje": "Urnes",
    "Lom Stavkyrkje": "Lom", "Svøufallet": "Svøufallet",
    "Atlantic road": "Atlantic Rd", "Trollstigen": "Trollstigen",
    "Dalsnibba": "Dalsnibba", "Vestkapp": "Vestkapp", "Volda": "Volda",
}

OFFICIAL_OVERRIDES = {
    "Bruno Wicht":   {},
    "Adam Bialek":   {"total_days": 8.62,  "ride_time_hrs": 162.1, "avg_speed_kmh": 21.5},
    "Jair Hoogland": {"total_days": 9.49,  "ride_time_hrs": 175.1, "avg_speed_kmh": 19.6},
}

RADIUS_M = 1000
R_EARTH  = 6_371_000


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


def compute_elev_gain(pts):
    alts = np.array([p["alt"] for p in pts], dtype=float)
    alts[(alts < -100) | (alts > 2500)] = np.nan
    alts = pd.Series(alts).ffill().bfill().values
    return float(np.diff(alts)[np.diff(alts) > 5].sum())


def detect_sleep(pts, t_start, t_finish, speed_thresh=3, min_dur_min=45):
    if t_start is None or t_finish is None or len(pts) < 2:
        return 0.0, 0
    ts_arr  = pd.to_datetime([p["ts"] for p in pts])
    spd_arr = np.array([p["speed"] for p in pts])
    in_race = (ts_arr >= t_start) & (ts_arr <= t_finish)
    ts_r    = ts_arr[in_race]
    spd_r   = spd_arr[in_race]
    if len(ts_r) < 2:
        return 0.0, 0
    stopped = spd_r < speed_thresh
    total_hrs, n_bouts, in_bout = 0.0, 0, False
    for i, s in enumerate(stopped):
        if s and not in_bout:
            bout_start = i; in_bout = True
        elif not s and in_bout:
            dur = (ts_r[i - 1] - ts_r[bout_start]).total_seconds() / 60
            if dur >= min_dur_min:
                total_hrs += dur / 60; n_bouts += 1
            in_bout = False
    if in_bout:
        dur = (ts_r[-1] - ts_r[bout_start]).total_seconds() / 60
        if dur >= min_dur_min:
            total_hrs += dur / 60; n_bouts += 1
    return round(total_hrs, 1), n_bouts


# ── Build race DataFrame ──────────────────────────────────────────────────────

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
        if len(pts) < 2:
            rows.append({"name": name, "status": "DNS",
                         "total_dist_km": None, "total_days": None,
                         "ride_time_hrs": None, "avg_speed_kmh": None,
                         "elev_gain_m": None, "sleep_hrs": 0.0, "n_sleeps": 0,
                         "t_start": None, "t_finish": None})
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

        t_start   = first_gate_hit(lats, lons, ts, start_g["lat"], start_g["lon"])
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

        sleep_hrs, n_sleeps = detect_sleep(pts, t_start, t_finish)
        status = "FINISHED" if gates_hit == 19 and t_finish else "DNF"

        rows.append({
            "name": name, "status": status,
            "total_dist_km": total_dist, "total_days": total_days,
            "ride_time_hrs": ride_hrs,   "avg_speed_kmh": avg_speed,
            "elev_gain_m": elev_gain,    "sleep_hrs": sleep_hrs,
            "n_sleeps": n_sleeps,        "t_start": t_start, "t_finish": t_finish,
        })

    df = pd.DataFrame(rows)
    for nm, ovr in OFFICIAL_OVERRIDES.items():
        mask = df["name"] == nm
        if mask.any():
            df.loc[mask, "status"] = "FINISHED"
            for col, val in ovr.items():
                if col in df.columns:
                    df.loc[mask, col] = val

    return df


def build_segments(raw, gates_df, finisher_names):
    """Return (detail_df, summary_df) for legs shared by ≥20 finishers."""
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
            moving = speeds[in_seg]
            moving = moving[moving > 2]
            avg_spd = round(float(moving.mean()), 1) if len(moving) > 0 else None
            seg_rows.append({
                "rider":     name,
                "from_gate": g0, "to_gate": g1,
                "elapsed_hrs": round((t1 - t0).total_seconds() / 3600, 2),
                "avg_speed":   avg_spd,
            })

    df = pd.DataFrame(seg_rows)
    df["leg"] = (df["from_gate"].map(lambda g: GATE_SHORT.get(g, g))
                 + " → "
                 + df["to_gate"].map(lambda g: GATE_SHORT.get(g, g)))

    counts      = df.groupby(["from_gate", "to_gate"]).size().reset_index(name="n")
    common      = counts[counts["n"] >= 20]
    common_keys = set(zip(common["from_gate"], common["to_gate"]))
    df          = df[df.apply(lambda r: (r["from_gate"], r["to_gate"]) in common_keys, axis=1)].copy()

    stats = df.groupby("leg").agg(
        n_riders    =("rider",     "count"),
        median_speed=("avg_speed", "median"),
    ).reset_index()

    fastest = (df.dropna(subset=["avg_speed"])
               .sort_values("avg_speed", ascending=False)
               .groupby("leg", as_index=False).first()
               [["leg", "rider", "avg_speed"]]
               .rename(columns={"rider": "fast_rider", "avg_speed": "fast_kmh"}))

    summary = stats.merge(fastest, on="leg")

    gate_visit_mean = {}
    for rider in raw["participants"]:
        name = f"{rider['first_name']} {rider['last_name']}"
        if name not in finisher_names or len(rider["points"]) < 2:
            continue
        pts   = rider["points"]
        lats  = np.array([p["lat"] for p in pts])
        lons  = np.array([p["lon"] for p in pts])
        ts    = pd.to_datetime([p["ts"] for p in pts])
        for order_i, (_, gate) in enumerate(gates_df.iterrows()):
            dists  = haversine_arr(lats, lons, gate["lat"], gate["lon"])
            within = np.where(dists <= RADIUS_M)[0]
            if len(within):
                gn = gate["gate"]
                gate_visit_mean.setdefault(gn, []).append(order_i)

    gate_pos = {g: np.mean(v) for g, v in gate_visit_mean.items()}
    summary["_sort"] = summary["leg"].apply(
        lambda l: gate_pos.get(l.split(" → ")[0], 99)
    )
    summary = summary.sort_values("_sort").drop(columns="_sort").reset_index(drop=True)
    return df, summary


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
    finishers["rest_hrs"]    = finishers["elapsed_hrs"] - finishers["ride_time_hrs"].fillna(0)
    finishers["rest_pct"]    = (finishers["rest_hrs"] / finishers["elapsed_hrs"] * 100).round(0)

    finisher_names = set(finishers["name"].tolist())

    print("Computing segments...")
    _, seg_summary = build_segments(raw, gates_df, finisher_names)

    total_riders   = len(race_df)
    n_finishers    = (race_df["status"] == "FINISHED").sum()
    n_dnf          = (race_df["status"] == "DNF").sum()
    n_dns          = (race_df["status"] == "DNS").sum()
    med_dist       = finishers["total_dist_km"].dropna().median()
    min_dist       = finishers["total_dist_km"].dropna().min()
    max_dist       = finishers["total_dist_km"].dropna().max()
    med_sleep      = finishers["sleep_hrs"].median()

    # ── Interesting highlights from data ──────────────────────────────────────
    # Juhani Saario route savings
    juhani_row   = finishers[finishers["name"] == "Juhani Saario"].iloc[0]
    becker_row   = finishers[finishers["name"] == "Lucas Becker"].iloc[0]
    juhani_dist  = juhani_row["total_dist_km"]
    juhani_rank  = int(juhani_row["rank"])
    becker_dist  = becker_row["total_dist_km"]
    becker_rank  = int(becker_row["rank"])
    juhani_gap_s = (juhani_row["total_days"] - becker_row["total_days"]) * 86400
    juhani_vs_median = med_dist - juhani_dist

    mücke_row  = finishers[finishers["name"] == "Mathias Mücke"].iloc[0]
    halix_row  = finishers[finishers["name"].str.contains("Halix")].iloc[0]

    # Document setup
    doc = SimpleDocTemplate(
        out_path,
        pagesize=A4,
        rightMargin=18 * mm, leftMargin=18 * mm,
        topMargin=14 * mm,   bottomMargin=14 * mm,
    )
    W = A4[0] - 36 * mm
    story = []

    # ── Title banner ──────────────────────────────────────────────────────────
    title_tbl = Table(
        [[Paragraph("VIA Race III — Ultima Thule", head_sty)],
         [Paragraph("Executive Summary · Netherlands → Norway · ~4,000 km · Race variant", body_sty)]],
        colWidths=[W],
    )
    title_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), ACCENT),
        ("TEXTCOLOR",  (0, 1), (-1, 1),  colors.HexColor("#f5c6bc")),
        ("TOPPADDING",    (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("LEFTPADDING",   (0, 0), (-1, -1), 10),
    ]))
    story.append(title_tbl)
    story.append(Spacer(1, 6))

    # ── Race overview KPIs ────────────────────────────────────────────────────
    story.append(Paragraph("Race Overview", sub_sty))
    kpi_data = [
        ["Start", "Finish", "Participants", "Finishers", "DNF", "DNS"],
        ["24 Jul 2026", "1 Aug 2026", str(total_riders), str(n_finishers), str(n_dnf), str(n_dns)],
    ]
    kpi_tbl = Table(kpi_data, colWidths=[W / 6] * 6)
    kpi_tbl.setStyle(make_style())
    story.append(kpi_tbl)
    story.append(Spacer(1, 4))

    dist_data = [
        ["Shortest route", "Median route", "Longest route", "Median sleep / rider"],
        [f"{min_dist:,.0f} km", f"{med_dist:,.0f} km", f"{max_dist:,.0f} km", f"{med_sleep:.0f} hrs"],
    ]
    dist_tbl = Table(dist_data, colWidths=[W / 4] * 4)
    dist_tbl.setStyle(make_style())
    story.append(dist_tbl)
    story.append(Spacer(1, 8))

    # ── Finisher results ──────────────────────────────────────────────────────
    story.append(Paragraph("Finisher Results", sub_sty))

    res_header = ["#", "Rider", "Days", "Ride hrs", "km/h", "Dist km", "Elev m"]
    res_rows   = [res_header]
    podium_rows = []
    high_rest_rows = []
    for _, row in finishers.iterrows():
        rank = int(row["rank"])
        res_rows.append([
            str(rank),
            row["name"],
            f"{row['total_days']:.2f}" if pd.notna(row["total_days"]) else "—",
            f"{row['ride_time_hrs']:.1f}" if pd.notna(row["ride_time_hrs"]) else "—",
            f"{row['avg_speed_kmh']:.1f}" if pd.notna(row["avg_speed_kmh"]) else "—",
            f"{row['total_dist_km']:,.0f}" if pd.notna(row["total_dist_km"]) else "—",
            f"{row['elev_gain_m']:,.0f}" if pd.notna(row["elev_gain_m"]) else "—",
        ])
        if rank <= 3:
            podium_rows.append(rank)
        if pd.notna(row["rest_pct"]) and row["rest_pct"] >= 50:
            high_rest_rows.append(rank)

    col_w = [W * f for f in [0.05, 0.30, 0.09, 0.10, 0.08, 0.10, 0.10, 0.10, 0.08]]
    # Adjust widths for 7 columns
    col_w7 = [W * f for f in [0.05, 0.35, 0.10, 0.11, 0.10, 0.11, 0.10, 0.08]]
    col_w7 = [W * f for f in [0.05, 0.34, 0.10, 0.10, 0.09, 0.11, 0.11]]

    extra_res = []
    for r in podium_rows:
        extra_res += [
            ("BACKGROUND", (0, r), (-1, r), GRN_BG),
            ("TEXTCOLOR",  (0, r), (-1, r), GRN_INK),
            ("FONTNAME",   (0, r), (-1, r), "Helvetica-Bold"),
        ]

    res_tbl = Table(res_rows, colWidths=col_w7, repeatRows=1)
    res_tbl.setStyle(make_style(extra=extra_res))
    story.append(res_tbl)
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        "Days = gate-to-gate elapsed time. Ride hrs = time above 2 km/h. "
        "km/h = avg moving speed. Dist km = odometer clipped to race window. "
        "Three riders are confirmed as official finishers by race organisers via override.",
        note_sty,
    ))

    # ── Route Highlights ──────────────────────────────────────────────────────
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width=W, thickness=0.5, color=colors.HexColor("#cccccc")))
    story.append(Spacer(1, 4))
    story.append(Paragraph("Route Highlights", sub_sty))

    hi_data = [
        ["Rider", "Rank", "Route", "Note"],
        ["Juhani Saario",
         f"#{juhani_rank}",
         f"{juhani_dist:,.0f} km",
         (f"{juhani_vs_median:.0f} km shorter than field median ({med_dist:,.0f} km). "
          f"Matched #{becker_rank} Lucas Becker's finish time within "
          f"{abs(juhani_gap_s) / 60:.0f} min while riding {becker_dist - juhani_dist:.0f} km less.")],
        ["Mathias Mücke",
         f"#{int(mücke_row['rank'])}",
         f"{mücke_row['total_dist_km']:,.0f} km",
         "Shortest route among all finishers — 30 km less than Juhani Saario."],
        ["Enrico Halix & Malte Weise",
         f"#{int(halix_row['rank'])}",
         f"{halix_row['total_dist_km']:,.0f} km",
         (f"Longest route by {halix_row['total_dist_km'] - med_dist:.0f} km above median, "
          "accumulating strategic loops to collect gates via Strynefjell and Sognefjord circuits.")],
    ]
    hi_col_w = [W * f for f in [0.22, 0.07, 0.11, 0.60]]
    hi_tbl   = Table(hi_data, colWidths=hi_col_w)
    hi_tbl.setStyle(make_style(extra=[
        ("ALIGN",     (3, 1), (3, -1), "LEFT"),
        ("BACKGROUND",(0, 1), (-1, 1), YLW_BG),
        ("FONTNAME",  (0, 1), (-1, 1), "Helvetica-Bold"),
    ]))
    story.append(hi_tbl)

    # ── Fastest Segment Spotlight ─────────────────────────────────────────────
    story.append(Spacer(1, 10))
    story.append(Paragraph("Fastest Segment Spotlights", sub_sty))

    spot_data = [
        ["Leg", "Character", "Fastest", "Best km/h", "Field median"],
        ["Sognefjellet → Lom",
         "~1,400 m descent off the highest road in Norway",
         "Matthew Downie",  "38.7", "29.6"],
        ["Suleskard → Lysebotn",
         "High-alpine traverse to fjord bottom",
         "Juhani Saario ⏱",  "20.3 (fastest time: 2.5 hrs)", "17.1"],
        ["Start → Brocken",
         "Opening flat blast across Germany",
         "Lucas Becker",    "29.1", "25.6"],
        ["Svøufallet → Atlantic Rd",
         "Norwegian coastal rollers",
         "Lucas Becker / Juhani Saario", "25.1", "21.9"],
        ["Lysebotn → Botn",
         "Long valley exit from Lysefjord",
         "Matthew Downie",  "25.3", "18.3"],
    ]
    spot_col_w = [W * f for f in [0.22, 0.33, 0.22, 0.13, 0.10]]
    spot_tbl   = Table(spot_data, colWidths=spot_col_w, repeatRows=1)
    spot_tbl.setStyle(make_style(extra=[
        ("ALIGN", (1, 1), (1, -1), "LEFT"),
        ("ALIGN", (2, 1), (2, -1), "LEFT"),
        ("BACKGROUND", (0, 1), (-1, 1), YLW_BG),  # Sognefjellet highlight
    ]))
    story.append(spot_tbl)
    story.append(Spacer(1, 3))
    story.append(Paragraph(
        "⏱ denotes fastest elapsed time on that leg, not necessarily highest moving speed.",
        note_sty,
    ))

    # ── All-leg segment summary ───────────────────────────────────────────────
    story.append(Spacer(1, 8))
    story.append(Paragraph("Gate-to-Gate Segment Analysis — All Common Legs", sub_sty))
    story.append(Paragraph(
        f"Legs shared by ≥ 20 of the {n_finishers} finishers. "
        "Avg moving speed excludes time below 2 km/h.",
        note_sty,
    ))
    story.append(Spacer(1, 3))

    seg_header = ["Leg", "Riders", "Median km/h", "Fastest rider", "Best km/h"]
    seg_rows_data = [seg_header]
    hi_spread_rows = []
    for i, row in seg_summary.iterrows():
        spread = row["fast_kmh"] - row["median_speed"] if pd.notna(row["fast_kmh"]) else 0
        seg_rows_data.append([
            row["leg"],
            str(int(row["n_riders"])),
            f"{row['median_speed']:.1f}" if pd.notna(row["median_speed"]) else "—",
            row["fast_rider"],
            f"{row['fast_kmh']:.1f}"    if pd.notna(row["fast_kmh"])    else "—",
        ])
        if spread >= 8:
            hi_spread_rows.append(i + 1)

    extra_seg = []
    for r in hi_spread_rows:
        extra_seg += [("BACKGROUND", (0, r), (-1, r), YLW_BG)]

    seg_col_w = [W * f for f in [0.30, 0.09, 0.14, 0.33, 0.12]]
    seg_tbl   = Table(seg_rows_data, colWidths=seg_col_w, repeatRows=1)
    seg_tbl.setStyle(make_style(extra=extra_seg + [
        ("ALIGN", (0, 1), (0, -1), "LEFT"),
        ("ALIGN", (3, 1), (3, -1), "LEFT"),
    ]))
    story.append(seg_tbl)
    story.append(Spacer(1, 3))
    story.append(Paragraph(
        "Yellow rows = legs where fastest rider beat field median by ≥ 8 km/h.",
        note_sty,
    ))

    # ── Sleep & Rest Patterns ─────────────────────────────────────────────────
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width=W, thickness=0.5, color=colors.HexColor("#cccccc")))
    story.append(Spacer(1, 4))
    story.append(Paragraph("Sleep & Rest Patterns", sub_sty))
    story.append(Paragraph(
        "Rest detected as GPS speed < 3 km/h sustained ≥ 45 min within the race window. "
        "Rest % = (elapsed − ride time) / elapsed.",
        note_sty,
    ))
    story.append(Spacer(1, 3))

    slp_header = ["#", "Rider", "Sleep hrs", "Stops", "Rest %", "Ride hrs", "Days"]
    slp_rows   = [slp_header]
    hi_rest_rows_slp = []
    for _, row in finishers.iterrows():
        rank = int(row["rank"])
        rest_pct = row["rest_pct"]
        slp_rows.append([
            str(rank),
            row["name"],
            f"{row['sleep_hrs']:.1f}" if pd.notna(row["sleep_hrs"]) else "—",
            str(int(row["n_sleeps"])) if pd.notna(row["n_sleeps"]) else "—",
            f"{rest_pct:.0f}%" if pd.notna(rest_pct) else "—",
            f"{row['ride_time_hrs']:.1f}" if pd.notna(row["ride_time_hrs"]) else "—",
            f"{row['total_days']:.2f}"    if pd.notna(row["total_days"])    else "—",
        ])
        if pd.notna(rest_pct) and rest_pct >= 50:
            hi_rest_rows_slp.append(rank)

    extra_slp = []
    for r in hi_rest_rows_slp:
        extra_slp += [
            ("TEXTCOLOR",  (4, r), (4, r), colors.HexColor("#922b21")),
            ("FONTNAME",   (4, r), (4, r), "Helvetica-Bold"),
        ]
    for r in range(1, 4):
        extra_slp += [
            ("BACKGROUND", (0, r), (-1, r), GRN_BG),
            ("TEXTCOLOR",  (0, r), (-1, r), GRN_INK),
            ("FONTNAME",   (0, r), (-1, r), "Helvetica-Bold"),
        ]

    slp_col_w = [W * f for f in [0.05, 0.34, 0.12, 0.09, 0.10, 0.12, 0.10]]
    slp_tbl   = Table(slp_rows, colWidths=slp_col_w, repeatRows=1)
    slp_tbl.setStyle(make_style(extra=extra_slp))
    story.append(slp_tbl)
    story.append(Spacer(1, 3))
    story.append(Paragraph(
        "Red Rest % = ≥ 50% of elapsed time not moving. "
        "Green rows = top 3 finishers.",
        note_sty,
    ))

    # ── Notes ─────────────────────────────────────────────────────────────────
    story.append(Spacer(1, 8))
    story.append(HRFlowable(width=W, thickness=0.5, color=colors.HexColor("#cccccc")))
    story.append(Spacer(1, 4))
    story.append(Paragraph("Notes", sub_sty))
    notes = [
        "Race distance is odometer clipped to the start–finish gate window, not raw tracker "
        "odometer. Raw odo inflates distance for riders whose trackers kept logging after "
        "finishing; four riders had their raw odometer corrected as a result.",
        "Gate detection radius: 1,000 m (haversine). 500 m produced false negatives on "
        "legitimately-ridden gates.",
        "Three riders are confirmed as official finishers by race organisers via override; "
        "their finish times and some metrics are set from official results.",
        "GPS data exported 2026-09-02. All analysis uses Race variant only (62 of 104 entrants).",
    ]
    for n in notes:
        story.append(Paragraph(f"• {n}", note_sty))
        story.append(Spacer(1, 2))

    print(f"Building PDF → {out_path}")
    doc.build(story)
    print("Done.")


if __name__ == "__main__":
    build_pdf()
