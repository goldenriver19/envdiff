import argparse
import json
import re
import sys
from pathlib import Path


def parse_env(path):
    values = {}
    for line_number, raw in enumerate(Path(path).read_text().splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export "):].strip()
        if "=" not in line:
            raise ValueError(f"{path}:{line_number}: invalid line: {raw!r}")
        key, value = line.split("=", 1)
        key = key.strip()
        if not key:
            raise ValueError(f"{path}:{line_number}: empty key")
        # Strip inline comments outside quotes.
        value = value.strip()
        if value and value[0] not in ('"', "'"):
            if " #" in value:
                value = value.split(" #", 1)[0].rstrip()
        value = value.strip().strip('"').strip("'")
        values[key] = value
    return values


def compare(left, right, ignored=None):
    ignored = set(ignored or [])
    left_keys = set(left) - ignored
    right_keys = set(right) - ignored
    return {
        "missing": sorted(left_keys - right_keys),
        "extra": sorted(right_keys - left_keys),
        "changed": sorted(key for key in left_keys & right_keys if left[key] != right[key]),
    }


def format_text(result, left_values, right_values, show_values):
    lines = []
    for key in result["missing"]:
        lines.append(f"- {key}" + (f" = {left_values[key]!r}" if show_values else ""))
    for key in result["extra"]:
        lines.append(f"+ {key}" + (f" = {right_values[key]!r}" if show_values else ""))
    for key in result["changed"]:
        if show_values:
            lines.append(f"~ {key}: {left_values[key]!r} -> {right_values[key]!r}")
        else:
            lines.append(f"~ {key}")
    if not lines:
        lines.append("No differences found.")
    return "\n".join(lines) + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser(description="Compare two .env files.")
    parser.add_argument("left")
    parser.add_argument("right")
    parser.add_argument("--json", action="store_true", dest="as_json")
    parser.add_argument("--ignore", default="", help="Comma-separated keys to ignore")
    parser.add_argument("--show-values", action="store_true")
    args = parser.parse_args(argv)

    ignored = [item.strip() for item in args.ignore.split(",") if item.strip()]
    left = parse_env(args.left)
    right = parse_env(args.right)
    result = compare(left, right, ignored)

    if args.as_json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        sys.stdout.write(format_text(result, left, right, args.show_values))
    return 1 if any(result.values()) else 0


if __name__ == "__main__":
    raise SystemExit(main())
