from __future__ import annotations

import argparse
import unicodedata
from collections import Counter
from pathlib import Path

BIDI_CODEPOINTS = {
    0x061C,
    0x200E,
    0x200F,
    0x202A,
    0x202B,
    0x202C,
    0x202D,
    0x202E,
    0x2066,
    0x2067,
    0x2068,
    0x2069,
}


def sanitize_text(text: str) -> tuple[str, Counter[int]]:
    removed: Counter[int] = Counter()
    output_chars: list[str] = []

    for char in text:
        codepoint = ord(char)
        is_format_char = unicodedata.category(char) == "Cf"
        if is_format_char or codepoint in BIDI_CODEPOINTS:
            removed[codepoint] += 1
            continue
        output_chars.append(char)

    return "".join(output_chars), removed


def sanitize_file(path: Path) -> tuple[bool, Counter[int]]:
    original = path.read_text(encoding="utf-8")
    cleaned, removed = sanitize_text(original)

    if cleaned != original:
        path.write_text(cleaned, encoding="utf-8", newline="\n")
        return True, removed

    return False, Counter()


def main() -> int:
    parser = argparse.ArgumentParser(description="Remove hidden/bidi unicode controls")
    parser.add_argument("files", nargs="+", help="Files to sanitize")
    args = parser.parse_args()

    changed = 0
    total_removed: Counter[int] = Counter()

    for raw_path in args.files:
        path = Path(raw_path)
        updated, removed = sanitize_file(path)
        if updated:
            changed += 1
            total_removed.update(removed)
            removed_desc = ", ".join(
                f"U+{cp:04X} x{count}" for cp, count in sorted(removed.items())
            )
            print(f"UPDATED {path}: {removed_desc}")
        else:
            print(f"OK {path}: no hidden/bidi controls found")

    if total_removed:
        summary = ", ".join(
            f"U+{cp:04X} x{count}" for cp, count in sorted(total_removed.items())
        )
        print(f"Removed controls summary: {summary}")
    else:
        print("No control characters removed")

    print(f"Files changed: {changed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
