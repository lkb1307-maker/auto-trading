from __future__ import annotations

import argparse
import unicodedata
from collections import Counter
from pathlib import Path

BIDI_CONTROLS = {
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


def clean_text(text: str) -> tuple[str, Counter[int]]:
    removed: Counter[int] = Counter()
    cleaned_chars: list[str] = []

    for char in text:
        codepoint = ord(char)
        if unicodedata.category(char) == "Cf" or codepoint in BIDI_CONTROLS:
            removed[codepoint] += 1
            continue
        cleaned_chars.append(char)

    return "".join(cleaned_chars), removed


def clean_file(path: Path) -> tuple[bool, Counter[int]]:
    raw = path.read_bytes()
    original = raw.decode("utf-8")
    cleaned, removed = clean_text(original)
    had_carriage_return = b"\r" in raw
    changed = cleaned != original or had_carriage_return
    if not changed:
        return False, Counter()

    path.write_text(cleaned, encoding="utf-8", newline="\n")
    return True, removed


def main() -> int:
    parser = argparse.ArgumentParser(description="Strip hidden/bidi unicode controls")
    parser.add_argument("files", nargs="+", help="Files to sanitize")
    args = parser.parse_args()

    total = Counter()
    changed_count = 0

    for file_arg in args.files:
        path = Path(file_arg)
        changed, removed = clean_file(path)
        if changed:
            changed_count += 1
            total.update(removed)
            detail = ", ".join(
                f"U+{codepoint:04X} x{count}"
                for codepoint, count in sorted(removed.items())
            )
            removed_count = sum(removed.values())
            print(f"UPDATED {path}: removed_count={removed_count}; {detail}")
        else:
            print(f"OK {path}: removed_count=0")

    if total:
        summary = ", ".join(
            f"U+{codepoint:04X} x{count}" for codepoint, count in sorted(total.items())
        )
        print(f"Removed summary: {summary}")
    else:
        print("Removed summary: none")

    print(f"Files changed: {changed_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
