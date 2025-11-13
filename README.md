# Waybar Tailscale Module

A compact Waybar custom module for managing Tailscale VPN connections directly from your status bar.


## Disclaimer

This project is an independent tool for managing Tailscale connections and is not affiliated with, endorsed by, or sponsored by Tailscale Inc. Tailscale is a registered trademark of Tailscale Inc.

This tool simply provides a convenient interface for the official Tailscale CLI commands and does not modify or redistribute any Tailscale software.


![Tailscale Module Demo](https://img.shields.io/badge/Status-Active-green) ![Python](https://img.shields.io/badge/Python-3.6+-blue) ![License](https://img.shields.io/badge/License-MIT-yellow)

## Features

- **Visual Status Indicators**: connected,disconnected,paused
- **Tooltips**: Hover to see detailed connection info, IP address, peer count, and available actions
- **Click Actions**:
  - **Left Click**: Toggle connection (connect/disconnect)
  - **Right Click**: Context-sensitive actions (pause when connected, stop when paused)
  - **Middle Click**: Copy current machine Tailscale IP to clipboard

## Screenshots

The module displays in your Waybar as:

<img width="310" height="230" alt="screenshot-2025-11-13_20-09-38" src="https://github.com/user-attachments/assets/ee030c73-a66f-40d0-a38f-196196d200c9" /> <img width="312" height="230" alt="screenshot-2025-11-13_20-12-42" src="https://github.com/user-attachments/assets/cb1e8c63-9962-4f0b-9b1a-a24c9df9ca34" /> <img width="309" height="230" alt="screenshot-2025-11-13_20-13-03" src="https://github.com/user-attachments/assets/0172c0fe-5b49-4040-804e-445b6e1eba64" />






## Prerequisites

- **Waybar** 
- **Tailscale** installed and configured
- **Python 3.6+**
- **Sudo access** for Tailscale commands (see setup below)

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/Zay931/waybar-tailscale-module.git
cd waybar-tailscale-module
```

### 2. Copy the Module Script

```bash

# Copy the module script
cp tailscale_module.py ~/.config/waybar/
chmod +x ~/.config/waybar/tailscale_module.py
```

### 3. Update Your Waybar Configuration

Add the module to your `~/.config/waybar/config.jsonc`:

```jsonc
{
  // Add "custom/tailscale" to your modules array
  "modules-right": [ "network", "battery", "clock", "custom/tailscale"],
  
  // Add the module configuration
   "custom/tailscale": {
    "format": "{}",
    "exec": "python3 ~/.config/waybar/tailscale_module.py --status",
    "return-type": "json",
    "interval": 10,
    "tooltip": true,
    "on-click": "python3 ~/.config/waybar/tailscale_module.py --click left",
    "on-click-right": "python3 ~/.config/waybar/tailscale_module.py --click right",
    "on-click-middle": "python3 ~/.config/waybar/tailscale_module.py --click middle",
    "on-scroll-up": "python3 ~/.config/waybar/tailscale_module.py --scroll up",
    "on-scroll-down": "python3 ~/.config/waybar/tailscale_module.py --scroll down",
    "escape": true
  }
}
```
You can refer to the **config.jsonc** file example.



### 5. Configure Sudo Access (Recommended)

To avoid password prompts, configure passwordless sudo for Tailscale:

```bash
sudo visudo
```

Add this line (replace `yourusername` with your actual username):
```
yourusername ALL=(ALL) NOPASSWD: /usr/bin/tailscale
```

to get your username run this command:
```bash
whoami
```

### 6. Restart Waybar

```bash
pkill waybar && waybar &
```


## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

