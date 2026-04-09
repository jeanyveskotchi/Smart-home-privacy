"""
Week 5b — VPN Simulation: Device Identification Under VPN Conditions
Smart Home Privacy Research - Jean-Yves Kotchi

Simulates what an attacker sees when the user is on a VPN:
- Port numbers are hidden (all traffic tunneled through VPN port)
- Destination IPs are hidden (only VPN server IP is visible)
- Only packet size and timing metadata remain

Compares classifier accuracy: Full features (98%) vs VPN-only features
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

# ── Features available with and without VPN ────────────────────────────────────

# Full feature set (Week 5 baseline)
FULL_FEATURES = [
    "packet_count", "total_bytes",
    "avg_pkt_size", "std_pkt_size", "max_pkt_size", "min_pkt_size",
    "avg_inter_arrival", "std_inter_arrival", "min_inter_arrival", "max_inter_arrival",
    "tcp_ratio", "udp_ratio",
    "unique_dst_ips", "unique_dst_ports",
    "port_443_ratio", "port_80_ratio",
    "burst_score",
]

# VPN feature set — port and IP features removed
# Under VPN: all traffic goes to one IP (the VPN server)
# and one port (e.g. 1194 for OpenVPN, 51820 for WireGuard)
# so unique_dst_ips, unique_dst_ports, port_443_ratio, port_80_ratio,
# tcp_ratio, udp_ratio all become meaningless or invisible
VPN_FEATURES = [
    "packet_count", "total_bytes",
    "avg_pkt_size", "std_pkt_size", "max_pkt_size", "min_pkt_size",
    "avg_inter_arrival", "std_inter_arrival", "min_inter_arrival", "max_inter_arrival",
    "burst_score",
]

REMOVED_FEATURES = [f for f in FULL_FEATURES if f not in VPN_FEATURES]

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

# ══════════════════════════════════════════════════════════════════════════════
# STEP 3 — Train & compare: Full vs VPN
# ══════════════════════════════════════════════════════════════════════════════
print("Training classifiers...")

min_windows = 5
valid = features_df.groupby("device").size()
valid = valid[valid >= min_windows].index
clf_df = features_df[features_df["device"].isin(valid)].copy()

le = LabelEncoder()
clf_df["label"] = le.fit_transform(clf_df["device"])
y = clf_df["label"].values

results = {}

for name, feature_cols in [("Full (no VPN)", FULL_FEATURES),
                             ("VPN simulation", VPN_FEATURES)]:
    X = clf_df[feature_cols].values
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y)

    rf = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
    rf.fit(X_train, y_train)
    y_pred = rf.predict(X_test)

    report = classification_report(y_test, y_pred,
                                    target_names=le.classes_,
                                    output_dict=True)
    results[name] = {
        "accuracy": report["accuracy"],
        "report":   report,
        "f1_scores": {k: v["f1-score"] for k, v in report.items()
                      if k in le.classes_},
        "importances": dict(zip(feature_cols, rf.feature_importances_))
    }
    print(f"  {name}: accuracy = {report['accuracy']:.3f}")

print()
print(f"  Features removed under VPN: {REMOVED_FEATURES}")
print(f"  Features remaining:         {VPN_FEATURES}")

# ══════════════════════════════════════════════════════════════════════════════
# CHART 1 — F1-score comparison per device: Full vs VPN
# ══════════════════════════════════════════════════════════════════════════════
print("\nGenerating Chart 1: Per-device F1 comparison...")

devices    = le.classes_
full_f1    = [results["Full (no VPN)"]["f1_scores"].get(d, 0) for d in devices]
vpn_f1     = [results["VPN simulation"]["f1_scores"].get(d, 0) for d in devices]
sort_idx   = np.argsort(full_f1)
devices_s  = [devices[i] for i in sort_idx]
full_f1_s  = [full_f1[i] for i in sort_idx]
vpn_f1_s   = [vpn_f1[i]  for i in sort_idx]

fig, ax = plt.subplots(figsize=(10, 7))
y_pos = np.arange(len(devices_s))
h = 0.35

ax.barh(y_pos + h/2, full_f1_s, h, color=BLUE,   label="Full features (no VPN)")
ax.barh(y_pos - h/2, vpn_f1_s,  h, color=ORANGE, label="VPN simulation (size + timing only)")

ax.set_yticks(y_pos)
ax.set_yticklabels(devices_s, fontsize=9)
ax.set_xlabel("F1-score")
ax.set_xlim(0, 1.12)
ax.axvline(1.0, color="gray", linestyle="--", linewidth=0.8, alpha=0.5)
ax.set_title(
    f"Chart 1 — Device identification: Full features vs VPN simulation\n"
    f"Full accuracy: {results['Full (no VPN)']['accuracy']:.1%}  →  "
    f"VPN accuracy: {results['VPN simulation']['accuracy']:.1%}",
    fontsize=11, fontweight="bold"
)
ax.legend(fontsize=9)

for i, (fv, vv) in enumerate(zip(full_f1_s, vpn_f1_s)):
    drop = fv - vv
    if drop > 0.05:
        ax.annotate(f"−{drop:.2f}", xy=(max(fv, vv) + 0.01, i),
                    va="center", fontsize=7, color=RED)

plt.tight_layout()
plt.savefig("chart5_vpn_f1_comparison.png", dpi=150)
plt.close()
print("  Saved: chart5_vpn_f1_comparison.png")

# ══════════════════════════════════════════════════════════════════════════════
# CHART 2 — Overall accuracy drop + feature importance under VPN
# ══════════════════════════════════════════════════════════════════════════════
print("Generating Chart 2: Accuracy summary + VPN feature importance...")

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

# Left: overall accuracy bar
scenarios  = ["Full features\n(no VPN)", "VPN simulation\n(size + timing only)"]
accuracies = [results["Full (no VPN)"]["accuracy"],
              results["VPN simulation"]["accuracy"]]
colors     = [BLUE, ORANGE]
bars = ax1.bar(scenarios, accuracies, color=colors, width=0.4, edgecolor="white")
for bar, val in zip(bars, accuracies):
    ax1.text(bar.get_x() + bar.get_width()/2, val + 0.005,
             f"{val:.1%}", ha="center", fontsize=12, fontweight="bold")
ax1.set_ylim(0, 1.1)
ax1.set_ylabel("Overall accuracy")
ax1.set_title("Overall classifier accuracy\nFull vs VPN simulation", fontweight="bold")
ax1.axhline(1.0, color="gray", linestyle="--", linewidth=0.8, alpha=0.4)

# Right: feature importance under VPN
vpn_imp = pd.Series(results["VPN simulation"]["importances"]).sort_values(ascending=True)
colors_imp = [GREEN if v >= 0.10 else BLUE for v in vpn_imp.values]
ax2.barh(vpn_imp.index, vpn_imp.values, color=colors_imp)
ax2.set_xlabel("Importance")
ax2.set_title("Feature importance under VPN\n(port/IP features removed)", fontweight="bold")
for i, (feat, val) in enumerate(zip(vpn_imp.index, vpn_imp.values)):
    ax2.text(val + 0.002, i, f"{val:.3f}", va="center", fontsize=8)

plt.suptitle("Chart 2 — VPN impact on device identification",
             fontsize=11, fontweight="bold", y=1.02)
plt.tight_layout()
plt.savefig("chart6_vpn_accuracy_summary.png", dpi=150)
plt.close()
print("  Saved: chart6_vpn_accuracy_summary.png")

# ══════════════════════════════════════════════════════════════════════════════
# Print summary
# ══════════════════════════════════════════════════════════════════════════════
full_acc = results["Full (no VPN)"]["accuracy"]
vpn_acc  = results["VPN simulation"]["accuracy"]
drop     = full_acc - vpn_acc

print()
print("=" * 60)
print("SUMMARY")
print("=" * 60)
print(f"Full features accuracy : {full_acc:.1%}  (17 features)")
print(f"VPN simulation accuracy: {vpn_acc:.1%}  (11 features)")
print(f"Accuracy drop          : {drop:.1%}")
print()
print("Features removed (hidden by VPN):")
for f in REMOVED_FEATURES:
    print(f"  - {f}")
print()
print("Top surviving features under VPN:")
vpn_imp_sorted = pd.Series(results["VPN simulation"]["importances"]).sort_values(ascending=False)
for feat, imp in vpn_imp_sorted.head(5).items():
    print(f"  {feat:<25} {imp:.3f}")
print()
print("Charts saved:")
print("  chart5_vpn_f1_comparison.png")
print("  chart6_vpn_accuracy_summary.png")
