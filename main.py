#!/usr/bin/env python3
"""Launch the CustomOS shell. Requires Python 3.11+ on Linux/WSL2/macOS."""
import sys

from customos.shell import Shell


def main() -> int:
    if sys.version_info < (3, 11):
        print("Error: Python 3.11 or newer is required.", file=sys.stderr)
        return 2
    try:
        Shell().run()
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
