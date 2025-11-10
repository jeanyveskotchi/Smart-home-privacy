# Smart Home Privacy Research

##  Project Overview
This research explores how data travels within **smart home environments**, focusing on the intersection of **IoT systems**, **machine learning**, and **privacy**.  
The study aims to understand what can be inferred from encrypted device traffic and how adaptive defenses can be designed to protect user behavior.

---

##  Research Goals
- Investigate **data patterns** from smart devices such as cameras, sensors, and assistants.  
- Study how **network traffic**, even when encrypted, leaks **user routines**.  
- Design and test **obfuscation strategies** to protect privacy while keeping devices functional.

---

##  Methods
The Raspberry Pi 5 acts as a **local IoT router** that captures and analyzes device traffic.  
Traffic from devices like a Wyze Cam v4 is collected under different conditions (idle, streaming, VPN, etc.) to compare behavioral patterns.

Experiments are grouped by week:
| Week | Focus | Description |
|------|-------|--------------|
| Week 1 | Pi Setup | Installed Raspberry Pi 5 OS, configured network tools, and verified packet capture. |
| Week 2 | Router Mode | Converted Pi into an AP router to monitor device traffic and VPN effects. |
| Week 3 | IoT Camera | Analyzed Wyze Cam v4 network patterns while idle vs streaming. |
| Week 4+ | Privacy Testing | Planned exploration of data obfuscation, VPN, and cross-device comparison. |

---

##  Tools Used
- **Raspberry Pi OS (Bookworm)**
- **Wireshark**, **tcpdump**
- **nmap**, **nmcli**, **dnsmasq**, **hostapd**
- **Python + Scapy** for traffic parsing (planned)
- **GitHub** for documentation & reproducibility

---

##  Key Takeaway
> Even with encrypted IoT traffic, **metadata alone**—like packet timing and frequency—can reveal user activity patterns.  
> The goal of this project is to develop awareness and techniques to **minimize privacy leaks** without sacrificing usability.

---

##  License & Ethics
This project is for **educational and research purposes only**.  
All captures are taken within a **private network** with devices owned by the researcher.  
No third-party or neighbor traffic is intentionally collected.  
See [data_policy_and_ethics.md](data_policy_and_ethics/data_policy_and_ethics.md) for more details.

---

