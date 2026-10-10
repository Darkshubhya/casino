import json

with open(r'C:\Users\vedan\.gemini\antigravity-ide\brain\9f173e54-b675-49cf-9521-021c312b1cba\.system_generated\logs\transcript_full.jsonl', 'r', encoding='utf-8', errors='ignore') as f:
    for line in f:
        data = json.loads(line)
        content = data.get('content', '')
        if 'id="gameRouletteContainer"' in content and 'funRouletteCanvas' in content:
            with open('scratch/orig_roulette_container.html', 'w', encoding='utf-8') as out:
                out.write(content)
            print("Found HTML!")
            break
