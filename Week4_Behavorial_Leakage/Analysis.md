## 1. Overview

Even though Wyze Cam traffic is fully encrypted (TLS/HTTPS), its timing patterns still leak information.
In Week 4, we re-used Week 3 captures and applied fine-grained time-delta analysis to see if we can detect:

When the camera is idle

When it is streaming

Whether internal tasks (or motion events) leave detectable timing fingerprints

## 2. Methodology
Wireshark Settings Used
Setting	Value
Device IP	10.42.0.37 (Wyze Cam v4)
Display Filter	ip.addr == 10.42.0.37
Interval	10 ms
Y-Axis	Bytes
Y-Axis Field	frame.time_delta_displayed
Graph Style	Line
Data Source	Week 3 PCAPs (idle + streaming)

The key idea is:
frame.time_delta_displayed measures time between packets → ideal for detecting abnormal burst patterns.

## 3. Visual Results & Interpretation
### 3.1 Streaming Timing Pattern

File: Screenshots/week4g1.png


What We See

A strong repeating waveform, representing continuous video frame uploads.

Packet bursts occur at nearly regular spacing (~frame intervals).

A huge spike around 52–53 s, indicating:

TLS renegotiation or

a video keyframe refresh.

Interpretation
Observation	What It Means
Regular wave pattern	Continuous live video streaming
High bandwidth	Video frame chunks sent to Wyze cloud
Spikes	Session refresh, keep-alive rollover, or keyframe transmission
Conclusion

Even when encrypted, streaming is easily identifiable from timing alone.

### 3.2 Idle Pattern (Zoomed Out)

File: Screenshots/week4g2.png


What We See

Very low baseline traffic.

Occasional small peaks between 30–32 s.

No repeating structure.

Interpretation
Observation	Meaning
Lightweight, random peaks	Heartbeat packets, DNS checks, cloud pings
No regular periodic pattern	Camera is not streaming
Small bursts only	Internal synchronization events
Conclusion

Idle mode produces irregular bursts, not sustained activity.
This forms the baseline for detecting abnormal behavior.

### 3.3 Idle Pattern (Zoomed In on Spike)

File: Screenshots/week4g3.png


What We See

A single tall spike around 53 s.

Smaller micro-peaks before and after it.

Interpretation
Observation	Meaning
One tall spike	Cloud re-sync or internal status update
Surrounding micro-bursts	Metadata transfer, SSL keep-alive, ACK chains
No cluster of spikes	→ Not motion or sound-triggered behavior
Conclusion

The camera still “wakes up” during idle → these background events create timing fingerprints.

## 4. Behavioral Leakage Findings

This is the core of Week 4 — what can an external observer infer?
| Leakage Type |  Evidence | Meaning |
|---|---|---|
Streaming detection|	Wave pattern visible|	Observer knows when live video is being viewed
Session refresh timing|	Large spike during stream	|Observer can estimate viewing session length
Idle periodic tasks|	Isolated spikes|	Time-sync, cloud beacons, internal tasks
Potential motion detection (future)|	Would show micro-burst clusters|	Can reveal activity inside the home

## **Key Insight**

Even with TLS encryption, timing metadata alone leaks private behavioral information.

Someone monitoring your network cannot see the video, but they can infer:

When you're home

When you’re watching the camera

When the camera detects something

When the camera re-connects or wakes up

This is real-world IoT privacy leakage.
