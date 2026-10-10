import json

with open(r'C:\Users\vedan\.gemini\antigravity-ide\brain\9f173e54-b675-49cf-9521-021c312b1cba\.system_generated\logs\transcript_full.jsonl', 'r', encoding='utf-8', errors='ignore') as f:
    for i, line in enumerate(f):
        data = json.loads(line)
        content = data.get('content', '')
        if 'id="gameRouletteContainer"' in content:
            print(f'Match on line {i}')
            idx = content.find('id="gameRouletteContainer"')
            snippet = content[max(0, idx - 100):min(len(content), idx + 8000)]
            with open(f'scratch/found_html_{i}.txt', 'w', encoding='utf-8') as out:
                out.write(snippet)
print('Done!')
