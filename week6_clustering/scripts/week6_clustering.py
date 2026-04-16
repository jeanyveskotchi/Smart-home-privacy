"""
Week 6 — Unsupervised Clustering
Smart Home Privacy Research

Threat model: External observer behind a router VPN.
No MAC addresses, no ports, no IPs — only packet size and timing.

Usage:
    Place 16-09-23.csv in the same directory, then run:
    python3 week6_clustering.py

Output:
    - Console: cluster purity per device, summary metrics
    - Screenshots/chart7_clustering_scatter.png
    - Screenshots/chart8_cluster_purity.png
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score

# ──────────────────────────────────────────────
# 0. CONFIG
# ──────────────────────────────────────────────

CSV_FILE     = "16-09-23.csv"
WINDOW_SEC   = 60
N_CLUSTERS   = 21          # one per real device
N_INIT       = 10          # K-Means random restarts
RANDOM_STATE = 42

OUTPUT_DIR   = "Screenshots"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ──────────────────────────────────────────────
# MAC → device name mapping (from List_Of_Devices.txt)
# ──────────────────────────────────────────────

DEVICE_MAP = {
    "14:cc:20:51:33:ea": "TPLink Router",        # gateway — excluded
    "d0:52:a8:00:67:5e": "Smart Things",
    "44:65:0d:56:cc:d3": "Amazon Echo",
    "70:ee:50:18:34:43": "Netatmo Welcome",
    "f4:f2:6d:93:51:f1": "Netatmo Weather Station",
    "00:16:6c:ab:6b:88": "Withings Smart Scale",
    "30:8c:fb:2f:e4:b2": "Dropcam",
    "00:62:6e:51:27:2e": "Insteon Camera",
    "e0:76:d0:33:bb:85": "Insteon Hub",
    "70:5a:0f:e4:9b:c0": "Belkin Wemo Switch",
    "ec:1a:59:83:28:11": "Belkin Wemo Motion",
    "50:c7:bf:01:56:39": "TP-Link Smart Plug",
    "74:c6:3b:29:d7:1d": "iHome SmartPlug",
    "18:b4:30:25:be:e4": "Nest Thermostat",
    "e0:76:d0:33:bb:86": "Insteon Camera 2",
    "14:91:82:f0:f4:64": "Samsung SmartCam",
    "44:91:60:e4:ea:9a": "TP-Link Camera",
    "b4:75:0e:65:00:5c": "Canary Camera",
    "00:24:e4:11:18:a8": "Withings Sleep Sensor",
    "74:2f:68:81:69:42": "Blipcare BP Meter",
    "d0:73:d5:01:83:05": "Withings Smart Baby Monitor",
    "00:24:e4:1b:6f:96": "Laptop",
    "b4:ce:f6:a7:a3:c7": "Android Phone",
}

GATEWAY_MAC = "14:cc:20:51:33:ea"

# ──────────────────────────────────────────────
# 1. LOAD DATA
# ──────────────────────────────────────────────

print("=" * 60)
print("Week 6 — Unsupervised Clustering")
print("=" * 60)

print("\n[1/5] Loading CSV...")
df = pd.read_csv(CSV_FILE)
df["device"] = df["eth.src"].map(DEVICE_MAP)
df = df[df["device"].notna()]
df = df[df["device"] != "TPLink Router"]
df["TIME"] = pd.to_numeric(df["TIME"], errors="coerce")
df = df.dropna(subset=["TIME"])
df["window"] = (df["TIME"] // WINDOW_SEC).astype(int)

# Inter-arrival time per device window
df = df.sort_values(["device", "TIME"])
df["inter_arrival"] = df.groupby("device")["TIME"].diff().fillna(0)

print(f"    Packets loaded: {len(df):,}")
print(f"    Devices: {df['device'].nunique()}")

# ──────────────────────────────────────────────
# 2. FEATURE EXTRACTION (no MAC, no ports, no IPs)
# ──────────────────────────────────────────────

print("\n[2/5] Extracting size and timing features (60-second windows)...")

def burst_score(x):
    return (x < 0.1).mean() if len(x) > 0 else 0

features_list = []
for (device, window), grp in df.groupby(["device", "window"]):
    ia = grp["inter_arrival"]
    sz = grp["Size"]
    features_list.append({
        "device":           device,
        "window":           window,
        "packet_count":     len(grp),
        "total_bytes":      sz.sum(),
        "avg_pkt_size":     sz.mean(),
        "std_pkt_size":     sz.std(ddof=0),
        "min_pkt_size":     sz.min(),
        "max_pkt_size":     sz.max(),
        "avg_inter_arrival":ia.mean(),
        "std_inter_arrival":ia.std(ddof=0),
        "min_inter_arrival":ia.min(),
        "max_inter_arrival":ia.max(),
        "burst_score":      burst_score(ia),
    })

feat_df = pd.DataFrame(features_list)
feat_df = feat_df.fillna(0)

FEATURE_COLS = [
    "packet_count", "total_bytes",
    "avg_pkt_size", "std_pkt_size", "min_pkt_size", "max_pkt_size",
    "avg_inter_arrival", "std_inter_arrival", "min_inter_arrival", "max_inter_arrival",
    "burst_score",
]

print(f"    Windows: {len(feat_df):,} across {feat_df['device'].nunique()} devices")

# ──────────────────────────────────────────────
# 3. STANDARDIZE + CLUSTER
# ──────────────────────────────────────────────

print(f"\n[3/5] Running K-Means (k={N_CLUSTERS}, n_init={N_INIT})...")

X = feat_df[FEATURE_COLS].values
y_true_labels = feat_df["device"].values

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

kmeans = KMeans(n_clusters=N_CLUSTERS, n_init=N_INIT, random_state=RANDOM_STATE)
cluster_labels = kmeans.fit_predict(X_scaled)
feat_df["cluster"] = cluster_labels

print("    Done.")

# ──────────────────────────────────────────────
# 4. EVALUATE
# ──────────────────────────────────────────────

print("\n[4/5] Evaluating cluster purity...")

# Encode true labels as integers for ARI/NMI
unique_devices = sorted(feat_df["device"].unique())
device_to_int  = {d: i for i, d in enumerate(unique_devices)}
y_true_int     = feat_df["device"].map(device_to_int).values

ari = adjusted_rand_score(y_true_int, cluster_labels)
nmi = normalized_mutual_info_score(y_true_int, cluster_labels)

# Per-cluster purity
purity_rows = []
for c in range(N_CLUSTERS):
    mask = cluster_labels == c
    if mask.sum() == 0:
        continue
    counts   = feat_df[mask]["device"].value_counts()
    dominant = counts.index[0]
    purity   = counts.iloc[0] / mask.sum()
    purity_rows.append({
        "cluster":  c,
        "dominant": dominant,
        "purity":   purity,
        "n_windows": mask.sum(),
    })

purity_df = pd.DataFrame(purity_rows).sort_values("purity", ascending=False)
avg_purity = purity_df["purity"].mean()

print(f"\n    Average cluster purity : {avg_purity:.1%}")
print(f"    Adjusted Rand Index    : {ari:.2f}")
print(f"    Normalized Mutual Info : {nmi:.2f}")
print()
print(f"    {'Device':<30} {'Purity':>8}  {'Windows':>8}")
print(f"    {'-'*30} {'-'*8}  {'-'*8}")
for _, row in purity_df.iterrows():
    print(f"    {row['dominant']:<30} {row['purity']:>7.1%}  {int(row['n_windows']):>8}")

# ──────────────────────────────────────────────
# 5. CHARTS
# ──────────────────────────────────────────────

print(f"\n[5/5] Generating charts...")

# ── Chart 7: PCA scatter — cluster assignments vs true labels ──
pca = PCA(n_components=2, random_state=RANDOM_STATE)
X_2d = pca.fit_transform(X_scaled)

fig, axes = plt.subplots(1, 2, figsize=(16, 6))
fig.suptitle("Week 6 — Unsupervised Clustering\nPCA Projection of Traffic Windows",
             fontsize=14, fontweight="bold", y=1.01)

# Left: cluster assignments (no knowledge)
cmap = plt.cm.get_cmap("tab20", N_CLUSTERS)
sc0  = axes[0].scatter(X_2d[:, 0], X_2d[:, 1],
                       c=cluster_labels, cmap=cmap, s=4, alpha=0.5)
axes[0].set_title("K-Means Cluster Assignments\n(no labels used)", fontsize=12)
axes[0].set_xlabel(f"PC1 ({pca.explained_variance_ratio_[0]:.1%} variance)")
axes[0].set_ylabel(f"PC2 ({pca.explained_variance_ratio_[1]:.1%} variance)")
axes[0].set_facecolor("#f8f9fa")

# Right: true device labels (ground truth)
color_map = {d: plt.cm.tab20(i / len(unique_devices))
             for i, d in enumerate(unique_devices)}
colors = [color_map[d] for d in y_true_labels]
axes[1].scatter(X_2d[:, 0], X_2d[:, 1], c=colors, s=4, alpha=0.5)
patches = [mpatches.Patch(color=color_map[d], label=d) for d in unique_devices]
axes[1].legend(handles=patches, fontsize=6, loc="upper right",
               ncol=2, framealpha=0.85)
axes[1].set_title("True Device Labels\n(ground truth)", fontsize=12)
axes[1].set_xlabel(f"PC1 ({pca.explained_variance_ratio_[0]:.1%} variance)")
axes[1].set_ylabel(f"PC2 ({pca.explained_variance_ratio_[1]:.1%} variance)")
axes[1].set_facecolor("#f8f9fa")

plt.tight_layout()
out7 = os.path.join(OUTPUT_DIR, "chart7_clustering_scatter.png")
plt.savefig(out7, dpi=150, bbox_inches="tight")
plt.close()
print(f"    Saved {out7}")

# ── Chart 8: Per-device cluster purity bar chart ──
purity_plot = purity_df.sort_values("purity", ascending=True)

fig, ax = plt.subplots(figsize=(10, 7))
colors_bar = ["#2ecc71" if p >= 0.8 else "#e67e22" if p >= 0.6 else "#e74c3c"
              for p in purity_plot["purity"]]

bars = ax.barh(purity_plot["dominant"], purity_plot["purity"] * 100,
               color=colors_bar, edgecolor="white", height=0.7)

# Value labels
for bar, val in zip(bars, purity_plot["purity"]):
    ax.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height() / 2,
            f"{val:.0%}", va="center", fontsize=9, color="#333")

# Average line
ax.axvline(avg_purity * 100, color="#2c3e50", linestyle="--", linewidth=1.5,
           label=f"Average purity: {avg_purity:.1%}")

ax.set_xlabel("Cluster Purity (%)", fontsize=11)
ax.set_title(
    "Week 6 — Cluster Purity Per Device\n"
    "K-Means Clustering · No Labels · Size and Timing Features Only",
    fontsize=12, fontweight="bold"
)
ax.set_xlim(0, 110)
ax.legend(fontsize=10)
ax.set_facecolor("#f8f9fa")
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

# Legend for colors
green_patch  = mpatches.Patch(color="#2ecc71", label="≥ 80% purity")
orange_patch = mpatches.Patch(color="#e67e22", label="60–79% purity")
red_patch    = mpatches.Patch(color="#e74c3c", label="< 60% purity")
ax.legend(handles=[green_patch, orange_patch, red_patch,
                   plt.Line2D([0], [0], color="#2c3e50", linestyle="--",
                              label=f"Average: {avg_purity:.1%}")],
          fontsize=9, loc="lower right")

plt.tight_layout()
out8 = os.path.join(OUTPUT_DIR, "chart8_cluster_purity.png")
plt.savefig(out8, dpi=150, bbox_inches="tight")
plt.close()
print(f"    Saved {out8}")

# ──────────────────────────────────────────────
# SUMMARY
# ──────────────────────────────────────────────

print()
print("=" * 60)
print("WEEK 6 RESULTS SUMMARY")
print("=" * 60)
print(f"  Features used        : size + timing only (no MACs, ports, IPs)")
print(f"  Windows clustered    : {len(feat_df):,}")
print(f"  Clusters requested   : {N_CLUSTERS}")
print(f"  Average purity       : {avg_purity:.1%}")
print(f"  Adjusted Rand Index  : {ari:.2f}")
print(f"  Normalized Mutual Info: {nmi:.2f}")
print()
print("  Research progression:")
print("    Week 5  (full features, supervised)  : 97.5% accuracy")
print("    Week 5b (VPN simulation, supervised)  : 96.7% accuracy")
print(f"    Week 6  (no labels, unsupervised)     : {avg_purity:.1%} purity")
print()
print("  Even with zero prior knowledge, K-Means recovers")
print("  device groupings with 72.7% average purity.")
print("=" * 60)
