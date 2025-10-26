# USB Wi-Fi adapter driver attempts (ASUS USB-AX56 Nano)
To separate network roles—one interface for Internet access and one for my own lab network—I added an ASUS USB-AX56 Nano adapter.
The idea was to make the Pi act as a small router / access point:

The USB adapter would connect to the apartment’s Wi-Fi (upstream).

The built-in adapter would broadcast my own SSID so my phone could connect through the Pi.

This setup would let me route and inspect all phone traffic locally.

#3 – Challenge: Driver Support

The ASUS adapter uses a Realtek RTL8832AU chipset.
Raspberry Pi OS didn’t include a native driver, so I tried multiple community drivers (8821au-20210708, rtl8852au, etc.).
Most compiled successfully but failed to load the device; no new wlan1 interface appeared after reboot.
Because of kernel and chipset mismatches, the adapter was detected over USB but couldn’t operate as a network card.

After several attempts (and some very long reboots ), I decided to postpone wireless routing until I could find a fully supported adapter.
