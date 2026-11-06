import argparse
import json
import re
import sys
from pathlib import Path


def _parse_value(raw_value):
    """Parse the right-hand side of a .env assignment."""
    value = raw_value.strip()
    if not value:
        return ""

    # Quoted values preserve their contents, including ``#`` characters. A
    # trailing comment after the closing quote is ignored.
    if value[0] == "'":
        end = value.find("'", 1)
        return value[1:] if end == -1 else value[1:end]

    if value[0] == '"':
        collected = []
        i = 1
        while i < len(value):
            char = value[i]
            if char == "\\" and i + 1 < len(value):
                nxt = value[i + 1]
                collected.append({
                    "n": "\n",
                    "t": "\t",
                    "r": "\r",
                    '"': '"',
                    "'": "'",
                    "\\": "\\",
                }.get(nxt, "\\" + nxt))
                i += 2
                continue
            if char == '"':
                break
            collected.append(char)
            i += 1
        return "".join(collected)

    # Unquoted values may contain an inline comment preceded by whitespace.
    match = re.search(r"\s+#", value)
    if match:
        value = value[:match.start()].rstrip()
    return value


def parse_env(path):
    values = {}
    for line_number, raw in enumerate(Path(path).read_text().splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue

        if re.match(r"^export\s+", line):
            line = re.sub(r"^export\s+", "", line, count=1).strip()

        if "=" not in line:
            raise ValueError(f"{path}:{line_number}: invalid line: {raw!r}")

        key, value = line.split("=", 1)
        key = key.strip()
        if not key:
            raise ValueError(f"{path}:{line_number}: empty key")
        values[key] = _parse_value(value)
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
    parser.add_argument(
        "--ignore",
        action="append",
        default=[],
        help="Comma-separated keys to ignore; may be repeated",
    )
    parser.add_argument("--show-values", action="store_true")
    args = parser.parse_args(argv)

    ignored = []
    for group in args.ignore:
        ignored.extend(item.strip() for item in group.split(",") if item.strip())

    try:
        left = parse_env(args.left)
        right = parse_env(args.right)
    except (OSError, ValueError, UnicodeError) as exc:
        print(f"envdiff: {exc}", file=sys.stderr)
        return 2

    result = compare(left, right, ignored)

    if args.as_json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        sys.stdout.write(format_text(result, left, right, args.show_values))
    return 1 if any(result.values()) else 0


if __name__ == "__main__":
    raise SystemExit(main())
