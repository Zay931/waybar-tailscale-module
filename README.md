# Waybar Tailscale Module

A compact Waybar custom module for managing Tailscale VPN connections directly from your status bar.


## Disclaimer

This project is an independent tool for managing Tailscale connections and is not affiliated with, endorsed by, or sponsored by Tailscale Inc. Tailscale is a registered trademark of Tailscale Inc.

This tool simply provides a convenient interface for the official Tailscale CLI commands and does not modify or redistribute any Tailscale software.


![Tailscale Module Demo](https://img.shields.io/badge/Status-Active-green) ![Python](https://img.shields.io/badge/Python-3.6+-blue) ![License](https://img.shields.io/badge/License-MIT-yellow)

## Features

- **Visual Status Indicators**: Green dot (connected), red dot (disconnected), pause emoji (paused)
- **Rich Tooltips**: Hover to see detailed connection info, IP address, peer count, and available actions
- **Click Actions**:
  - **Left Click**: Toggle connection (connect/disconnect)
  - **Right Click**: Context-sensitive actions (pause when connected, stop when paused)
  - **Middle Click**: Refresh status
- **Auto-Resume**: Automatically resumes connection after 5-minute pause
- **Lightweight**: Pure Python with no external dependencies beyond Tailscale CLI

## Screenshots

The module displays in your Waybar as:
- 🟢 TS (Connected)
- 🔴 TS (Disconnected)  
- ⏸️ TS (Paused)

## Prerequisites

- **Waybar** with custom module support
- **Tailscale** installed and configured
- **Python 3.6+**
- **Sudo access** for Tailscale commands (see setup below)

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/waybar-tailscale-module.git
cd waybar-tailscale-module
```

### 2. Copy the Module Script

```bash
# Create waybar config directory if it doesn't exist
mkdir -p ~/.config/waybar

# Copy the module script
cp tailscale_module.py ~/.config/waybar/
chmod +x ~/.config/waybar/tailscale_module.py
```

### 3. Update Your Waybar Configuration

Add the module to your `~/.config/waybar/config.jsonc`:

```jsonc
{
  // Add "custom/tailscale" to your modules array
  "modules-right": ["custom/tailscale", "network", "battery", "clock"],
  
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
    "escape": true
  }
}
```

### 4. Add CSS Styling

Append the contents of `waybar-styles.css` to your `~/.config/waybar/style.css`:

```bash
cat waybar-styles.css >> ~/.config/waybar/style.css
```

### 5. Configure Sudo Access (Recommended)

To avoid password prompts, configure passwordless sudo for Tailscale:

```bash
sudo visudo
```

Add this line (replace `yourusername` with your actual username):
```
yourusername ALL=(ALL) NOPASSWD: /usr/bin/tailscale
```

### 6. Restart Waybar

```bash
pkill waybar && waybar &
```

## Usage

### Status Indicators
- **🟢 TS**: Connected to Tailscale network
- **🔴 TS**: Disconnected from network
- **⏸️ TS**: Paused (will auto-resume in 5 minutes)

### Interactions
- **Hover**: View detailed status, IP address, peer count, and available actions
- **Left Click**: Toggle connection state
- **Right Click**: Context-sensitive action (pause when connected, stop when paused)
- **Middle Click**: Refresh status immediately

### Pause Feature
When you right-click while connected, Tailscale will pause for 5 minutes and automatically resume. The tooltip shows the remaining pause time. You can manually resume by left-clicking or stop completely by right-clicking while paused.

## Customization

### Change Update Interval
Modify the `interval` value in your Waybar config:
```json
"interval": 5  // Update every 5 seconds instead of 10
```

### Customize Icons
Edit the `format_output` method in `tailscale_module.py`:
```python
icon = "🟢"  # Change to your preferred icon
```

### Adjust Colors
Modify the CSS classes in `waybar-styles.css`:
```css
#custom-tailscale.connected {
    background-color: #your-color;
    color: #your-text-color;
}
```

### Change Pause Duration
Edit the pause duration in `tailscale_module.py`:
```python
pause_end = datetime.now() + timedelta(minutes=10)  # 10 minutes instead of 5
```

## Troubleshooting

### Module Not Appearing
- Verify the Python script path in your Waybar config
- Check that the script is executable: `chmod +x ~/.config/waybar/tailscale_module.py`
- Test the script manually: `python3 ~/.config/waybar/tailscale_module.py --status`

### Permission Errors
- Set up passwordless sudo for Tailscale (see installation step 5)
- Verify your user can run: `tailscale status`

### Click Actions Not Working
- Test click commands manually: `python3 ~/.config/waybar/tailscale_module.py --click left`
- Check Waybar logs by running `waybar` in a terminal

### Styling Issues
- Ensure CSS is properly appended to your style.css
- Restart Waybar after CSS changes
- Check for CSS syntax errors in the terminal output

## Technical Details

The module works by:
1. Polling `tailscale status --json` every 10 seconds
2. Parsing the JSON output to determine connection state
3. Formatting the output for Waybar with appropriate icons and tooltips
4. Handling click events to execute Tailscale commands via sudo

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes and test thoroughly
4. Commit your changes: `git commit -am 'Add feature'`
5. Push to the branch: `git push origin feature-name`
6. Submit a pull request



## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

