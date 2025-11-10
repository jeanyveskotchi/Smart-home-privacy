# Week 1 summary

For the first week I installed the Raspberry pi 5 (8GB RAM). The Raspberry Pi 5 is a small, single-board computer that runs a full Linux-based operating system (Raspberry Pi OS) and can perform many of the same tasks as a desktop computer like coding, data collection, machine learning, and networking.
I  mounted the pc and plugged it to a monitor, I added a mouse and a keyboard
Performed a full system update:







Then I Installed essential packages for networking and scripting:
 git, python3-pip, tcpdump, nmap, wireshark.


**Purpose:**
 These tools provide the foundation for data collection (tcpdump), network discovery (nmap), and packet-level inspection (Wireshark), all necessary for privacy-leak analysis.
 finally I identified the active network interface (wlan0) using ifconfig.
Ran a live packet capture:
 sudo tcpdump -i wlan0 -c 50

**Purpose:**
 To confirm that the Pi can observe network activity and collect real-time traffic metadata—proof that it can serve as a network sensor for subsequent ML-based privacy analysis.

