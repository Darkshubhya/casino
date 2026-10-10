import json

html_found = None
js_found = None

with open(r'C:\Users\vedan\.gemini\antigravity-ide\brain\9f173e54-b675-49cf-9521-021c312b1cba\.system_generated\logs\transcript_full.jsonl', 'r', encoding='utf-8', errors='ignore') as f:
    for line in f:
        data = json.loads(line)
        content = data.get('content', '')
        if 'id="gameRouletteContainer"' in content and 'rouletteStatusBanner' in content:
            html_found = content
        if 'function confirmRouletteBetAndSpin' in content and 'function animateRouletteSpin' in content:
            js_found = content

with open('scratch/roulette_html.txt', 'w', encoding='utf-8') as out:
    out.write(html_found or 'NOT FOUND')

with open('scratch/roulette_js.txt', 'w', encoding='utf-8') as out:
    out.write(js_found or 'NOT FOUND')

print("Extraction done!")
