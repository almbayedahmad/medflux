from __future__ import annotations

import json
from . import get_version_info


def main() -> None:
    """CLI entry to emit version info to stdout as JSON.

    Outcome:
        Prints a JSON object with version fields so test harnesses that
        capture stdout can parse it directly.
    """
    info = get_version_info()
    print(json.dumps(info, ensure_ascii=False))


if __name__ == "__main__":
    main()
