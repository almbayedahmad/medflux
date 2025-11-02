import subprocess
import sys


FORBIDDEN_PREFIXES = [
    "OneDrive/",
    "Desktop/",
    "Downloads/",
    "medflux/outputs/",
    "outputs/",
]


def get_tracked_files() -> list[str]:
    out = subprocess.check_output(["git", "ls-files"], text=True)
    return [line.strip() for line in out.splitlines() if line.strip()]


def main() -> int:
    tracked = get_tracked_files()
    offenders: list[str] = []
    for path in tracked:
        for pref in FORBIDDEN_PREFIXES:
            if path.startswith(pref):
                offenders.append(path)
                break

    if offenders:
        print("Forbidden tracked paths detected (update .gitignore or move files):", file=sys.stderr)
        for p in offenders:
            print(f" - {p}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
