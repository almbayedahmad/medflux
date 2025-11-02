from __future__ import annotations

import json
from . import get_version_info


def main() -> None:
    info = get_version_info()
    print(json.dumps(info, ensure_ascii=False))


if __name__ == "__main__":
    main()
