# Week 6 — ML Algorithm Analysis: Why K-Means Clustering?

## 1. The Shift from Supervised to Unsupervised

In Week 5, a Random Forest classifier was trained on **labeled** data — every training window was tagged with the correct device name. The model learned decision boundaries from those labels and achieved 97.5% accuracy on held-out test windows.

Week 6 introduces a fundamentally different problem. The attacker has no labels. They see a stream of packets from an anonymous router and must discover, on their own, whether any grouping structure exists in the traffic.

This is **unsupervised learning**: finding patterns without being told what the patterns are.

---

## 2. Why K-Means?

### 2.1 It matches the threat model exactly

K-Means requires no labels, no prior knowledge of device types, and no pretrained model. It operates purely on geometric similarity in feature space — asking "which windows look like each other?" rather than "which windows match a known device?". This mirrors an attacker who has only passive packet capture.

### 2.2 It is interpretable

K-Means produces hard cluster assignments — each window belongs to exactly one cluster. The cluster center (centroid) is a real vector in feature space representing the "average" traffic pattern for that group. This makes results easy to inspect and explain.

### 2.3 It is computationally tractable at this scale

With ~7,000 feature windows and 11 features, K-Means converges in seconds. More complex algorithms (DBSCAN, Gaussian Mixture Models, hierarchical clustering) would introduce hyperparameter sensitivity without a clear accuracy benefit at this scale.

### 2.4 It provides a clean baseline

K-Means is the standard baseline for clustering research. Reporting K-Means results establishes a lower bound — future work can compare more sophisticated algorithms against it.

---

## 3. How K-Means Works — Step by Step

### The Intuition

Imagine each traffic window as a point in 11-dimensional space (one dimension per feature). K-Means finds 21 "centers of gravity" such that each point is as close as possible to its assigned center.

### The Algorithm

```
1. Randomly initialize 21 cluster centroids in feature space
2. Assign every window to its nearest centroid (by Euclidean distance)
3. Recompute each centroid as the mean of all windows assigned to it
4. Repeat steps 2–3 until assignments stop changing
```

The algorithm is guaranteed to converge but may find a local minimum. To reduce this risk, it was run 10 times with different random initializations (`n_init=10`) and the best result (lowest inertia) was kept.

### Why Standardization Matters

The 11 features are on very different scales:
- `total_bytes` ranges from 0 to ~500,000
- `burst_score` ranges from 0.0 to 1.0
- `avg_inter_arrival` ranges from 0.001 to 60.0 seconds

Without normalization, `total_bytes` would dominate the Euclidean distance computation and effectively erase all other features. All features were standardized to zero mean and unit variance before clustering.

---

## 4. What It Found

### Cluster-to-Device Mapping

After clustering, the real device labels were restored to evaluate quality. For each of the 21 clusters, the most common true device label was identified:

```
Cluster → Dominant Device → Purity
```

High-purity clusters correspond to devices with a unique traffic signature. Low-purity clusters correspond to devices that look similar in feature space.

### Why Some Devices Are Easy to Separate

| Device | Why It Clusters Well |
|---|---|
| Laptop | Large, bursty packets — distinctly human-driven traffic |
| Netatmo Weather Station | Tiny, infrequent, highly regular packets — sensor reporting pattern |
| Samsung SmartCam | Distinctive packet size range, high inter-arrival variance |
| Amazon Echo | Medium packet sizes, irregular bursts corresponding to voice commands |

### Why Some Devices Merge

| Device | Why It Clusters Poorly |
|---|---|
| Dropcam | Camera with similar packet size and timing profile to Netatmo Welcome |
| Netatmo Welcome | Camera — hard to distinguish from Dropcam on size and timing alone |

Both Dropcam and Netatmo Welcome are cameras. Without port or IP information (which a VPN hides), their traffic patterns overlap significantly in feature space. This is not a failure of the algorithm — it is a true reflection of the limits of the available information.

---

## 5. Evaluation Metrics

### Cluster Purity

```
purity(cluster k) = max_device(count of windows labeled device d in cluster k)
                    ----------------------------------------------------------
                              total windows in cluster k
```

Average purity across all 21 clusters: **72.7%**

### Adjusted Rand Index (ARI)

Measures how well the clustering matches the true labels, corrected for chance. Ranges from -1 (worse than random) to 1 (perfect). Result: **0.68**

A score of 0.68 means the clustering is substantially better than random, with meaningful correspondence to true device groupings.

### Normalized Mutual Information (NMI)

Measures how much information the cluster assignments share with the true labels. Ranges from 0 (none) to 1 (perfect). Result: **0.81**

An NMI of 0.81 is a strong result — it means the algorithm has recovered most of the structure of the true device groupings purely from packet size and timing.

---

## 6. Comparison: Supervised vs Unsupervised

| Property | Random Forest (Week 5) | K-Means (Week 6) |
|---|---|---|
| Requires labels | Yes | No |
| Training data needed | Yes | No |
| Accuracy | 97.5% | 72.7% purity |
| Interpretability | Feature importance scores | Cluster centroids |
| Attacker knowledge needed | MAC → device mapping | None |
| Real-world scenario | Local network observer | External / ISP-level observer |

The 25-point gap between 97.5% and 72.7% represents the "cost" of having no prior knowledge. Even bearing that full cost, the algorithm still recovers 3 in 4 traffic windows to the correct device group.

---

## 7. Implications

The K-Means result closes the loop on the research question:

> *Is device fingerprinting from traffic metadata still possible when an attacker has absolutely no prior knowledge of the network?*

**Yes — with 72.7% average cluster purity and ARI of 0.68.**

An external observer — an ISP, a network adversary, or a passive traffic monitor — can analyze aggregate traffic from a smart home router and discover that distinct device types exist, identify which traffic windows likely belong to the same device, and in some cases determine the device type from the cluster's traffic signature (e.g., a cluster of tiny, regular packets is likely a sensor; a cluster of large, bursty traffic is likely a camera or laptop).

No decryption is needed. No insider access is needed. Only packet sizes and timing are required.
