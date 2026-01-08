"""
Pytest configuration for the test suite.

Skip collecting the package root __init__.py so tests don't try to import it
as a standalone module (which breaks its relative imports).
"""

import sys
from pathlib import Path

# Ensure repository root is importable for test modules
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

collect_ignore = ["../__init__.py"]
