import json

# Load levels and chapters
with open("data/levels.json", "r", encoding="utf-8") as f:
    levels = json.load(f)

with open('data/chapters.json', 'r', encoding='utf-8') as f:
    chapters_data = json.load(f)
chapters = chapters_data.get('chapters', [])

print("Chapters:")
for chapter in chapters:
    print(f"  Chapter {chapter.get('id')}: {chapter.get('name')} - Level Range: {chapter.get('level_range', 'Not set')}")

print("\nCreating level_to_chapter mapping...")

# Map level number to chapter object (same logic as in app.py)
level_to_chapter = {}
for chapter in chapters:
    if 'level_range' in chapter:
        for lvl in chapter['level_range']:
            level_to_chapter[lvl] = chapter

print("\nLevel to Chapter Mapping:")
for level_num, chapter in level_to_chapter.items():
    print(f"  Level {level_num} → Chapter {chapter.get('id')} ({chapter.get('name')})")

print("\nFirst 5 levels and their chapter assignments:")
for level in levels[:5]:
    level_num = level.get('level')
    if level_num in level_to_chapter:
        chapter = level_to_chapter[level_num]
        print(f"  Level {level_num}: Chapter {chapter.get('id')} ({chapter.get('name')})")
    else:
        print(f"  Level {level_num}: Unassigned")

print("\nLevels 11-15 and their chapter assignments:")
for level in levels[10:15]:  # Levels 11-15
    level_num = level.get('level')
    if level_num in level_to_chapter:
        chapter = level_to_chapter[level_num]
        print(f"  Level {level_num}: Chapter {chapter.get('id')} ({chapter.get('name')})")
    else:
        print(f"  Level {level_num}: Unassigned")