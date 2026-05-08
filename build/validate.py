"""Compatibility wrapper for the CSV validator."""
import sys

from validate_data import validate_all


if __name__ == "__main__":
    sys.exit(1 if validate_all() else 0)
