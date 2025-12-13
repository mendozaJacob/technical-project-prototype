# 📋 JSON Data Format Reference

## 📝 questions.json Schema

```json
[
  {
    "id": 1,                    // Required: Unique integer ID
    "q": "Question text?",      // Required: The actual question
    "answer": "correct answer", // Required: Primary correct answer
    "type": "short_answer",     // Required: Question type (short_answer|multiple_choice|true_false)
    "options": ["A", "B", "C"], // Required for multiple_choice: Array of answer options
    "keywords": [               // Optional: Alternative answers (mainly for short_answer)
      "keyword1",
      "keyword2"
    ],
    "difficulty": "medium",     // Optional: Difficulty level (easy|medium|hard)
    "feedback": "Explanation",  // Required: Educational feedback text
    "ai_generated": false       // Optional: Whether question was AI-generated
  }
]
```

### Question Types:

**Short Answer Questions:**
```json
{
  "id": 1,
  "q": "Which command lists directory contents?",
  "answer": "ls",
  "type": "short_answer",
  "keywords": ["ls", "list", "dir"],
  "feedback": "The 'ls' command lists directory contents."
}
```

**Multiple Choice Questions:**
```json
{
  "id": 2,
  "q": "Which command shows disk usage?",
  "answer": "df -h",
  "type": "multiple_choice",
  "options": ["df -h", "du -h", "ls -l", "ps aux"],
  "feedback": "The 'df -h' command displays filesystem disk usage."
}
```

**True/False Questions:**
```json
{
  "id": 3,
  "q": "Linux is an open-source operating system.",
  "answer": "true",
  "type": "true_false",
  "feedback": "Linux is indeed open-source and freely available."
}
```

### Question Guidelines:
- **ID**: Must be unique across all questions
- **Question**: Keep under 200 characters for best display
- **Type**: Must be "short_answer", "multiple_choice", or "true_false"
- **Answer**: 
  - Short Answer: Any text, enhanced fuzzy matching will handle variations
  - Multiple Choice: Must exactly match one of the options
  - True/False: Must be "true" or "false" (case-insensitive)
- **Options**: Required for multiple_choice (2-4 options recommended)
- **Keywords**: Alternative answers for short_answer questions (supports fuzzy matching)
- **Feedback**: Educational explanation, can include HTML tags

---

## 🎮 levels.json Schema

```json
[
  {
    "level": 1,                 // Required: Level number (1-10)
    "questions": [1,2,3,4,5]    // Required: Array of question IDs
  }
]
```

### Level Guidelines:
- **Level**: Sequential numbering recommended
- **Questions**: Exactly 10 questions per level recommended
- **Question IDs**: Must exist in questions.json

---

## 👾 enemies.json Schema

```json
[
  {
    "level": 1,                     // Required: Corresponding level number
    "name": "Enemy Name",           // Required: Display name
    "avatar": "🧙‍♂️",                // Required: Emoji or character
    "taunt": "Taunt message",       // Required: What enemy says
    "range": "Q1–Q10",             // Optional: Question range info
    "image": "enemies/enemy1.png"  // Optional: Image file path
  }
]
```

### Enemy Guidelines:
- **Level**: Must match level in levels.json
- **Name**: Keep under 30 characters
- **Avatar**: Single emoji works best
- **Taunt**: Keep under 100 characters
- **Image**: Place in static/enemies/ directory

---

## 🏆 leaderboard.json Schema (Auto-generated)

```json
[
  {
    "player": "Player Name",        // Player's chosen name
    "score": 150,                   // Final score achieved
    "time": 45.67,                  // Time taken in seconds
    "correct_answers": 8,           // Number of correct answers
    "wrong_answers": 2              // Number of wrong answers
  }
]
```

### Notes:
- This file is automatically created and managed
- No manual editing required
- Sorted by score (highest first)

---

## ✅ Validation Rules

### JSON Syntax:
- All strings must be in double quotes
- Arrays use square brackets []
- Objects use curly braces {}
- No trailing commas allowed
- Use escape characters for special characters

### Data Integrity:
- Question IDs must be unique
- Question types must be valid (short_answer, multiple_choice, true_false)
- Multiple choice questions must have options array with 2-4 items
- Multiple choice answers must exactly match one of the options
- True/false answers must be "true" or "false"
- Level question IDs must exist in questions.json
- Enemy levels must correspond to existing levels
- Image paths must point to existing files

### Testing Your JSON:
1. Use online JSON validators (jsonlint.com)
2. Run the app after changes
3. Check browser console for errors
4. Test all game modes

---

## 🛠️ Example Additions

### Adding Question 101 (Short Answer):
```json
{
  "id": 101,
  "q": "Which command shows disk usage?",
  "answer": "df -h",
  "type": "short_answer",
  "keywords": ["df", "du", "disk usage"],
  "difficulty": "medium",
  "feedback": "The 'df -h' command displays filesystem disk space usage in human-readable format."
}
```

### Adding Question 102 (Multiple Choice):
```json
{
  "id": 102,
  "q": "Which command creates a directory?",
  "answer": "mkdir",
  "type": "multiple_choice",
  "options": ["mkdir", "rmdir", "ls", "cd"],
  "difficulty": "easy",
  "feedback": "The 'mkdir' command creates new directories."
}
```

### Adding Question 103 (True/False):
```json
{
  "id": 103,
  "q": "The 'rm' command can delete directories.",
  "answer": "false",
  "type": "true_false",
  "difficulty": "medium",
  "feedback": "The 'rm' command deletes files. Use 'rm -r' or 'rmdir' for directories."
}
```

### Adding Level 11:
```json
{
  "level": 11,
  "questions": [101, 102, 103, 104, 105, 106, 107, 108, 109, 110]
}
```

### Adding Enemy for Level 11:
```json
{
  "level": 11,
  "name": "Storage Master",
  "avatar": "💾",
  "taunt": "Your disk knowledge ends here!",
  "range": "Q101–Q110"
}
```

---

## ⚠️ Common JSON Errors

### Syntax Errors:
```json
// ❌ Wrong (trailing comma)
{
  "id": 1,
  "q": "Question?",
}

// ✅ Correct
{
  "id": 1,
  "q": "Question?"
}
```

### Missing Fields:
```json
// ❌ Wrong (missing required fields)
{
  "id": 1,
  "q": "Question?"
}

// ✅ Correct (all required fields)
{
  "id": 1,
  "q": "Question?",
  "answer": "answer",
  "type": "short_answer",
  "keywords": ["keyword"],
  "feedback": "explanation"
}
```

### Question Type Errors:
```json
// ❌ Wrong (multiple choice without options)
{
  "id": 2,
  "q": "Which is correct?",
  "answer": "A",
  "type": "multiple_choice",
  "feedback": "explanation"
}

// ✅ Correct (multiple choice with options)
{
  "id": 2,
  "q": "Which is correct?",
  "answer": "Option A",
  "type": "multiple_choice",
  "options": ["Option A", "Option B", "Option C"],
  "feedback": "explanation"
}
```

### Invalid Characters:
```json
// ❌ Wrong (unescaped quotes)
{
  "feedback": "Use "quotes" carefully"
}

// ✅ Correct (escaped quotes)
{
  "feedback": "Use \"quotes\" carefully"
}
```

---

## 🧠 Enhanced Fuzzy Matching System

### Short Answer Matching:
The system uses multiple matching techniques:
- **Exact Match**: Direct string comparison
- **Keyword Match**: Checks alternative answers in keywords array
- **Partial Match**: Substring matching for longer answers
- **Fuzzy Match**: Sequence similarity matching (80% threshold)
- **Word Match**: Word-based analysis (70% overlap threshold)

### Multiple Choice Matching:
- Accepts option letters (A, B, C, D)
- Accepts full option text
- Case-insensitive matching

### True/False Matching:
Accepts multiple input formats:
- **True**: true, t, yes, y, 1, correct, right
- **False**: false, f, no, n, 0, incorrect, wrong

---

*Remember: Always validate your JSON after making changes! 🔍*