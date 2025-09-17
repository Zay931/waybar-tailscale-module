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

    def format_output(self, status):
        """Format output for Waybar JSON"""
        if status['state'] == 'Connected':
            icon = "🟢"
            text = "TS"
            css_class = "connected"
            tooltip = f"Tailscale Connected\nMachine: {status['machine_name']}\nIP: {status.get('tailscale_ip', 'N/A')}\nOnline Peers: {status.get('peer_count', 0)}\n\nLeft Click: Toggle Connection\nRight Click: Pause 5min\nMiddle Click: Refresh"
        elif status['state'] == 'Paused':
            icon = "⏸️"
            text = "TS"
            css_class = "paused"
            tooltip = f"Tailscale Paused\nMachine: {status['machine_name']}\n{status['pause_info']}\n\nLeft Click: Resume\nRight Click: Stop\nMiddle Click: Refresh"
        elif status['state'] == 'Stopped':
            icon = "🔴"
            text = "TS"
            css_class = "disconnected"
            tooltip = f"Tailscale Disconnected\nMachine: {status['machine_name']}\n\nLeft Click: Connect\nRight Click: Pause 5min\nMiddle Click: Refresh"
        else:
            icon = "🔴"
            text = "TS"
            css_class = "error"
            error_msg = status.get('error', 'Unknown error')
            tooltip = f"Tailscale Error\nState: {status['state']}\nError: {error_msg}\n\nLeft Click: Try Connect\nMiddle Click: Refresh"

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
        """Pause Tailscale for 5 minutes"""
        if self.run_command(['sudo', 'tailscale', 'down']):
            # Set pause state
            pause_end = datetime.now() + timedelta(minutes=5)
            with open(self.pause_file, 'w') as f:
                f.write(pause_end.isoformat())
            
            # Schedule auto-resume
            def auto_resume():
                time.sleep(300)  # 5 minutes
                if os.path.exists(self.pause_file):
                    os.remove(self.pause_file)
                    self.start_tailscale()
            
            threading.Thread(target=auto_resume, daemon=True).start()
            return True
        return False

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
                # Pause for 5 minutes
                self.pause_tailscale()
            elif status['state'] == 'Paused':
                # Stop completely
                self.stop_tailscale()
            else:
                # Start
                self.start_tailscale()
                
        elif button == "middle":
            # Refresh - just update status
            pass

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
    parser.add_argument('--status', action='store_true', 
                       help='Output current status (default)')
    
    args = parser.parse_args()
    
    try:
        module = WaybarTailscaleModule()
        
        if args.click:
            module.handle_click(args.click)
            # After handling click, output updated status
            time.sleep(1)  # Brief delay for command to take effect
        
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
