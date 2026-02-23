from pathlib import Path

FILES = [
  'README.md',
  'src/app/bot.py',
  'src/app/run_once_e2e.py',
  'src/app/state.py',
  'src/config/settings.py',
  'src/exchange/binance_testnet.py',
]

def read_any(p: Path) -> str:
  # utf-8 우선, 실패 시 utf-8-sig(BOM 포함)로 재시도
  try:
    return p.read_text(encoding='utf-8')
  except UnicodeDecodeError:
    return p.read_text(encoding='utf-8-sig')

changed = []
for f in FILES:
  p = Path(f)
  if not p.exists():
    continue
  text = read_any(p)
  # 개행 정규화: CRLF/CR -> LF
  text = text.replace('\r\n', '\n').replace('\r', '\n')
  # UTF-8 + LF로 재저장
  p.write_text(text, encoding='utf-8', newline='\n')
  changed.append(f)

print('Rewrote files as UTF-8 with LF:')
for f in changed:
  print(' -', f)
