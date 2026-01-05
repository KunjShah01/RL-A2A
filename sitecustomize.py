"""
Project local sitecustomize hook to ensure the repository root is on sys.path.

This is a permanent solution so `import src.*` works when running Python from the
project root (development and test runs) without requiring test-specific hacks.
"""
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
root_str = str(_ROOT)
if root_str not in sys.path:
    # Insert at front so project packages shadow other installed packages during dev
    sys.path.insert(0, root_str)
