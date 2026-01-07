"""
Pytest configuration for the test suite.

Skip collecting the package root __init__.py so tests don't try to import it
as a standalone module (which breaks its relative imports).
"""

collect_ignore = ["../__init__.py"]
