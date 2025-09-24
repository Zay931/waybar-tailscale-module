#!/usr/bin/env python3
"""
Waybar Tailscale Module
A compact Tailscale manager for Waybar that provides status display and click actions.
"""

import json
import subprocess
import sys
import argparse
import threading
import time
from datetime import datetime, timedelta
import os
import tempfile

class WaybarTailscaleModule:
    def __init__(self):
        self.pause_file = os.path.join(tempfile.gettempdir(), "tailscale_pause_state")
        self.duration_file = os.path.join(tempfile.gettempdir(), "tailscale_pause_duration")
        self.pause_durations = [1, 5, 10, 15, 30, 60, 120]  # minutes
        self.default_duration_index = 1  # 5 minutes
        
    def get_machine_name(self):
        """Get the current machine's Tailscale name"""
        try:
            # Try to get machine name from JSON status first
            result = subprocess.run(['tailscale', 'status', '--json'],
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                status_data = json.loads(result.stdout)
                # The Self field contains info about current machine
                self_info = status_data.get('Self')
                if self_info and 'DNSName' in self_info:
                    dns_name = self_info['DNSName']
                    # Remove the .tail-scale.ts.net suffix if present
                    machine_name = dns_name.split('.')[0]
                    if machine_name:
                        return machine_name
                
                # Fallback: try HostName from Self
                if self_info and 'HostName' in self_info:
                    return self_info['HostName']
            
            # Fallback: try to parse from regular status
            result = subprocess.run(['tailscale', 'status'],
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0 and result.stdout.strip():
                lines = result.stdout.strip().split('\n')
                # The first line is usually the current machine
                if lines:
                    first_line = lines[0].strip()
                    parts = first_line.split()
                    if len(parts) >= 2:
                        # Second column should be the machine name
                        machine_name = parts[1]
                        if machine_name and not machine_name.startswith('100.'):
                            return machine_name
                            
        except Exception:
            pass
        return "unknown"

    def get_tailscale_status(self):
        """Get Tailscale connection status"""
        try:
            result = subprocess.run(['tailscale', 'status', '--json'],
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                status_data = json.loads(result.stdout)
                backend_state = status_data.get('BackendState', 'Unknown')
                
                # Check for pause status
                pause_info = self.get_pause_status()
                if pause_info:
                    return {
                        'state': 'Paused',
                        'connected': False,
                        'machine_name': self.get_machine_name(),
                        'pause_info': pause_info
                    }
                
                if backend_state == 'Running':
                    # Check if we have peers and are actually connected
                    peers = status_data.get('Peer', {})
                    online_peers = sum(1 for peer in peers.values() if peer.get('Online', False))
                    
                    return {
                        'state': 'Connected',
                        'connected': True,
                        'machine_name': self.get_machine_name(),
                        'peer_count': online_peers,
                        'tailscale_ip': status_data.get('TailscaleIPs', ['N/A'])[0] if status_data.get('TailscaleIPs') else 'N/A'
                    }
                elif backend_state == 'Stopped':
                    return {
                        'state': 'Stopped',
                        'connected': False,
                        'machine_name': self.get_machine_name()
                    }
                else:
                    return {
                        'state': backend_state,
                        'connected': False,
                        'machine_name': self.get_machine_name()
                    }
                    
        except Exception as e:
            return {
                'state': 'Error',
                'connected': False,
                'machine_name': 'unknown',
                'error': str(e)
            }

    def get_pause_status(self):
        """Check if Tailscale is in paused state"""
        try:
            if os.path.exists(self.pause_file):
                with open(self.pause_file, 'r') as f:
                    pause_end_str = f.read().strip()
                    pause_end = datetime.fromisoformat(pause_end_str)
                    
                    if datetime.now() < pause_end:
                        remaining = pause_end - datetime.now()
                        minutes = int(remaining.total_seconds() // 60)
                        seconds = int(remaining.total_seconds() % 60)
                        return f"{minutes}m {seconds}s remaining"
                    else:
                        # Pause expired, remove file
                        os.remove(self.pause_file)
                        return None
        except Exception:
            pass
        return None

    def get_pause_duration(self):
        """Get current pause duration in minutes"""
        try:
            if os.path.exists(self.duration_file):
                with open(self.duration_file, 'r') as f:
                    index = int(f.read().strip())
                    if 0 <= index < len(self.pause_durations):
                        return self.pause_durations[index], index
        except Exception:
            pass
        return self.pause_durations[self.default_duration_index], self.default_duration_index

    def set_pause_duration_index(self, index):
        """Set pause duration index"""
        try:
            # Clamp index to valid range
            index = max(0, min(index, len(self.pause_durations) - 1))
            with open(self.duration_file, 'w') as f:
                f.write(str(index))
            return self.pause_durations[index]
        except Exception:
            return self.pause_durations[self.default_duration_index]

    def adjust_pause_duration(self, direction):
        """Adjust pause duration up or down"""
        current_duration, current_index = self.get_pause_duration()
        
        if direction == "up":
            new_index = min(current_index + 1, len(self.pause_durations) - 1)
        else:  # down
            new_index = max(current_index - 1, 0)
        
        new_duration = self.set_pause_duration_index(new_index)
        return new_duration, current_duration != new_duration

    def format_output(self, status):
        """Format output for Waybar JSON"""
        current_duration, _ = self.get_pause_duration()
        
        if status['state'] == 'Connected':
            icon = "🟢"
            text = "TS"
            css_class = "connected"
            tooltip = f"Tailscale Connected\nMachine: {status['machine_name']}\nIP: {status.get('tailscale_ip', 'N/A')}\nOnline Peers: {status.get('peer_count', 0)}\nPause Duration: {current_duration}min\n\nLeft Click: Toggle Connection\nRight Click: Pause {current_duration}min\nMiddle Click: Copy IP to clipboard\nScroll: Adjust pause duration"
        elif status['state'] == 'Paused':
            icon = "⏸️"
            text = "TS"
            css_class = "paused"
            tooltip = f"Tailscale Paused\nMachine: {status['machine_name']}\n{status['pause_info']}\nPause Duration: {current_duration}min\n\nLeft Click: Resume\nRight Click: Stop\nMiddle Click: Copy IP to clipboard\nScroll: Adjust pause duration"
        elif status['state'] == 'Stopped':
            icon = "🔴"
            text = "TS"
            css_class = "disconnected"
            tooltip = f"Tailscale Disconnected\nMachine: {status['machine_name']}\nPause Duration: {current_duration}min\n\nLeft Click: Connect\nRight Click: Pause {current_duration}min\nMiddle Click: Copy IP to clipboard\nScroll: Adjust pause duration"
        else:
            icon = "🔴"
            text = "TS"
            css_class = "error"
            error_msg = status.get('error', 'Unknown error')
            tooltip = f"Tailscale Error\nState: {status['state']}\nError: {error_msg}\nPause Duration: {current_duration}min\n\nLeft Click: Try Connect\nMiddle Click: Copy IP to clipboard\nScroll: Adjust pause duration"

        return {
            "text": f"{icon} {text}",
            "tooltip": tooltip,
            "class": css_class
        }

    def run_command(self, command):
        """Run a command and return success status"""
        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except Exception:
            return False

    def start_tailscale(self):
        """Start Tailscale connection"""
        # Clear any pause state
        if os.path.exists(self.pause_file):
            os.remove(self.pause_file)
        return self.run_command(['sudo', 'tailscale', 'up'])

    def stop_tailscale(self):
        """Stop Tailscale connection"""
        # Clear any pause state
        if os.path.exists(self.pause_file):
            os.remove(self.pause_file)
        return self.run_command(['sudo', 'tailscale', 'down'])

    def pause_tailscale(self):
        """Pause Tailscale for the configured duration"""
        current_duration, _ = self.get_pause_duration()
        
        if self.run_command(['sudo', 'tailscale', 'down']):
            # Set pause state
            pause_end = datetime.now() + timedelta(minutes=current_duration)
            with open(self.pause_file, 'w') as f:
                f.write(pause_end.isoformat())
            
            # Schedule auto-resume - create a separate script that handles the resume
            self.schedule_auto_resume(current_duration)
            return True
        return False

    def schedule_auto_resume(self, duration_minutes):
        """Schedule auto-resume using a separate background process"""
        import subprocess
        import sys
        
        # Create a command that will run after the specified time
        resume_command = [
            'bash', '-c', 
            f'sleep {duration_minutes * 60} && python3 {sys.argv[0]} --auto-resume'
        ]
        
        # Start the background process
        try:
            subprocess.Popen(resume_command, 
                           stdout=subprocess.DEVNULL, 
                           stderr=subprocess.DEVNULL,
                           start_new_session=True)
        except Exception:
            # Fallback to threading if subprocess fails
            def auto_resume():
                time.sleep(duration_minutes * 60)
                self.auto_resume()
            
            threading.Thread(target=auto_resume, daemon=False).start()

    def auto_resume(self):
        """Automatically resume Tailscale after pause period"""
        try:
            # Check if pause file still exists (user didn't manually resume)
            if os.path.exists(self.pause_file):
                # Read the pause end time
                with open(self.pause_file, 'r') as f:
                    pause_end_str = f.read().strip()
                    pause_end = datetime.fromisoformat(pause_end_str)
                
                # Only resume if the pause period has actually ended
                if datetime.now() >= pause_end:
                    os.remove(self.pause_file)
                    # Attempt to reconnect
                    self.start_tailscale()
        except Exception:
            # If anything goes wrong, just remove the pause file
            if os.path.exists(self.pause_file):
                try:
                    os.remove(self.pause_file)
                except Exception:
                    pass

    def handle_click(self, button):
        """Handle click actions"""
        status = self.get_tailscale_status()
        
        if button == "left":
            if status['state'] == 'Connected':
                # Toggle - disconnect
                self.stop_tailscale()
            elif status['state'] in ['Stopped', 'Paused']:
                # Connect
                self.start_tailscale()
            else:
                # Error state - try to connect
                self.start_tailscale()
                
        elif button == "right":
            if status['state'] == 'Connected':
                # Pause for configured duration
                self.pause_tailscale()
            elif status['state'] == 'Paused':
                # Stop completely
                self.stop_tailscale()
            else:
                # Start
                self.start_tailscale()
                
        elif button == "middle":
            # Copy IP to clipboard
            self.copy_ip_to_clipboard()

    def copy_ip_to_clipboard(self):
        """Copy the current machine's Tailscale IP to clipboard"""
        try:
            # Get the current status to extract IP
            status = self.get_tailscale_status()
            ip_address = status.get('tailscale_ip', 'N/A')
            
            if ip_address and ip_address != 'N/A':
                # Try different clipboard methods
                clipboard_commands = [
                    ['wl-copy', ip_address],  # Wayland
                    ['xclip', '-selection', 'clipboard', '-i'],  # X11
                    ['xsel', '--clipboard', '--input']  # X11 alternative
                ]
                
                for cmd in clipboard_commands:
                    try:
                        if cmd[0] == 'wl-copy':
                            result = subprocess.run(cmd, timeout=2)
                        else:
                            result = subprocess.run(cmd, input=ip_address, text=True, timeout=2)
                        
                        if result.returncode == 0:
                            return True
                    except (subprocess.TimeoutExpired, FileNotFoundError):
                        continue
                
                # Fallback: try to use python clipboard libraries if available
                try:
                    import pyperclip
                    pyperclip.copy(ip_address)
                    return True
                except ImportError:
                    pass
                    
        except Exception:
            pass
        return False
        """Handle scroll wheel actions"""
        new_duration, changed = self.adjust_pause_duration(direction)
        return new_duration if changed else None

    def get_status_output(self):
        """Get current status for Waybar output"""
        try:
            status = self.get_tailscale_status()
            return self.format_output(status)
        except Exception as e:
            # If anything goes wrong, return a valid JSON error state
            return {
                "text": "🔴 TS",
                "tooltip": f"Error: {str(e)}",
                "class": "error"
            }

def main():
    parser = argparse.ArgumentParser(description='Waybar Tailscale Module')
    parser.add_argument('--click', choices=['left', 'right', 'middle'], 
                       help='Handle click action')
    parser.add_argument('--scroll', choices=['up', 'down'], 
                       help='Handle scroll action')
    parser.add_argument('--status', action='store_true', 
                       help='Output current status (default)')
    parser.add_argument('--auto-resume', action='store_true', 
                       help='Auto-resume after pause (internal use)')
    
    args = parser.parse_args()
    
    try:
        module = WaybarTailscaleModule()
        
        if args.auto_resume:
            # Handle auto-resume
            module.auto_resume()
            return
        elif args.click:
            module.handle_click(args.click)
            # After handling click, output updated status
            time.sleep(1)  # Brief delay for command to take effect
        elif args.scroll:
            new_duration = module.handle_scroll(args.scroll)
            # Don't need delay for scroll, just output updated status
        
        # Default action is to output status
        output = module.get_status_output()
        print(json.dumps(output))
        
    except Exception as e:
        # If everything fails, output a minimal valid JSON
        error_output = {
            "text": "❌ TS",
            "tooltip": f"Module Error: {str(e)}",
            "class": "error"
        }
        print(json.dumps(error_output))

if __name__ == "__main__":
    main()