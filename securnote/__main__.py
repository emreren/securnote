"""
Entry point for SecurNote application.
"""

import sys
from .cli import SecurNoteCLI
from .remote_cli import main as remote_main


def main():
    # Check if running with command line arguments (remote mode)
    if len(sys.argv) > 1:
        # Use remote CLI for command-line operations
        remote_main()
    else:
        # Use interactive CLI for normal operation
        app = SecurNoteCLI()
        app.run()


if __name__ == "__main__":
    main()
