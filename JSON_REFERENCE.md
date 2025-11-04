# 📋 JSON Data Format Reference

## 📝 questions.json Schema

```json
[
  {
    "id": 1,                    // Required: Unique integer ID
    "q": "Question text?",      // Required: The actual question
    "answer": "correct answer", // Required: Primary correct answer
    "keywords": [               // Required: Array of alternative answers
      "keyword1",
      "keyword2"
    ],
    "feedback": "Explanation"   // Required: Educational feedback text
  }
]
```

### Question Guidelines:
- **ID**: Must be unique across all questions
- **Question**: Keep under 200 characters for best display
- **Answer**: Case-insensitive, exact match expected
- **Keywords**: Alternative answers that are also correct
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

### Adding Question 101:
```json
{
  "id": 101,
  "q": "Which command shows disk usage?",
  "answer": "df -h",
  "keywords": ["df", "du", "disk usage"],
  "feedback": "The 'df -h' command displays filesystem disk space usage in human-readable format."
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
  "keywords": ["keyword"],
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

*Remember: Always validate your JSON after making changes! 🔍*