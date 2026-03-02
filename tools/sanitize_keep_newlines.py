import unicodedata as ud
from pathlib import Path

FILES = [
  'README.md',
  'src/app/bot.py',
  'src/app/run_once_e2e.py',
  'src/app/state.py',
  'src/config/settings.py',
]

def clean(s: str) -> tuple[str, int]:
  # 개행 형태만 통일 (CRLF/CR -> LF). LF 자체는 유지.
  s = s.replace('\r\n', '\n').replace('\r', '\n')
  out = []
  removed = 0
  for ch in s:
    if ch in ('\n', '\t'):
      out.append(ch); continue
    cat = ud.category(ch)
    if cat in ('Cc','Cf'):
      removed += 1
      continue
    out.append(ch)
  return ''.join(out), removed

total_removed = 0
for f in FILES:
  p = Path(f)
  if not p.exists():
    continue
  raw = p.read_text(encoding='utf-8', errors='ignore')
  cleaned, removed = clean(raw)
  # newline='\n'로 저장해서 LF 강제
  p.write_text(cleaned, encoding='utf-8', newline='\n')
  print(f'{f}: removed {removed}')
  total_removed += removed

print('TOTAL removed:', total_removed)
