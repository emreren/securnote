#!/usr/bin/env python3
"""
Start Prometheus metrics server for SecurNote monitoring
"""

import sys
import time
import signal
import os
sys.path.insert(0, '/app')

from securnote.metrics import metrics_collector
from securnote.logging_config import setup_logging

def signal_handler(sig, frame):
    """Handle shutdown gracefully."""
    print("\nShutting down metrics server...")
    sys.exit(0)

def main():
    """Start metrics server."""
    # Setup logging
    log_level = os.getenv('LOG_LEVEL', 'INFO')
    setup_logging(log_level)

    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Start metrics server
    port = int(os.getenv('METRICS_PORT', '9090'))
    print(f"Starting SecurNote Prometheus metrics server on port {port}")
    metrics_collector.start_server()

    # Keep running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        signal_handler(None, None)

if __name__ == "__main__":
    main()