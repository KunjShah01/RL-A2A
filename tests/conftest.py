"""Test configuration.

Ensure the repository root is on sys.path so tests can import `src.*`.
This is a robust, permanent fixture: it walks upward from the tests folder
to locate the project root (where `pyproject.toml` or `setup.py` lives) and
inserts it onto `sys.path` if missing. This avoids test flakiness across IDEs
and CI where `sitecustomize.py` may not be loaded.
"""

import sys
from pathlib import Path


def _find_project_root(start: Path) -> Path:
	current = start.resolve()
	for parent in [current] + list(current.parents):
		if (parent / "pyproject.toml").exists() or (parent / "setup.py").exists() or (parent / ".git").exists():
			return parent
	# fallback to repository two levels up (tests/..)
	return start.resolve().parents[1]


ROOT = _find_project_root(Path(__file__).parent)
ROOT_STR = str(ROOT)
if ROOT_STR not in sys.path:
	sys.path.insert(0, ROOT_STR)

__all__ = []
