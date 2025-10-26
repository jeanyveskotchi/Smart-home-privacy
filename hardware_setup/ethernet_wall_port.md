# Apartment ethernet wall port notes
To keep progressing, I connected the Pi directly to my apartment’s wall LAN port with a long Cat 6 Ethernet cable. This solved two problems at once:

Stable Internet uplink: eth0 came UP immediately and obtained an IP address.

Reliable packet capture: no Wi-Fi interference or dropped frames.

With Ethernet as the uplink, the Pi can now use its internal Wi-Fi purely as a controlled access point (PiTestNet) for my phone and IoT devices. This architecture is also ideal for Week 2 experiments comparing VPN vs non-VPN traffic, because it isolates all test traffic within my own mini-network.
