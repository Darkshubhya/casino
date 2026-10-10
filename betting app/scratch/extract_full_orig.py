import json

with open(r'C:\Users\vedan\.gemini\antigravity-ide\brain\9f173e54-b675-49cf-9521-021c312b1cba\.system_generated\logs\transcript_full.jsonl', 'r', encoding='utf-8', errors='ignore') as f:
    for i, line in enumerate(f):
        data = json.loads(line)
        content = data.get('content', '')
        if 'id="gameRouletteContainer"' in content and 'roulette-felt' in content:
            print(f'Found full roulette at line {i}')
            with open('scratch/full_orig_roulette.html', 'w', encoding='utf-8') as out:
                out.write(content)
            break
print('Extraction complete!')
