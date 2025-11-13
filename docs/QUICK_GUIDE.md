# 🚀 Quick Customization Guide

## ⚡ Most Common Changes

### 1. 📝 Add New Questions (5 minutes)
1. Open `data/questions.json`
2. Add new question at the end:
```json
{
  "id": 101,
  "q": "Your question here?",
  "answer": "correct answer",
  "keywords": ["alternative", "answers"],
  "feedback": "Explanation of the answer"
}
```
3. Update `data/levels.json` to include question ID 101

### 2. 🎨 Change Font (2 minutes)
**In ALL template files**, replace:
```html
<link href="https://fonts.googleapis.com/css2?family=MedievalSharp&display=swap" rel="stylesheet">
```
With your chosen Google Font.

**In `static/style.css`**, replace:
```css
font-family: 'MedievalSharp', cursive;
```

### 3. 🌈 Change Color Theme (10 minutes)
In `static/style.css`, find and replace:
- `#2e3d1f` → Your background color
- `#f3eac2` → Your container/text color  
- `#4b2e05` → Your border/button color

### 4. 👾 Add New Enemy (3 minutes)
1. Add to `data/enemies.json`:
```json
{
  "level": 11,
  "name": "New Enemy",
  "avatar": "🔥",
  "taunt": "Prepare to face me!",
  "range": "Q101-Q110"
}
```
2. (Optional) Add enemy image to `static/enemies/`

### 5. 🎮 Change Game Title (1 minute)
In `templates/index.html`, find and modify:
```html
<h1>Your New Game Title</h1>
```

---

## 📋 File Priority for Customization

### 🔥 High Priority (Most Often Changed)
1. `data/questions.json` - Add/edit questions
2. `static/style.css` - Visual appearance
3. `data/levels.json` - Level organization

### 🔶 Medium Priority
4. `data/enemies.json` - Enemy details
5. `templates/index.html` - Landing page
6. `templates/select_level.html` - Level descriptions

### 🔷 Low Priority (Advanced Users)
7. `app.py` - Game logic and routes
8. Other template files - Specific page layouts

---

## ⚠️ Important Notes

### Before Making Changes:
1. **Backup your files** - Copy the project folder
2. **Test after each change** - Run `python app.py` to check
3. **Validate JSON** - Use online JSON validators for data files

### Common Mistakes:
- ❌ Forgetting commas in JSON files
- ❌ Mismatched question IDs between files  
- ❌ Wrong file paths for images
- ❌ CSS syntax errors

### Testing Checklist:
- ✅ App starts without errors
- ✅ All game modes work
- ✅ Questions display correctly
- ✅ Styling looks good
- ✅ Images load properly

---

## 💡 Tips for Success

1. **Start Small** - Make one change at a time
2. **Use Browser Tools** - F12 to inspect CSS issues
3. **Keep Backups** - Before major changes
4. **Test Thoroughly** - Play through the game after changes
5. **Ask for Help** - Check the full DOCUMENTATION.md for details

---

*Ready to customize? Start with questions and work your way up! 🎯*