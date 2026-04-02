"""
UNSW IoT Behavioral Fingerprinting Pipeline + Visualizations
Smart Home Privacy Research - Jean-Yves Kotchi
Dataset: UNSW TMC 2018, Day: 16-09-23
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
from sklearn.preprocessing import LabelEncoder
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import warnings
warnings.filterwarnings("ignore")

# ── Style ──────────────────────────────────────────────────────────────────────
plt.rcParams.update({
    "figure.facecolor": "white",
    "axes.facecolor":   "#f8f8f8",
    "axes.grid":        True,
    "grid.color":       "white",
    "grid.linewidth":   1.2,
    "font.family":      "sans-serif",
    "axes.spines.top":  False,
    "axes.spines.right":False,
})
BLUE   = "#2196F3"
ORANGE = "#FF9800"
GREEN  = "#4CAF50"
RED    = "#F44336"
GRAY   = "#90A4AE"

# ── Device map ─────────────────────────────────────────────────────────────────
DEVICE_MAP = {
    "d0:52:a8:00:67:5e": "Smart Things",
    "44:65:0d:56:cc:d3": "Amazon Echo",
    "70:ee:50:18:34:43": "Netatmo Welcome",
    "f4:f2:6d:93:51:f1": "TP-Link Camera",
    "00:16:6c:ab:6b:88": "Samsung SmartCam",
    "30:8c:fb:2f:e4:b2": "Dropcam",
    "00:62:6e:51:27:2e": "Insteon Camera (wired)",
    "e8:ab:fa:19:de:4f": "Insteon Camera (wifi)",
    "00:24:e4:11:18:a8": "Withings Baby Monitor",
    "ec:1a:59:79:f4:89": "Belkin Wemo Switch",
    "50:c7:bf:00:56:39": "TP-Link Smart Plug",
    "74:c6:3b:29:d7:1d": "iHome",
    "ec:1a:59:83:28:11": "Belkin Wemo Motion",
    "18:b4:30:25:be:e4": "NEST Protect",
    "70:ee:50:03:b8:ac": "Netatmo Weather",
    "00:24:e4:1b:6f:96": "Withings Scale",
    "74:6a:89:00:2e:25": "Blipcare BP Meter",
    "00:24:e4:20:28:c6": "Withings Sleep Sensor",
    "d0:73:d5:01:83:08": "LiFX Smart Bulb",
    "18:b7:9e:02:20:44": "Triby Speaker",
    "e0:76:d0:33:bb:85": "PIX-STAR Photo-frame",
    "70:5a:0f:e4:9b:c0": "HP Printer",
    "08:21:ef:3b:fc:e3": "Samsung Galaxy Tab",
    "30:8c:fb:b6:ea:45": "Nest Dropcam",
    "40:f3:08:ff:1e:da": "Android Phone 1",
    "74:2f:68:81:69:42": "Laptop",
    "ac:bc:32:d4:6f:2f": "MacBook",
    "b4:ce:f6:a7:a3:c2": "Android Phone 2",
    "d0:a6:37:df:a1:e1": "iPhone",
    "f4:5c:89:93:cc:85": "MacBook/iPhone",
    "14:cc:20:51:33:ea": "TPLink Router (Gateway)",
}

# ══════════════════════════════════════════════════════════════════════════════
# STEP 1 — Load & label
# ══════════════════════════════════════════════════════════════════════════════
print("Loading data...")
df = pd.read_csv("16-09-23.csv")
df.columns = df.columns.str.strip()
df["datetime"] = pd.to_datetime(df["TIME"], unit="s")
df["device"]   = df["eth.src"].map(DEVICE_MAP)
df = df[df["device"].notna()]
df = df[df["device"] != "TPLink Router (Gateway)"]
print(f"  {len(df):,} packets | {df['device'].nunique()} devices")

# ══════════════════════════════════════════════════════════════════════════════
# STEP 2 — Feature extraction (60s windows)
# ══════════════════════════════════════════════════════════════════════════════
print("Extracting features...")
WINDOW_SEC = 60
df["window"] = (df["TIME"] // WINDOW_SEC).astype(int)

def extract_features(group):
    times  = group["TIME"].sort_values().values
    deltas = np.diff(times) if len(times) > 1 else np.array([0])
    return pd.Series({
        "packet_count":       len(group),
        "total_bytes":        group["Size"].sum(),
        "avg_pkt_size":       group["Size"].mean(),
        "std_pkt_size":       group["Size"].std(ddof=0),
        "max_pkt_size":       group["Size"].max(),
        "min_pkt_size":       group["Size"].min(),
        "avg_inter_arrival":  deltas.mean(),
        "std_inter_arrival":  deltas.std(ddof=0),
        "min_inter_arrival":  deltas.min(),
        "max_inter_arrival":  deltas.max(),
        "tcp_ratio":          (group["IP.proto"] == 6).mean(),
        "udp_ratio":          (group["IP.proto"] == 17).mean(),
        "unique_dst_ips":     group["IP.dst"].nunique(),
        "unique_dst_ports":   group["port.dst"].nunique(),
        "port_443_ratio":     (group["port.dst"] == 443).mean(),
        "port_80_ratio":      (group["port.dst"] == 80).mean(),
        "burst_score":        (deltas < 0.1).mean() if len(deltas) > 0 else 0,
    })

features_df = (
    df.groupby(["device", "window"])
      .apply(extract_features, include_groups=False)
      .reset_index()
      .fillna(0)
)

# Idle / active label
features_df["state"] = "idle"
for device, grp in features_df.groupby("device"):
    median_pkts = grp["packet_count"].median()
    mask = (features_df["device"] == device) & \
           (features_df["packet_count"] > median_pkts)
    features_df.loc[mask, "state"] = "active"

# ══════════════════════════════════════════════════════════════════════════════
# STEP 3 — Random Forest
# ══════════════════════════════════════════════════════════════════════════════
print("Training classifier...")
FEATURE_COLS = [c for c in features_df.columns
                if c not in ["device", "window", "state"]]

min_windows = 5
valid = features_df.groupby("device").size()
valid = valid[valid >= min_windows].index
clf_df = features_df[features_df["device"].isin(valid)].copy()

le = LabelEncoder()
clf_df["label"] = le.fit_transform(clf_df["device"])
X = clf_df[FEATURE_COLS].values
y = clf_df["label"].values

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y)

rf = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
rf.fit(X_train, y_train)
y_pred = rf.predict(X_test)

report = classification_report(y_test, y_pred,
                                target_names=le.classes_,
                                output_dict=True)
f1_scores = {k: v["f1-score"] for k, v in report.items()
             if k in le.classes_}

importance_df = pd.DataFrame({
    "feature":    FEATURE_COLS,
    "importance": rf.feature_importances_
}).sort_values("importance", ascending=False)

print("  Done. Overall accuracy:", round(report["accuracy"], 3))

# ══════════════════════════════════════════════════════════════════════════════
# CHART 1 — Idle vs Active packets per device
# ══════════════════════════════════════════════════════════════════════════════
print("Generating Chart 1: Idle vs Active...")

state_summary = features_df.groupby(["device", "state"])["packet_count"].mean().unstack(fill_value=0)
state_summary = state_summary.sort_values("active", ascending=True)

# Drop devices with too few windows for a meaningful bar
enough = features_df.groupby("device").size()
state_summary = state_summary[state_summary.index.isin(enough[enough >= 5].index)]

fig, ax = plt.subplots(figsize=(10, 7))
y_pos = np.arange(len(state_summary))
h = 0.35

ax.barh(y_pos + h/2, state_summary["active"],  h, color=ORANGE, label="Active")
ax.barh(y_pos - h/2, state_summary.get("idle", 0), h, color=BLUE,   label="Idle")

ax.set_yticks(y_pos)
ax.set_yticklabels(state_summary.index, fontsize=9)
ax.set_xlabel("Average packets per 60s window")
ax.set_title("Chart 1 — Idle vs Active traffic per device\n"
             "UNSW TMC 2018 dataset · 22 Sep 2016", fontsize=11, fontweight="bold")
ax.legend()
ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x):,}"))
plt.tight_layout()
plt.savefig("chart1_idle_vs_active.png", dpi=150)
plt.close()
print("  Saved: chart1_idle_vs_active.png")

# ══════════════════════════════════════════════════════════════════════════════
# CHART 2 — RF classifier F1-score per device
# ══════════════════════════════════════════════════════════════════════════════
print("Generating Chart 2: Classifier accuracy per device...")

f1_series = pd.Series(f1_scores).sort_values()
colors = [GREEN if v >= 0.95 else ORANGE if v >= 0.80 else RED
          for v in f1_series]

fig, ax = plt.subplots(figsize=(10, 6))
bars = ax.barh(f1_series.index, f1_series.values, color=colors)

for bar, val in zip(bars, f1_series.values):
    ax.text(val + 0.005, bar.get_y() + bar.get_height()/2,
            f"{val:.2f}", va="center", fontsize=8)

ax.axvline(0.95, color=GREEN,  linestyle="--", linewidth=1, alpha=0.7, label="≥ 0.95 (excellent)")
ax.axvline(0.80, color=ORANGE, linestyle="--", linewidth=1, alpha=0.7, label="≥ 0.80 (good)")
ax.set_xlim(0, 1.08)
ax.set_xlabel("F1-score")
ax.set_title("Chart 2 — Device identification accuracy (Random Forest)\n"
             "Traffic metadata only · no packet contents", fontsize=11, fontweight="bold")
ax.legend(fontsize=8)
plt.tight_layout()
plt.savefig("chart2_classifier_accuracy.png", dpi=150)
plt.close()
print("  Saved: chart2_classifier_accuracy.png")

# ══════════════════════════════════════════════════════════════════════════════
# CHART 3 — Packet count over 24h for camera devices
# (mirrors your Wireshark I/O graphs from Week 3)
# ══════════════════════════════════════════════════════════════════════════════
print("Generating Chart 3: 24h traffic timeline for cameras...")

CAMERAS = ["Dropcam", "Netatmo Welcome", "Samsung SmartCam", "TP-Link Camera"]
cam_df  = df[df["device"].isin(CAMERAS)].copy()
cam_df["hour_bin"] = (df["TIME"] // 300).astype(int)  # 5-min buckets

timeline = (cam_df.groupby(["device", "hour_bin"])
                  .size()
                  .reset_index(name="packets"))
timeline["time_offset_hr"] = (timeline["hour_bin"] - timeline["hour_bin"].min()) * 5 / 60

cam_colors = {
    "Dropcam":         "#E53935",
    "Netatmo Welcome": "#8E24AA",
    "Samsung SmartCam":"#1E88E5",
    "TP-Link Camera":  "#43A047",
}

fig, axes = plt.subplots(len(CAMERAS), 1, figsize=(12, 9), sharex=True)
fig.suptitle("Chart 3 — 24-hour packet timeline (camera devices)\n"
             "Mirrors your Wireshark I/O graphs · UNSW dataset",
             fontsize=11, fontweight="bold")

for ax, cam in zip(axes, CAMERAS):
    sub = timeline[timeline["device"] == cam]
    if sub.empty:
        ax.set_ylabel(cam, fontsize=8)
        continue
    ax.fill_between(sub["time_offset_hr"], sub["packets"],
                    alpha=0.3, color=cam_colors[cam])
    ax.plot(sub["time_offset_hr"], sub["packets"],
            color=cam_colors[cam], linewidth=1)
    ax.set_ylabel("Pkts / 5 min", fontsize=8)
    ax.set_title(cam, fontsize=9, loc="left", pad=2)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x):,}"))

axes[-1].set_xlabel("Hours since capture start")
plt.tight_layout()
plt.savefig("chart3_camera_timeline.png", dpi=150)
plt.close()
print("  Saved: chart3_camera_timeline.png")

# ══════════════════════════════════════════════════════════════════════════════
# CHART 4 — Cross-dataset comparison: your Wyze Cam vs UNSW cameras
# ══════════════════════════════════════════════════════════════════════════════
print("Generating Chart 4: Cross-dataset comparison...")

# Active/idle ratios
unsw_cameras = {}
for cam in CAMERAS:
    sub = features_df[features_df["device"] == cam]
    if sub.empty:
        continue
    idle_pkts   = sub[sub["state"] == "idle"]["packet_count"].mean()
    active_pkts = sub[sub["state"] == "active"]["packet_count"].mean()
    if idle_pkts > 0:
        unsw_cameras[cam] = round(active_pkts / idle_pkts, 1)

# Add your Wyze Cam result from Week 3
wyze_ratio = 8.6   # ~4210 / 491 pkts per 3-min window
all_cameras = {"Your Wyze Cam\n(Week 3 capture)": wyze_ratio, **unsw_cameras}

labels  = list(all_cameras.keys())
ratios  = list(all_cameras.values())
colors  = [RED] + [BLUE] * len(unsw_cameras)  # red = your device

fig, ax = plt.subplots(figsize=(9, 5))
bars = ax.bar(labels, ratios, color=colors, width=0.5, edgecolor="white")

for bar, val in zip(bars, ratios):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
            f"{val}x", ha="center", fontsize=10, fontweight="bold")

ax.axhline(wyze_ratio, color=RED, linestyle="--", linewidth=1,
           alpha=0.5, label="Your Wyze Cam baseline")
ax.set_ylabel("Active / Idle packet ratio")
ax.set_title("Chart 4 — Cross-dataset comparison\n"
             "Active/idle packet ratio: your Wyze Cam vs UNSW cameras",
             fontsize=11, fontweight="bold")
ax.set_ylim(0, max(ratios) * 1.25)
ax.legend(fontsize=8)

# Annotate the pattern
ax.text(0.98, 0.92,
        "All cameras spike when active.\nRatio varies by vendor.",
        transform=ax.transAxes, ha="right", va="top",
        fontsize=8, color="#555",
        bbox=dict(boxstyle="round,pad=0.3", facecolor="#fff8e1", edgecolor="#ccc"))

plt.xticks(fontsize=8)
plt.tight_layout()
plt.savefig("chart4_cross_dataset.png", dpi=150)
plt.close()
print("  Saved: chart4_cross_dataset.png")

print()
print("All 4 charts saved in the same folder as this script.")
print("  chart1_idle_vs_active.png")
print("  chart2_classifier_accuracy.png")
print("  chart3_camera_timeline.png")
print("  chart4_cross_dataset.png")
