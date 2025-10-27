# Router lab plan
## Summary

This experiment demonstrated how VPN encryption conceals both DNS requests and destination details from local observers such as a Raspberry Pi access point.  
Without a VPN, the capture showed visible DNS queries, multiple destination IPs, and readable metadata about visited domains.  
With a VPN enabled, all traffic became encrypted under the ESP protocol, revealing only the VPN server’s IP and general timing patterns.  

These results confirm that a VPN:
- Protects user privacy by hiding browsing behavior from local networks.  
- Redirects all traffic through a single encrypted tunnel.  
- Limits what can be inferred to volume and timing of packets only.  

Overall, this validates the VPN’s role in maintaining confidentiality of user traffic in a smart-home or shared-Wi-Fi context.
