import re

with open('index.html', 'r', encoding='utf-8') as f:
    content = f.read()

game_containers = re.findall(r'id=[\"\'](game[A-Za-z0-9_-]+)[\"\']', content)
print("Game containers:", set(game_containers))

modal_switches = re.findall(r'gameId === [\'\"]([a-zA-Z0-9_-]+)[\'\"]', content)
print("Modal switches:", set(modal_switches))
