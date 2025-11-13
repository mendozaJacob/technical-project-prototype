# 🎮 Quiz Battle: Dungeons of Knowledge

> An Interactive Medieval-Themed Educational RPG Platform for Learning System Administration

[![Built with Flask](https://img.shields.io/badge/Built%20with-Flask-blue.svg)](https://flask.palletsprojects.com/)
[![Python 3.7+](https://img.shields.io/badge/Python-3.7%2B-green.svg)](https://www.python.org/)
[![Medieval Theme](https://img.shields.io/badge/Theme-Medieval%20RPG-purple.svg)](https://github.com/mendozaJacob/technical-project-prototype)

## 📖 Table of Contents

- [🎯 Project Overview](#-project-overview)
- [✨ Key Features](#-key-features)
- [🚀 Quick Start](#-quick-start)
- [🎮 Game Modes](#-game-modes)
- [👨‍🏫 Teacher Portal](#-teacher-portal)
- [🏗️ Project Structure](#️-project-structure)
- [🔧 Customization Guide](#-customization-guide)
- [📊 Settings System](#-settings-system)
- [🧑‍🎓 Student Management](#-student-management)
- [📁 Data Format Reference](#-data-format-reference)
- [🛠️ Advanced Features](#️-advanced-features)
- [🐛 Troubleshooting](#-troubleshooting)
- [🤝 Contributing](#-contributing)

## 🎯 Project Overview

Quiz Battle: Dungeons of Knowledge is a comprehensive educational platform that gamifies learning through a medieval RPG experience. Students battle enemies by answering technical questions correctly, progressing through levels while mastering system administration concepts.

### 🎨 Theme & Design
- **Medieval parchment aesthetic** with warm, educational colors
- **Character selection** from 16 unique avatars
- **Enemy progression** through 10+ challenging levels
- **Responsive design** that works on desktop and mobile devices

### 🧑‍🎓 Educational Focus
- **Linux system administration** commands and concepts
- **Interactive learning** through gameplay mechanics
- **Immediate feedback** with detailed explanations
- **Progress tracking** and performance analytics

## ✨ Key Features

### 🎮 For Students
- **Multiple Game Modes**: Adventure Mode, Endless Mode, Test Yourself
- **Character Customization**: Choose from 16 different avatars
- **Real-time Combat**: HP-based battle system with enemies
- **Progress Tracking**: Save and load game progress
- **Leaderboards**: Compete with other students
- **Profile Management**: Update email and password
- **Mobile Responsive**: Play on any device

### 👨‍🏫 For Teachers
- **Complete Student Management**: Add, edit, and monitor students
- **AI-Powered Question Generation**: Upload curriculum and generate questions automatically
- **Advanced Settings Control**: Configure 22+ game parameters
- **Performance Analytics**: Track student progress and performance
- **Intelligent Grading**: AI-powered answer evaluation
- **Content Management**: Manage questions, levels, and enemies

### 🤖 AI Integration
- **OpenAI GPT Integration** for question generation
- **Curriculum Processing** from PDF, DOCX, TXT, and MD files
- **Semantic Answer Evaluation** for open-ended questions
- **Adaptive Difficulty** based on student performance

## 🚀 Quick Start

### Prerequisites
- Python 3.7 or higher
- Flask framework
- Modern web browser

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/mendozaJacob/technical-project-prototype.git
cd technical-project-prototype
```

2. **Install dependencies**
```bash
pip install Flask==2.3.3 Werkzeug==2.3.7 requests==2.31.0 whoosh
```

3. **Configure AI integration (optional)**
```bash
# Create config.py and add your OpenAI API key
OPENAI_API_KEY = "your-api-key-here"
AI_MODEL = "gpt-3.5-turbo"
```

4. **Run the application**
```bash
python app.py
```

5. **Access the game**
Open your browser to `http://localhost:5000`

### First Time Setup

1. **Teacher Account**: Access `/teacher/login` with default credentials
2. **Student Management**: Add students through the teacher portal
3. **Game Configuration**: Adjust settings in the teacher dashboard
4. **Content Review**: Check questions and levels are appropriate

## 🎮 Game Modes

### 🗡️ Adventure Mode
- **Structure**: Progress through 10 challenging levels
- **Mechanics**: Each level has unique enemies and 10 questions
- **Goal**: Complete all levels to become a master
- **Features**: Character selection, HP management, enemy battles

### ♾️ Endless Mode
- **Structure**: Continuous questions until HP reaches 0
- **Mechanics**: Random questions from all difficulty levels
- **Goal**: Achieve the highest score possible
- **Features**: Progressive difficulty, extended gameplay

### 📝 Test Yourself Mode
- **Structure**: 40-question comprehensive exam
- **Mechanics**: Timed assessment with 75% pass requirement
- **Goal**: Demonstrate mastery of all concepts
- **Features**: Detailed results, performance analysis

## 👨‍🏫 Teacher Portal

### 🔐 Authentication System
- **Secure Login**: Session-based authentication
- **Role Separation**: Teachers and students have separate access
- **Session Management**: Configurable timeout periods

### 🧑‍🎓 Student Management
- **Student Accounts**: Create and manage individual student logins
- **Progress Tracking**: Monitor individual student performance
- **Profile Management**: Students can update their own profiles
- **Login Analytics**: Track student engagement and activity

### 🤖 AI Question Generator
- **File Upload**: Support for PDF, DOCX, TXT, and MD files
- **Content Analysis**: AI extracts key concepts from curriculum
- **Question Generation**: Creates diverse question types automatically
- **Quality Control**: Review and approve generated questions

### ⚙️ Advanced Settings
**22 Configurable Parameters**:
- Game mechanics (HP, damage, timing)
- Scoring systems (points, bonuses, penalties)
- Difficulty progression and adaptive features
- Interface customization (sounds, animations, themes)
- System settings (debug mode, analytics, session management)

### 📊 Analytics & Reporting
- **Student Performance**: Individual and class-wide statistics
- **Question Analysis**: Identify difficult or problematic questions
- **Engagement Metrics**: Track time spent and completion rates
- **AI Grading Accuracy**: Monitor automated grading performance

## 🏗️ Project Structure

```
📁 technical-project-prototype-main/
├── 📄 app.py                 # Main Flask application
├── 📄 config.py              # Configuration settings
├── 📄 requirements.txt       # Python dependencies
├── 📁 data/                  # Game data storage
│   ├── 📄 questions.json     # Question database
│   ├── 📄 levels.json        # Level configurations
│   ├── 📄 enemies.json       # Enemy definitions
│   ├── 📄 students.json      # Student accounts
│   ├── 📄 student_progress.json # Individual progress
│   ├── 📄 game_settings.json # Global game settings
│   └── 📄 leaderboard.json   # High scores
├── 📁 docs/                  # Documentation files
│   ├── 📄 DOCUMENTATION.md   # Complete project documentation
│   ├── 📄 JSON_REFERENCE.md  # Data format reference
│   ├── 📄 QUICK_GUIDE.md     # Quick customization guide
│   ├── 📄 TEACHER_PORTAL_README.md # Teacher portal guide
│   ├── 📄 IMPLEMENTATION_COMPLETE.md # Implementation details
│   ├── 📄 SETTINGS_SYSTEM_FIXED.md # Settings system info
│   └── 📄 TEACHER_SETUP.md   # Teacher setup instructions
├── 📁 static/                # Static assets
│   ├── 📄 style.css          # Main stylesheet
│   ├── 📁 characters/        # Character avatars
│   └── 📁 enemies/           # Enemy images
├── 📁 templates/             # HTML templates
│   ├── 📄 index.html         # Landing page
│   ├── 📄 game.html          # Game interface
│   ├── 📄 student_dashboard.html # Student dashboard
│   ├── 📄 teacher_dashboard.html # Teacher portal
│   └── 📄 ...                # Additional templates
└── 📁 uploads/               # Temporary file storage
```

## 🔧 Customization Guide

### ⚡ Quick Changes (5 minutes)

**1. Add New Questions**
```json
// In data/questions.json
{
  "id": 101,
  "q": "Which command shows disk usage?",
  "answer": "df -h",
  "keywords": ["df", "du", "disk usage"],
  "feedback": "The 'df -h' command displays filesystem disk space usage."
}
```

**2. Change Game Title**
```html
<!-- In templates/index.html -->
<div class="site-title">⚔️ Your Custom Game Title ⚔️</div>
```

**3. Modify Colors**
```css
/* In static/style.css */
:root {
  --bg-color: #2e3d1f;      /* Background */
  --container-color: #f3eac2; /* Parchment */
  --border-color: #4b2e05;   /* Borders */
}
```

### 🎨 Theme Customization

**Change Font**
1. Replace Google Fonts link in all templates
2. Update CSS font-family declarations
3. Test across all game screens

**Color Scheme**
1. Update CSS color variables
2. Test contrast ratios for accessibility
3. Ensure medieval theme consistency

**Character Assets**
1. Replace images in `static/characters/`
2. Update character selection grid
3. Maintain consistent image dimensions

### 📝 Content Management

**Question Guidelines**:
- Keep questions under 200 characters
- Provide comprehensive feedback
- Include alternative answer keywords
- Test with actual students

**Level Organization**:
- 10 questions per level recommended
- Progressive difficulty increase
- Thematic consistency within levels

**Enemy Design**:
- Match enemy difficulty to level
- Create engaging taunt messages
- Use appropriate emoji or images

## 📊 Settings System

### 🎮 Game Mechanics (5 settings)
- **Base Player HP**: Starting health points (50-200)
- **Base Enemy HP**: Enemy health points (25-150)
- **Base Damage**: Damage per correct answer (5-30)
- **Question Time Limit**: Seconds per question (15-120)
- **Questions Per Level**: Number of questions (1-20)

### 🏆 Scoring System (4 settings)
- **Points for Correct**: Points awarded for right answers
- **Points for Wrong**: Points deducted for wrong answers
- **Speed Bonus**: Extra points for fast answers
- **Level Bonus**: Bonus points for completing levels

### 📊 Difficulty & Progression (4 settings)
- **Adaptive Difficulty**: Adjust based on performance
- **Minimum Accuracy**: Required accuracy to advance (50-95%)
- **Lives System**: Enable/disable lives instead of HP
- **Maximum Lives**: Number of lives when enabled (1-10)

### 🎨 Interface & Theme (4 settings)
- **Sound Effects**: Enable audio feedback
- **Show Timer**: Display countdown timer
- **Show Progress**: Display progress indicators
- **Animation Speed**: UI animation speed (slow/normal/fast)

### 🔧 Advanced Settings (5 settings)
- **Debug Mode**: Enable debugging features
- **Analytics**: Track student performance
- **Auto Save**: Automatic progress saving
- **Session Timeout**: Minutes before session expires (15-120)
- **Timeout Behavior**: Action on question timeout (fail/skip/retry)

## 🧑‍🎓 Student Management

### 👤 Student Accounts
- **Individual Logins**: Each student has unique credentials
- **Profile Management**: Students can update email and password
- **Progress Tracking**: Automatic save/load functionality
- **Performance Analytics**: Detailed statistics for each student

### 📈 Progress Tracking
- **Game Mode Progress**: Separate tracking for each mode
- **Question History**: Record of all answered questions
- **Performance Metrics**: Accuracy, speed, and improvement trends
- **Achievement System**: Level completions and high scores

### 🔐 Authentication Features
- **Secure Sessions**: Session-based authentication
- **Login Prompts**: Automatic prompts for unauthenticated users
- **Profile Updates**: Email and password change functionality
- **Activity Logging**: Track login times and session duration

## 📁 Data Format Reference

### 📝 questions.json Schema
```json
[
  {
    "id": 1,                    // Required: Unique integer ID
    "q": "Question text?",      // Required: The actual question
    "answer": "correct answer", // Required: Primary correct answer
    "keywords": [               // Required: Alternative answers
      "keyword1", "keyword2"
    ],
    "feedback": "Explanation"   // Required: Educational feedback
  }
]
```

### 🎮 levels.json Schema
```json
[
  {
    "level": 1,                 // Required: Level number
    "questions": [1,2,3,4,5]    // Required: Array of question IDs
  }
]
```

### 👾 enemies.json Schema
```json
[
  {
    "level": 1,                     // Required: Corresponding level
    "name": "Enemy Name",           // Required: Display name
    "avatar": "🧙‍♂️",                // Required: Emoji or character
    "taunt": "Taunt message",       // Required: What enemy says
    "range": "Q1–Q10",             // Optional: Question range info
    "image": "enemies/enemy1.png"  // Optional: Image file path
  }
]
```

### 🧑‍🎓 students.json Schema
```json
[
  {
    "id": "0001",                   // Required: Unique student ID
    "username": "student1",         // Required: Login username
    "password": "hashedpassword",   // Required: Hashed password
    "full_name": "Student Name",    // Required: Display name
    "email": "student@email.com",   // Required: Contact email
    "created_date": "2024-01-01",   // Required: Account creation
    "last_login": "2024-01-15",     // Optional: Last login time
    "status": "active"              // Required: Account status
  }
]
```

## 🛠️ Advanced Features

### 🤖 AI Integration
- **Question Generation**: Upload curriculum files for automatic question creation
- **Semantic Grading**: Intelligent evaluation of open-ended answers
- **Content Analysis**: Extract key concepts from educational materials
- **Adaptive Learning**: Adjust difficulty based on student performance

### 📊 Analytics System
- **Event Tracking**: Comprehensive logging of student interactions
- **Performance Metrics**: Detailed statistics and trend analysis
- **Question Analytics**: Identify problematic or effective questions
- **Class Overview**: Teacher dashboard with class-wide insights

### 🔧 Technical Features
- **Search Functionality**: Full-text search across questions
- **Auto-save System**: Automatic progress preservation
- **Session Management**: Configurable timeout and security
- **Error Handling**: Graceful degradation and user feedback

### 🎯 Accessibility Features
- **Responsive Design**: Mobile-friendly interface
- **Keyboard Navigation**: Full keyboard accessibility
- **Screen Reader Support**: Semantic HTML and ARIA labels
- **High Contrast**: Readable color combinations

## 🐛 Troubleshooting

### 🚨 Common Issues

**App Won't Start**
- Check Python version (3.7+ required)
- Verify all dependencies installed
- Ensure no other app using port 5000

**Questions Not Displaying**
- Validate JSON syntax in data files
- Check question IDs match between files
- Verify file permissions for read/write

**Images Not Loading**
- Confirm image files exist in static directories
- Check file naming conventions
- Verify image formats (PNG, JPG, GIF)

**Settings Not Saving**
- Check write permissions on data/game_settings.json
- Verify JSON format validity
- Ensure teacher authentication is working

**AI Features Not Working**
- Configure OpenAI API key in config.py
- Check API key has sufficient credits
- Verify internet connection for API calls

### 🔍 Debug Mode
Enable debug mode in teacher settings for:
- Detailed error messages
- Game state inspection
- Performance monitoring
- Development tools

### 📋 Validation Checklist
- ✅ App starts without errors
- ✅ All game modes functional
- ✅ Student login/registration works
- ✅ Teacher portal accessible
- ✅ Questions display correctly
- ✅ Images and styling load properly
- ✅ Settings save and apply correctly

## 🤝 Contributing

### 🛠️ Development Setup
1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Submit a pull request

### 📝 Contribution Guidelines
- Follow existing code style
- Add tests for new features
- Update documentation
- Test across different browsers

### 🐛 Bug Reports
Include:
- Python version and OS
- Steps to reproduce
- Expected vs actual behavior
- Error messages or screenshots

### ✨ Feature Requests
Consider:
- Educational value
- User experience impact
- Technical feasibility
- Maintenance requirements

---

## 📄 License

This project is open source and available under the MIT License.

## � Additional Documentation

For detailed information, check the `docs/` folder:
- **📄 DOCUMENTATION.md** - Complete technical documentation
- **📄 JSON_REFERENCE.md** - Data format schemas and examples
- **📄 QUICK_GUIDE.md** - Fast customization guide
- **📄 TEACHER_PORTAL_README.md** - Teacher portal setup and usage
- **📄 IMPLEMENTATION_COMPLETE.md** - Implementation details and features
- **📄 SETTINGS_SYSTEM_FIXED.md** - Settings system configuration
- **📄 TEACHER_SETUP.md** - Teacher account setup instructions

## �📞 Support

For help and support:
1. Check this documentation and the `docs/` folder
2. Review existing GitHub issues
3. Create a new issue with details
4. Join our community discussions

---

## 🎯 Quick Links

- **🎮 Start Playing**: [http://localhost:5000](http://localhost:5000)
- **👨‍🏫 Teacher Portal**: [http://localhost:5000/teacher/login](http://localhost:5000/teacher/login)
- **📊 Settings Guide**: See [Settings System](#-settings-system) section
- **📝 Question Format**: See [Data Format Reference](#-data-format-reference) section
- **🔧 Customization**: See [Customization Guide](#-customization-guide) section

---

*Ready to embark on your learning adventure? May your knowledge grow strong and your battles be victorious! ⚔️📚*

---

**Built with ❤️ for education • Powered by Flask & AI • Medieval theme by design**