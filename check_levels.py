import json

with open('data/levels.json', 'r', encoding='utf-8') as f:
    levels = json.load(f)

print('Current Levels:')
for level in levels:
    level_num = level.get('level')
    question_count = len(level.get('questions', []))
    print(f'  Level {level_num}: {question_count} questions')

max_level = max([lvl.get('level', 0) for lvl in levels])
print(f'\nMax level: {max_level}')
print(f'Next available levels should be: {list(range(max_level + 1, max_level + 11))}')