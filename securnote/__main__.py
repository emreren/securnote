"""
Entry point for SecurNote application.
"""

from .cli import SecurNoteCLI

if __name__ == "__main__":
    app = SecurNoteCLI()
    app.run()
