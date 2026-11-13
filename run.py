"""Offline launcher: no package installation or external dependencies needed."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
from integer_neuron_lab.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
