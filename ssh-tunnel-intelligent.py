#!/usr/bin/env python3
"""Intelligent SSH Tunnel Launcher for VibeProxy

This script provides:
- Auto-discovery of Mac when IP changes
- Intelligent error classification
- Smart retry logic (doesn't loop forever)
- Auto-config update when Mac found at new IP
- Clear, actionable error messages
- Verbose logging options for monitoring
- Real-time activity monitoring
"""

import sys
import time
import argparse
import logging
from datetime import datetime
from pathlib import Path

# Add vibeproxy_manager to path
sys.path.insert(0, str(Path(__file__).parent))

from vibeproxy_manager.tunnel import TunnelManager
from vibeproxy_manager.config import ConfigManager


def setup_logging(verbose=False, very_verbose=False, log_file=None):
    """Setup logging with appropriate level and format."""
    level = logging.DEBUG if very_verbose else (logging.INFO if verbose else logging.WARNING)
    
    handlers = []
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)
    handlers.append(console_handler)
    
    # File handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s')
        file_handler.setFormatter(file_formatter)
        handlers.append(file_handler)
    
    logging.basicConfig(
        level=level,
        handlers=handlers,
        force=True  # Override any existing logging config
    )


def print_header():
    """Print welcome header."""
    print("=" * 79)
    print(" " * 15 + "VibeProxy SSH Tunnel - Intelligent Auto-Connect")
    print("=" * 79)
    print()


def print_config(tunnel: TunnelManager, verbose=False):
    """Print current configuration."""
    print("  🔌 Configuration:")
    print(f"     Mac Target      : {tunnel.mac_user}@{tunnel.mac_ip}")
    print(f"     Local Port      : {tunnel.port}")
    print(f"     Remote Port     : {tunnel.config_manager.load().remote_port}")
    print(f"     Auto-Discover   : {'Enabled' if verbose else 'Enabled (scans network if IP changed)'}")
    if verbose:
        print(f"     SSH Password    : {'Yes' if tunnel.config_manager.load().ssh_password else 'No'}")
        print(f"     Platform        : {sys.platform}")
    print()
    print("  💡 Features:")
    print("     • Automatically finds Mac if IP changes")
    print("     • Updates config when Mac found at new IP")
    print("     • Provides clear error messages")
    print("     • Smart retry (doesn't loop forever)")
    if verbose:
        print("     • Verbose logging enabled")
    print()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='VibeProxy SSH Tunnel - Intelligent Auto-Connect')
    parser.add_argument('-v', '--verbose', action='store_true', help='Show detailed connection information')
    parser.add_argument('-vv', '--very-verbose', action='store_true', help='Show extensive debugging information')
    parser.add_argument('--log-file', help='Log output to specified file')
    parser.add_argument('--monitor', action='store_true', help='Enable real-time activity monitoring')
    parser.add_argument('--kill-port', action='store_true', help='Kill any process using the tunnel port before connecting')
    
    args = parser.parse_args()
    
    # Setup logging based on arguments
    setup_logging(verbose=args.verbose, very_verbose=args.very_verbose, log_file=args.log_file)
    
    if args.verbose or args.very_verbose:
        logging.info("Verbose mode enabled")
    if args.monitor:
        logging.info("Real-time monitoring enabled")

    print_header()
    
    # Handle --kill-port option
    if args.kill_port:
        print("🔪 Kill port mode - checking for processes on tunnel port...\n")
        temp_tunnel = TunnelManager()
        success, message = temp_tunnel.force_reset()
        print(f"   {message}")
        print()
        if not args.monitor:
            return 0

    # Initialize tunnel manager
    tunnel = TunnelManager()

    # Show config
    print_config(tunnel, verbose=args.verbose or args.very_verbose)

    # Check if already running
    if tunnel.is_running():
        print("✅ Tunnel is already running!")
        print(f"   Port {tunnel.port} is open and listening")
        print()
        print("   Test with: curl http://localhost:8317/v1/models")
        return 0

    print("🚀 Starting intelligent connection...\n")

    # Use intelligent connection with auto-discovery
    success, message = tunnel.connect_with_retry(max_attempts=3, auto_discover=True)

    if args.very_verbose:
        logging.debug(f"Initial connection result: success={success}, message={message}")

    if success:
        print(f"\n✅ SUCCESS! {message}")
        print(f"   Port {tunnel.port} is now open")
        print()
        print("   Test with: curl http://localhost:8317/v1/models")
        print()
        print("   Keep this window open while using VibeProxy")
        print("   Press Ctrl+C to disconnect")

        # Keep tunnel alive
        try:
            while True:
                time.sleep(30)  # Check every 30 seconds instead of 60
                
                if args.monitor or args.verbose:
                    current_time = time.strftime('%H:%M:%S')
                    if tunnel.is_running():
                        print(f"   🟢 [{current_time}] Tunnel ACTIVE - Port {tunnel.port} accessible")
                        logging.info(f"Tunnel active at {current_time}")
                    else:
                        print(f"   🔴 [{current_time}] Tunnel INACTIVE - Port {tunnel.port} not responding")
                        logging.warning(f"Tunnel inactive at {current_time}")
                
                if not tunnel.is_running():
                    print("\n⚠️  Tunnel connection lost!")
                    print("   Attempting to reconnect...\n")
                    logging.warning("Tunnel connection lost, attempting to reconnect...")
                    
                    success, message = tunnel.connect_with_retry(
                        max_attempts=3, auto_discover=True
                    )
                    
                    if args.very_verbose:
                        logging.debug(f"Reconnection result: success={success}, message={message}")
                    
                    if not success:
                        print(f"\n❌ Reconnection failed: {message}")
                        logging.error(f"Reconnection failed: {message}")
                        return 1
                    else:
                        print(f"\n✅ Reconnected successfully!")
                        logging.info("Successfully reconnected tunnel")
        except KeyboardInterrupt:
            print("\n\n👋 Disconnecting...")
            tunnel.stop()
            return 0
    else:
        print(f"\n❌ FAILED: {message}")
        print()
        print("   The tunnel could not be established.")
        print("   Review the messages above for specific guidance.")
        return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
