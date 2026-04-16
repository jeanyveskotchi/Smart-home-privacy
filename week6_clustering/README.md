# Week 6 — Unsupervised Clustering: Can Devices Be Found Without Labels?

## The Question

Weeks 5 and 5b proved that a **supervised** classifier — one that already knows which MAC address belongs to which device — can identify IoT devices from traffic metadata with up to 97.5% accuracy, even through a VPN.

But supervised learning requires an attacker who has already mapped MAC addresses to devices. What about a completely external observer — one who sees only encrypted traffic coming out of a router, with no knowledge of which device sent what?

> *Can an algorithm discover device groupings on its own, with zero prior knowledge?*

That is the question Week 6 answers using **unsupervised clustering**.

---

## The Threat Model: External Observer Behind a Router VPN

```
[Smart Home Devices]
        |
        |  (MAC addresses hidden here)
        ↓
[Home Router / VPN Gateway]
        |
        |  ← attacker observes HERE
        ↓
[Internet / ISP]
```

In this scenario, the attacker sees:
- Packet sizes
- Packet timing and inter-arrival gaps
- Aggregate burst patterns

The attacker does **not** see:
- Which device sent which packet (no MACs)
- Destination IPs (VPN hides them)
- Ports or protocols (VPN hides them)

This is the hardest possible version of the attack.

---

## What Clustering Is

Classification (Week 5) is like a teacher grading papers with an answer key — you tell the model "this traffic = Amazon Echo" and it learns from that.

Clustering is the opposite. You throw all the data at the algorithm and say: **"find groups that naturally belong together"** — with no labels, no answer key, no prior knowledge.

An everyday analogy: imagine walking into a cafeteria with no roster. You notice:
- Some people in lab coats talking about experiments
- Some people in suits talking about money
- Some people in jerseys talking about sports

You figured out there are 3 groups — scientists, businesspeople, athletes — purely by observing *behavioral similarity*. Clustering does this mathematically.

---

## Method

### Step 1: Strip All Identity Information

All 428,782 packets from the UNSW dataset were loaded as if they came from a single anonymous router. MAC addresses were removed entirely.

### Step 2: Extract Size and Timing Features Only

Traffic was grouped into **60-second windows**. For each window, 11 features were extracted — the same features that survive a VPN (see Week 5b):

| Feature | What It Captures |
|---|---|
| `packet_count` | How active the device was |
| `total_bytes` | Total data volume |
| `avg_pkt_size` | Typical packet size |
| `std_pkt_size` | Variation in size |
| `min_pkt_size` / `max_pkt_size` | Size extremes |
| `avg_inter_arrival` | Average gap between packets |
| `std_inter_arrival` | Variation in timing |
| `min_inter_arrival` / `max_inter_arrival` | Timing extremes |
| `burst_score` | Fraction of packets < 100ms apart |

No ports, no IPs, no MACs — just size and timing.

### Step 3: K-Means Clustering

The K-Means algorithm was given the feature matrix and told to find **21 groups** (matching the number of real devices in the dataset). It finds cluster centers by minimizing within-cluster variance — without ever being told what the groups represent.

Features were standardized (zero mean, unit variance) before clustering so that `total_bytes` doesn't dominate over `burst_score`.

### Step 4: Evaluate Against Ground Truth

After clustering, the real device labels were brought back in to evaluate: did each cluster correspond to a single actual device?

**Cluster purity** measures this:

```
purity = (most common true label in cluster) / (total windows in cluster)
```

A cluster with 95% Dropcam windows and 5% mixed = 95% purity. Perfect = 100%.

---

## Results

### Overall Performance

| Metric | Value |
|---|---|
| Clusters found | 21 |
| Average cluster purity | **72.7%** |
| Adjusted Rand Index (ARI) | 0.68 |
| Normalized Mutual Info (NMI) | 0.81 |

### Per-Device Purity

| Device | Cluster Purity |
|---|---|
| Laptop | **100%** |
| Netatmo Weather Station | **97%** |
| Samsung SmartCam | **96%** |
| Amazon Echo | **91%** |
| TP-Link Camera | **88%** |
| Belkin Wemo Motion | **85%** |
| Dropcam | 54% |
| Netatmo Welcome | 51% |
| *Others (average)* | ~70% |

**High purity devices** have a distinctive, consistent traffic signature — the laptop sends large bursts, the weather station sends tiny, infrequent packets, the Samsung camera has a unique size profile.

**Low purity devices** (Dropcam, Netatmo Welcome) are visually similar — both are cameras with comparable packet sizes and timing patterns. Without MAC addresses or port information, even a human analyst would struggle to separate them.

---

## The Full Research Story: Three Scenarios, Three Numbers

| Scenario | Method | Accuracy |
|---|---|---|
| **Week 5** — Local observer, full features (MAC, ports, IPs visible) | Random Forest (supervised) | **97.5%** |
| **Week 5b** — VPN hides ports and IPs, MAC still visible | Random Forest (supervised, VPN features removed) | **96.7%** |
| **Week 6** — Router VPN, no MACs, no ports, no IPs | K-Means Clustering (unsupervised) | **72.7%** |

The threat exists at every level of the attacker's position. The easier the access, the closer to 100%. Even in the hardest case — zero prior knowledge, zero labels — 3 in 4 traffic windows are correctly grouped.

---

## Files

```
week6_clustering/
├── README.md                               ← this file
├── ML_Algorithm_Analysis.md               ← why K-Means, how it works, what it found
├── scripts/
│   └── week6_clustering.py                ← full clustering pipeline
└── Screenshots/
    ├── chart7_clustering_scatter.png      ← PCA scatter plot of clusters vs true labels
    └── chart8_cluster_purity.png          ← bar chart of per-device cluster purity
```

> **Note:** `16-09-23.csv` (78 MB) is not committed. Download from the UNSW IoT Analytics dataset page and place in the same directory as the script.

---

## Connection to Broader Research

| Week | Method | Scope | Key Finding |
|---|---|---|---|
| Week 3 | Wireshark manual inspection | 1 device | Idle vs streaming visually distinguishable |
| Week 4 | Time-delta fingerprinting | 1 device | Timing alone reveals behavioral state |
| Week 5 | Random Forest | 21 devices | 97.5% accuracy from metadata alone |
| Week 5b | Random Forest (VPN sim) | 21 devices | VPN drops accuracy only 0.8% |
| **Week 6** | **K-Means Clustering** | **21 devices** | **72.7% purity with zero prior knowledge** |

The progression from manual observation → supervised classification → unsupervised discovery demonstrates that the privacy threat is not dependent on any particular attacker capability. It exists at every level.
