import json, argparse
from .file_type_detector import detect_many

def main():
    ap = argparse.ArgumentParser(description="Run File Type Detection")
    ap.add_argument("paths", nargs="+", help="File paths")
    args = ap.parse_args()
    res = detect_many(args.paths)
    print(json.dumps([r.to_dict() for r in res], ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()


