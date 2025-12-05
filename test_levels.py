import json

# Test the level loading logic
def load_chapters():
    with open('data/chapters.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def load_levels():
    with open('data/levels.json', 'r', encoding='utf-8') as f:
        return json.load(f)

try:
    levels_data = load_levels()
    chapters_data = load_chapters()
    
    # Get Chapter 2 levels (levels 11-20)
    chapter_2 = None
    for chapter in chapters_data.get("chapters", []):
        if chapter.get("id") == 2:
            chapter_2 = chapter
            break
    
    if chapter_2:
        print("Found Chapter 2!")
        print(f"Chapter 2 name: {chapter_2.get('name')}")
        print(f"Chapter 2 description: {chapter_2.get('description')}")
        
        # Show Chapter 2's levels (11-20) for assignment
        chapter_2_levels = list(range(11, 21))
        available_levels = chapter_2_levels
        print(f"Available levels for assignment: {available_levels}")
    else:
        print("Chapter 2 not found!")
        
except Exception as e:
    print(f"Error: {e}")