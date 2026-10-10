import re

with open('index.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for idx, line in enumerate(lines):
    if 'function openGame' in line or 'function selectGame' in line or 'function launchGame' in line or 'function playGame' in line or 'openGameModal' in line:
        print(f"Line {idx+1}: {line.strip()}")
        for sub in lines[idx:idx+45]:
            print("  ", sub.rstrip())
        print("="*60)
