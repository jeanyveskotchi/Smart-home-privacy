# Week 5 — UNSW IoT Dataset Analysis

## Objective

Validate the behavioral leakage findings from Weeks 3 & 4 (Wyze Cam) against an **independent, external dataset** from UNSW Sydney's IoT Analytics Research Group.  
The goal is to show that traffic metadata alone can identify devices and infer behavioral states — across 21 different IoT devices, not just the Wyze Cam.

---

## Dataset Used

| Field | Detail |
|---|---|
| **Source** | [UNSW IoT Analytics — Traffic Traces (IEEE TMC 2018)](https://iotanalytics.unsw.edu.au/iottraces.html) |
| **Day analyzed** | 22 September 2016 (`16-09-23.csv`) |
| **File type** | CSV (pre-processed packet metadata) |
| **Total packets** | 802,581 raw · 428,782 after filtering to labeled IoT devices |
| **Time range** | 2016-09-22 14:00:02 → 2016-09-23 13:59:59 (full 24 hours) |
| **Devices** | 21 labeled IoT devices |

### CSV Columns

| Column | Description |
|---|---|
| `Packet ID` | Sequential packet number |
| `TIME` | Unix timestamp |
| `Size` | Packet size in bytes |
| `eth.src` | Source MAC address |
| `eth.dst` | Destination MAC address |
| `IP.src` | Source IP |
| `IP.dst` | Destination IP |
| `IP.proto` | Protocol (6 = TCP, 17 = UDP) |
| `port.src` | Source port |
| `port.dst` | Destination port |

### Devices in Dataset

Devices were labeled by cross-referencing `eth.src` MAC addresses against `List_Of_Devices.txt` provided by UNSW.  
The gateway (`14:cc:20:51:33:ea`) was excluded from analysis.

---

## Files

```
week5_unsw_dataset/
├── README.md                        ← this file
├── scripts/
│   └── unsw_pipeline_viz.py         ← full analysis pipeline
├── data/
│   └── List_of_Devices.txt          ← MAC → device name mapping
└── Screenshots/
    ├── chart1_idle_vs_active.png    ← idle vs active packets per device
    ├── chart2_classifier_accuracy.png ← RF classifier F1-score per device
    ├── chart3_camera_timeline.png   ← 24h traffic timeline (camera devices)
    └── chart4_cross_dataset.png     ← Wyze Cam vs UNSW cameras comparison
```

> **Note:** `16-09-23.csv` (78 MB) is not committed to the repo.  
> Download it from the UNSW TMC 2018 dataset page and place it in the same folder as the script before running.

---

## Method

### 1. Device Labeling
Each packet's `eth.src` MAC was mapped to a device name using `List_Of_Devices.txt`.  
The TPLink Router/Gateway was excluded as it forwards all traffic and is not an IoT endpoint.

### 2. Feature Extraction (60-second windows)
Rather than inspecting individual packets, traffic was grouped into **60-second time windows** per device.  
17 behavioral features were extracted per window:

| Feature | What it captures |
|---|---|
| `packet_count` | Volume of activity |
| `total_bytes` | Data transferred |
| `avg/std/min/max_pkt_size` | Packet size distribution |
| `avg/std/min/max_inter_arrival` | Timing between packets |
| `tcp_ratio` / `udp_ratio` | Protocol mix |
| `unique_dst_ips` / `unique_dst_ports` | Communication breadth |
| `port_443_ratio` / `port_80_ratio` | Encrypted vs plain traffic |
| `burst_score` | Fraction of packets arriving < 100ms apart |

This mirrors the manual timing analysis done in **Week 4** using Wireshark's `frame.time_delta_displayed`, but automated and applied across all 21 devices.

### 3. Behavioral State Detection (Idle vs Active)
Each window was labeled **active** if its `packet_count` exceeded the device's median, and **idle** otherwise.  
This is a per-device relative threshold — it accounts for the fact that a Dropcam's "idle" looks very different from a smart plug's "idle."

### 4. Device Classification (Random Forest)
A Random Forest classifier (100 trees) was trained on the 17 features to identify which device produced each 60-second window.  
Only devices with ≥ 5 windows were included (18 devices).  
80/20 train/test split with stratification.

---

## Results

### Device Identification
- **Overall accuracy: 98%**
- 13 out of 18 devices achieved F1-score ≥ 0.95
- Most important features: `min_pkt_size`, `max_pkt_size`, `total_bytes`, `port_443_ratio`

> Even though all traffic is encrypted (TLS/HTTPS), packet size and timing metadata alone is enough to identify the device with 98% accuracy.

### Idle vs Active Detection
All devices show a measurable difference between idle and active windows.  
Notable examples:

| Device | Idle avg pkts/window | Active avg pkts/window | Ratio |
|---|---|---|---|
| Netatmo Welcome | 3.0 | 19.3 | 6.4x |
| TP-Link Camera | 2.0 | 14.1 | 7.1x |
| Dropcam | 55.4 | 110.5 | 2.0x |
| Samsung SmartCam | 22.3 | 46.5 | 2.1x |

### Cross-Dataset Comparison (Chart 4)

| Camera | Active/Idle packet ratio |
|---|---|
| **Wyze Cam v4 (Week 3, own capture)** | **~8.6x** |
| Netatmo Welcome (UNSW) | 6.4x |
| TP-Link Camera (UNSW) | 7.1x |
| Dropcam (UNSW) | 2.0x |
| Samsung SmartCam (UNSW) | 2.1x |

**Finding:** The behavioral leakage pattern generalizes — all cameras show a significant spike in traffic when active. However, the ratio is vendor-specific, which means a universal threshold detector would underperform. Per-device models are more appropriate.

---

## How to Run

```bash
# 1. Install dependencies
pip install pandas scikit-learn numpy matplotlib

# 2. Place 16-09-23.csv in the same folder as the script

# 3. Run
python scripts/unsw_pipeline_viz.py
```

Charts will be saved as PNGs in the working directory.

---

## Connection to Previous Weeks

| Week | Device | Method | Finding |
|---|---|---|---|
| Week 3 | Wyze Cam v4 | Wireshark manual | 9x packet increase idle→streaming |
| Week 4 | Wyze Cam v4 | Time-delta analysis | Timing alone reveals streaming state |
| **Week 5** | **21 UNSW devices** | **Automated pipeline + RF** | **98% device ID, behavioral leakage generalizes** |
