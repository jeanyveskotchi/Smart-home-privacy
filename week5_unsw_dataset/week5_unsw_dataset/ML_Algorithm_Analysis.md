# Why Random Forest — Algorithm Choice, Methodology & Findings

## 1. The Core Research Question

> *Can an external observer identify smart home devices and infer what they are doing — purely from network traffic metadata, without ever decrypting a single packet?*

This is the question the machine learning component of this research answers.  
The answer, based on the UNSW TMC 2018 dataset (22 September 2016, 21 devices, 802,581 packets), is **yes — with 98% accuracy.**

---

## 2. Why Machine Learning at All?

In Weeks 3 and 4, the idle vs. streaming states of a Wyze Cam v4 were identified **manually** using Wireshark I/O graphs. That works for one device. It does not scale.

The goal of Week 5 was to ask: does this pattern hold across 21 different devices simultaneously, and can it be detected automatically?

Manual Wireshark inspection across 21 devices over 24 hours would produce hundreds of graphs with no consistent way to compare them. Machine learning solves this by reducing each 60-second window of traffic to **17 numbers** and learning which combination of numbers corresponds to which device or behavior.

---

## 3. Why Random Forest Specifically?

Several classifiers were considered. Random Forest was chosen for the following reasons:

### 3.1 It handles mixed feature types well
The 17 features extracted per window include counts (`packet_count`), ratios (`port_443_ratio`, `tcp_ratio`), and timing statistics (`avg_inter_arrival`). These are on very different scales. Random Forest handles this naturally — it makes decisions based on thresholds within each feature, so no normalization is required.

### 3.2 It is robust to noisy features
Not every feature is equally useful. Some windows may have unusual values due to background system activity unrelated to the device's actual behavior. Random Forest builds 100 independent decision trees, each trained on a random subset of features. The final prediction is a majority vote across all 100 trees. This means one noisy or misleading feature cannot dominate the result.

### 3.3 It provides feature importance scores
After training, Random Forest ranks which features contributed most to correct classifications. This is directly useful for this research — it tells us *what* in the traffic is leaking the device identity, not just *that* it is leaking.

### 3.4 It works well on small-to-medium tabular datasets
The extracted feature set has ~16,000 windows across 18 devices. This is well within Random Forest's effective range. Deep learning models would overfit or require far more data for this task.

### 3.5 It is interpretable enough for privacy research
Unlike a neural network, a Random Forest's decisions can be traced back to specific features. When we say "packet size and port 443 ratio identify the Amazon Echo," that is a verifiable, explainable claim — not a black box output.

---

## 4. How It Worked — Step by Step

### Step 1: Labeling
Every packet in `16-09-23.csv` has a source MAC address (`eth.src`).  
`List_Of_Devices.txt` maps each MAC to a device name.  
Example:
```
44:65:0d:56:cc:d3  →  Amazon Echo
30:8c:fb:2f:e4:b2  →  Dropcam
ec:1a:59:83:28:11  →  Belkin Wemo Motion
```
The TPLink Router/Gateway was excluded — it forwards all traffic and is not an IoT endpoint.  
Result: **428,782 packets labeled across 21 devices.**

### Step 2: Feature extraction (60-second windows)
Instead of classifying individual packets, traffic was grouped into **60-second windows** per device.  
For each window, 17 behavioral features were computed:

| Feature | What it measures |
|---|---|
| `packet_count` | How active the device was |
| `total_bytes` | How much data it transferred |
| `avg_pkt_size` | Typical packet size |
| `std_pkt_size` | Variation in packet sizes |
| `min_pkt_size` / `max_pkt_size` | Size extremes |
| `avg_inter_arrival` | Average time gap between packets |
| `std_inter_arrival` | Variation in timing |
| `min_inter_arrival` / `max_inter_arrival` | Timing extremes |
| `tcp_ratio` | Fraction of TCP packets |
| `udp_ratio` | Fraction of UDP packets |
| `unique_dst_ips` | How many different servers it contacted |
| `unique_dst_ports` | How many different ports it used |
| `port_443_ratio` | Fraction of encrypted HTTPS traffic |
| `port_80_ratio` | Fraction of plain HTTP traffic |
| `burst_score` | Fraction of packets arriving < 100ms apart |

None of these features require reading packet contents. They are all metadata.

Result: **16,725 labeled windows, 17 features each.**

### Step 3: Training
- Devices with fewer than 5 windows were excluded (too little data to learn from)
- Remaining: **18 devices, 16,719 windows**
- 80% of windows used for training, 20% held back for testing
- The split was **stratified** — each device is proportionally represented in both sets
- A Random Forest with **100 decision trees** was trained on the training set

### Step 4: Prediction
The 20% test set was passed to the trained model with labels hidden.  
The model predicted which device produced each window based solely on the 17 features.

---

## 5. What It Found

### 5.1 Overall accuracy: 98%

| Device | F1-Score | Notes |
|---|---|---|
| Amazon Echo | 1.00 | Perfect classification |
| Dropcam | 1.00 | Perfect classification |
| Netatmo Welcome | 1.00 | Perfect classification |
| Samsung SmartCam | 1.00 | Perfect classification |
| Smart Things | 1.00 | Perfect classification |
| TP-Link Camera | 1.00 | Perfect classification |
| Withings Baby Monitor | 1.00 | Perfect classification |
| HP Printer | 0.99 | Near-perfect |
| Netatmo Weather | 0.99 | Near-perfect |
| PIX-STAR Photo-frame | 0.98 | Near-perfect |
| TP-Link Smart Plug | 0.97 | Strong |
| Triby Speaker | 0.96 | Strong |
| Laptop | 0.97 | Strong |
| Samsung Galaxy Tab | 0.91 | Good |
| Belkin Wemo Motion | 0.88 | Good |
| Belkin Wemo Switch | 0.86 | Good |
| Android Phone 2 | 0.85 | Good — phone traffic is less consistent |
| iPhone | 0.00 | Only 2 test windows — insufficient data |

### 5.2 What features mattered most

| Rank | Feature | Importance | Interpretation |
|---|---|---|---|
| 1 | `min_pkt_size` | 14.6% | Devices have characteristic smallest packets (ACKs, heartbeats) |
| 2 | `max_pkt_size` | 11.4% | Devices cap their payload size differently |
| 3 | `total_bytes` | 10.4% | Overall bandwidth footprint is device-specific |
| 4 | `port_443_ratio` | 10.3% | Some devices use HTTPS for everything, others mix protocols |
| 5 | `avg_pkt_size` | 8.4% | Average size reflects the device's data transfer style |
| 6 | `std_pkt_size` | 6.8% | Variation in size — video cameras vary a lot, sensors very little |
| 7 | `packet_count` | 6.6% | Activity level is device-specific |
| 8 | `avg_inter_arrival` | 6.1% | How frequently the device communicates |

**Key insight:** The top features are all about packet size and HTTPS usage — not content. This means the *shape* of a device's communication is enough to identify it, even when everything is encrypted.

### 5.3 Idle vs Active detection

Every device shows a measurable behavioral difference between idle and active windows:

| Device | Idle avg pkts/window | Active avg pkts/window | Ratio |
|---|---|---|---|
| TP-Link Camera | 2.0 | 14.1 | **7.1x** |
| Netatmo Welcome | 3.0 | 19.3 | **6.4x** |
| Dropcam | 55.4 | 110.5 | **2.0x** |
| Samsung SmartCam | 22.3 | 46.5 | **2.1x** |
| Amazon Echo | 9.6 | 23.8 | **2.5x** |
| Belkin Wemo Motion | 18.1 | 74.5 | **4.1x** |

This mirrors the Week 3 & 4 findings on the Wyze Cam (8.6x ratio), now validated across 6 additional devices from an independent dataset.

---

## 6. Privacy Implications

The classifier was trained and tested entirely on **metadata** — timestamps, packet sizes, port numbers, and protocol ratios. No packet payloads were accessed. All traffic was encrypted.

This means:

- An observer on the same network (or an ISP) can identify which smart home devices you own just by watching traffic patterns
- They can infer when those devices are active — and therefore when you are home, awake, or using a specific device
- This is possible even when devices use HTTPS/TLS encryption
- The attack requires no specialized hardware — only passive traffic capture, which is what this research replicates with a Raspberry Pi

---

## 7. Connection to the Broader Research

| Week | Method | Scope | Finding |
|---|---|---|---|
| Week 3 | Wireshark manual inspection | 1 device | Idle vs streaming visually distinguishable |
| Week 4 | Time-delta fingerprinting | 1 device | Timing alone reveals behavioral state |
| **Week 5** | **Random Forest on extracted features** | **21 devices, external dataset** | **98% device identification from metadata alone** |

The progression from manual observation (Week 3) to automated, quantified, cross-dataset validation (Week 5) transforms a qualitative finding into a measurable privacy threat.

---

## 8. Limitations

- The UNSW dataset is from 2016 — device firmware and cloud architectures have evolved
- Only one day of traffic was analyzed; behavior may vary across days
- The idle/active threshold used is relative (per-device median) — not ground-truth labeled states
- iPhone had only 2 test windows, making its 0.00 F1-score statistically meaningless
- The model was trained and tested on the same dataset — cross-day or cross-network validation would strengthen the claim further
