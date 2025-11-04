# 📚 Technical Project Prototype - Complete Documentation

## 🎯 Project Overview
This is a medieval-themed educational RPG game built with Flask that teaches Linux system administration through interactive questions and battles. Players fight enemies by answering technical questions correctly.

---

## 📁 Project Structure

### 🏗️ Root Files
- **`app.py`** - Main Flask application with all routes and game logic
- **`DOCUMENTATION.md`** - This documentation file

### 📂 Data Directory (`data/`)
Contains all game data in JSON format:

#### `questions.json` 📝
Contains all the questions used in the game.
```json
{
  "id": 1,
  "q": "Configure your Host Name to server1.example.com",
  "answer": "hostnamectl set-hostname server1.example.com",
  "keywords": ["hostname", "hostnamectl"],
  "feedback": "hostnamectl is the systemd command for managing the system hostname..."
}
```

#### `levels.json` 🎮
Defines game levels and which questions belong to each level.
```json
{
  "level": 1,
  "questions": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
}
```

#### `enemies.json` 👾
Contains enemy data for each level.
```json
{
  "level": 1,
  "name": "Novice Gnome",
  "avatar": "🧙‍♂️",
  "taunt": "Let's see if you even know what 'ls' does!",
  "range": "Q1–Q10"
}
```

#### `leaderboard.json` 🏆
Stores player scores and statistics (auto-generated).

### 🎨 Static Directory (`static/`)

#### `style.css` 🎨
Main stylesheet containing:
- Medieval theme colors and fonts
- Layout styles for all pages
- Button and form styling
- HP bar animations
- Responsive design

#### `characters/` 👤
Contains character avatar images:
- `character1.png` through `character16.png`
- Used for player selection

#### `enemies/` 👾
Contains enemy avatar images:
- Various enemy images matching `enemies.json`
- Named after enemy types

### 🌐 Templates Directory (`templates/`)
Contains all HTML templates:

#### Core Game Templates
- **`index.html`** - Main landing page
- **`select_level.html`** - Level selection screen
- **`choose_character.html`** - Character selection
- **`game.html`** - Main battle interface
- **`feedback.html`** - Shows results after each question
- **`result.html`** - End-of-level results

#### Game Mode Templates
- **`endless.html`** - Endless mode gameplay
- **`endless_setup.html`** - Endless mode setup page
- **`endless_result.html`** - Endless mode results
- **`test_yourself.html`** - Test mode gameplay
- **`test_yourself_result.html`** - Test mode results

#### Utility Templates
- **`leaderboard.html`** - High scores display
- **`search.html`** - Question search functionality
- **`howto.html`** - Game instructions

---

## 🔧 How to Customize the Game

### 📝 Adding/Modifying Questions

#### 1. Edit `data/questions.json`
Each question follows this structure:
```json
{
  "id": 101,
  "q": "Your question text here",
  "answer": "exact answer expected",
  "keywords": ["alternative", "answers", "accepted"],
  "feedback": "Educational explanation shown after answering"
}
```

**Required Fields:**
- `id`: Unique number for the question
- `q`: The question text
- `answer`: Primary correct answer (case-insensitive)
- `keywords`: Array of alternative acceptable answers
- `feedback`: Explanation shown after answering

#### 2. Update `data/levels.json`
Assign questions to levels:
```json
{
  "level": 11,
  "questions": [101, 102, 103, 104, 105, 106, 107, 108, 109, 110]
}
```

### 🎨 Changing Fonts and Styling

#### 1. Font Customization
The game uses **MedievalSharp** font from Google Fonts. To change:

**Option A: Different Google Font**
1. Go to [Google Fonts](https://fonts.google.com)
2. Choose your font
3. In each HTML template, replace:
```html
<link href="https://fonts.googleapis.com/css2?family=MedievalSharp&display=swap" rel="stylesheet">
```
With your new font link.

4. In `static/style.css`, replace all instances of:
```css
font-family: 'MedievalSharp', cursive;
```

**Option B: System Fonts**
Remove Google Fonts links and use:
```css
font-family: Arial, sans-serif; /* or any system font */
```

#### 2. Color Scheme Customization
Main color variables in `static/style.css`:
```css
/* Medieval Theme Colors */
background: #2e3d1f;        /* Dark green background */
container: #f3eac2;         /* Parchment background */
borders: #4b2e05;           /* Dark brown borders */
text: #f3eac2;              /* Light text */
buttons: #4b2e05;           /* Button background */
```

To change themes, replace these colors throughout the CSS file.

### 👾 Adding New Enemies

#### 1. Edit `data/enemies.json`
```json
{
  "level": 11,
  "name": "Your Enemy Name",
  "avatar": "🔥",
  "taunt": "Your enemy's taunt message",
  "range": "Q101–Q110"
}
```

#### 2. Add Enemy Image (Optional)
Place image in `static/enemies/` with a descriptive filename.

### 🎮 Adding New Game Modes

#### 1. Create Route in `app.py`
```python
@app.route('/new_mode', methods=['GET', 'POST'])
def new_mode():
    # Your game logic here
    return render_template('new_mode.html')
```

#### 2. Create Template
Create `templates/new_mode.html` following the existing template structure.

#### 3. Add Navigation
Update `templates/index.html` to include a link to your new mode.

### 🏆 Customizing Scoring System

In `app.py`, find the scoring logic:
```python
# Time-based scoring
if time_taken <= 5:
    damage = 20
    score = 20
elif time_taken <= 15:
    damage = 10
    score = 10
else:
    damage = 5
    score = 5
```

Modify these values to change the scoring system.

---

## 🚀 Running the Game

### Prerequisites
- Python 3.7+
- Flask
- Whoosh (for search functionality)

### Installation
1. Clone the repository
2. Install dependencies:
```bash
pip install flask whoosh
```
3. Run the application:
```bash
python app.py
```
4. Open browser to `http://localhost:5000`

---

## 🎯 Game Features

### 🎮 Game Modes
1. **Level Mode**: Progress through 10 structured levels
2. **Endless Mode**: Continuous questions until HP reaches 0
3. **Test Yourself**: 40-question timed exam (75% pass rate)

### 💪 Game Mechanics
- **HP System**: Players and enemies have health points
- **Timer**: Questions have time limits
- **Scoring**: Based on speed and accuracy
- **Feedback**: Educational explanations for each question
- **Character Selection**: 16 different avatars
- **Leaderboard**: Track high scores

### 🎨 Visual Features
- Medieval parchment theme
- Animated HP bars
- Character and enemy avatars
- Responsive design
- Fantasy fonts and icons

---

## 🛠️ Advanced Customization

### Database Integration
To use a database instead of JSON:
1. Install SQLAlchemy: `pip install flask-sqlalchemy`
2. Create models in `app.py`
3. Replace JSON file operations with database queries

### User Authentication
To add user accounts:
1. Install Flask-Login: `pip install flask-login`
2. Create user model and authentication routes
3. Protect game routes with login requirements

### Multiplayer Features
To add multiplayer:
1. Install Flask-SocketIO: `pip install flask-socketio`
2. Create real-time game rooms
3. Sync game state between players

---

## 🐛 Troubleshooting

### Common Issues

**1. Questions not displaying**
- Check `data/questions.json` syntax
- Ensure question IDs match `levels.json`

**2. Images not loading**
- Verify image files exist in `static/` directories
- Check file naming conventions

**3. Styling issues**
- Clear browser cache
- Check CSS syntax in `static/style.css`

**4. Search not working**
- Delete `indexdir` folder and restart app
- Check Whoosh installation

### Debug Mode
Enable debug mode by setting:
```python
app.run(debug=True)
```

---

## 📄 License
This project is open source and available under the MIT License.

---

## 🤝 Contributing
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

---

## 📞 Support
For questions or issues:
1. Check this documentation
2. Review existing GitHub issues
3. Create a new issue with detailed description

---

*Happy coding and may your Linux skills grow strong! ⚔️🐧*