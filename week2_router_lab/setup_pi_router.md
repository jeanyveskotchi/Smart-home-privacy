# NAT / AP config steps

# 1 – Starting Point: Wireless-Only Setup

I began this project using the Raspberry Pi 5’s built-in Wi-Fi (wlan0) as my only network interface.
Initially the goal was simple: monitor and capture wireless packets on my home network to understand how much traffic information is visible even when encryption is used.
However, because I live in an apartment complex where the Wi-Fi is shared, the Pi could only capture its own encrypted packets.
I couldn’t observe my phone’s or smart-device traffic directly, which limited what I could analyze.

# 2 – Attempt #1: Adding a USB Wi-Fi Adapter

To separate network roles—one interface for Internet access and one for my own lab network—I added an ASUS USB-AX56 Nano adapter.
The idea was to make the Pi act as a small router / access point:

The USB adapter would connect to the apartment’s Wi-Fi (upstream).

The built-in adapter would broadcast my own SSID so my phone could connect through the Pi.

This setup would let me route and inspect all phone traffic locally.

# 3 – Challenge: Driver Support

The ASUS adapter uses a Realtek RTL8832AU chipset.
Raspberry Pi OS didn’t include a native driver, so I tried multiple community drivers (8821au-20210708, rtl8852au, etc.).
Most compiled successfully but failed to load the device; no new wlan1 interface appeared after reboot.
Because of kernel and chipset mismatches, the adapter was detected over USB but couldn’t operate as a network card.

After several attempts (and some very long reboots ), I decided to postpone wireless routing until I could find a fully supported adapter.

# 4 – Attempt #2: Switch to Ethernet for Stability

To keep progressing, I connected the Pi directly to my apartment’s wall LAN port with a long Cat 6 Ethernet cable.
This solved two problems at once:

Stable Internet uplink: eth0 came UP immediately and obtained an IP address.

Reliable packet capture: no Wi-Fi interference or dropped frames.

With Ethernet as the uplink, the Pi can now use its internal Wi-Fi purely as a controlled access point (PiTestNet) for my phone and IoT devices.
This architecture is also ideal for Week 2 experiments comparing VPN vs non-VPN traffic, because it isolates all test traffic within my own mini-network.
