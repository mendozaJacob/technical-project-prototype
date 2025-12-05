import json

# Load current levels
with open('data/levels.json', 'r', encoding='utf-8') as f:
    levels_data = json.load(f)

# Find Level 14 and add the AI-generated questions (136-145)
ai_question_ids = list(range(136, 146))  # IDs 136-145

for level in levels_data:
    if level.get('level') == 14:
        print(f"Level 14 currently has questions: {level.get('questions', [])}")
        
        # Add the AI-generated questions
        if 'questions' not in level:
            level['questions'] = []
        
        # Add the AI questions to level 14
        level['questions'].extend(ai_question_ids)
        print(f"Level 14 now has questions: {level['questions']}")
        break

# Save updated levels
with open('data/levels.json', 'w', encoding='utf-8') as f:
    json.dump(levels_data, f, indent=2, ensure_ascii=False)

print("✅ Successfully assigned AI-generated questions (136-145) to Level 14!")