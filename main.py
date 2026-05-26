"""
Main entry point for the Sports Tournament Scheduling application.
Run this file to start the GUI.
"""

import os
import sys
# Ensure the script directory is on sys.path so sibling imports work when
# executing this file directly (e.g., `python src/src/main.py`).
sys.path.insert(0, os.path.dirname(__file__))

from gui import TournamentGUI  # if using a package, change to: from .gui import TournamentGUI


def main():
    app = TournamentGUI()
    app.mainloop()


if __name__ == "__main__":
    main()
