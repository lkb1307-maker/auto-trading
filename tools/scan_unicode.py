import unicodedata as ud
from pathlib import Path
import subprocess

out = subprocess.check_output(
    ["git", "diff", "--name-only", "origin/main...HEAD"],
    text=True
)
files = [f.strip() for f in out.splitlines() if f.strip()]

def read_text(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return p.read_text(encoding="utf-8-sig")

any_hits = False

for f in files:
    p = Path(f)
    if not p.is_file():
        continue

    data = read_text(p)
    hits = []

    for i, ch in enumerate(data):
        if ud.category(ch) == "Cf":
            hits.append((i, "U+%04X" % ord(ch), ud.name(ch, "UNKNOWN")))

    if hits:
        any_hits = True
        print("\n%s -> %d Cf chars" % (f, len(hits)))
        for (i, code, name) in hits[:20]:
            print("  idx=%d %s %s" % (i, code, name))

if not any_hits:
    print("No Cf (format) characters found in changed files.")
