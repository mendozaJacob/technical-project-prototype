import json

# Check questions file
with open('data/questions.json', 'r') as f:
    questions = json.load(f)

print(f"Total questions: {len(questions)}")

# Find questions with IDs > 135 (the AI generated ones)
ai_questions = [q for q in questions if q.get('id', 0) > 135]
print(f"AI generated questions: {len(ai_questions)}")

if ai_questions:
    print("\nAI Generated Questions:")
    for q in ai_questions:
        print(f"ID {q.get('id')}: {q.get('q', 'No question')[:60]}...")
else:
    print("No AI generated questions found")

# Check the last few questions
print(f"\nLast 5 questions:")
for q in questions[-5:]:
    print(f"ID {q.get('id')}: {q.get('q', 'No question')[:60]}...")