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
- [📡 Real-Time Monitoring](#-real-time-monitoring)
- [📁 Data Format Reference](#-data-format-reference)
- [🛠️ Advanced Features](#️-advanced-features)
- [� Documentation Hub](#-documentation-hub)
- [�🐛 Troubleshooting](#-troubleshooting)
- [🤝 Contributing](#-contributing)

## 🎯 Project Overview

Quiz Battle: Dungeons of Knowledge is a comprehensive educational platform that gamifies learning through a medieval RPG experience. Students battle enemies by answering technical questions correctly, progressing through levels while mastering system administration concepts.

### 🆕 Recent Updates (December 2025)
- **✅ JavaScript Syntax Fixes**: Resolved 235+ VS Code syntax errors in teacher portal
- **🔧 Enhanced Chapter Filtering**: Improved level filtering functionality with cleaner code
- **🚀 Performance Optimizations**: Eliminated console logging overhead and improved DOM handling
- **💻 Code Maintainability**: Refactored template literal mixing for better developer experience
- **🎯 Improved Error Handling**: Better separation of Jinja2 templates and JavaScript code

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
- **Diverse Question Types**: Short Answer, Multiple Choice, True/False questions
- **Intelligent Answer Matching**: Enhanced fuzzy matching for flexible responses
- **Character Customization**: Choose from 16 different avatars
- **Real-time Combat**: HP-based battle system with enemies
- **Progress Tracking**: Save and load game progress
- **Leaderboards**: Compete with other students
- **Profile Management**: Update email and password
- **Mobile Responsive**: Play on any device

### 👨‍🏫 For Teachers
- **📚 Enhanced Chapter Management System**: Organize questions into chapters with improved filtering
  - Lock/unlock chapters per game mode (Test Yourself, Level Mode, Endless Mode)
  - **New**: Improved chapter filtering with cleaner JavaScript implementation
  - Automatic question pool synchronization
  - Visual chapter cards with progress tracking
- **📡 Real-Time Student Monitoring**: Watch student answers live as they play with WebSocket technology
- **Complete Student Management**: Add, edit, and monitor students with individual/batch reset capabilities
- **Multi-Type Question Creation**: Create Short Answer, Multiple Choice, and True/False questions
- **AI-Powered Question Generation**: Upload curriculum and generate mixed question types automatically
  - Comprehensive API key validation with helpful error messages
  - Support for Gemini and OpenAI APIs
  - Automatic detection of missing or invalid API keys
- **Enhanced Answer Evaluation**: Advanced fuzzy matching with multiple validation methods
- **Advanced Settings Control**: Configure game parameters (redundant settings removed)
- **Live Performance Analytics**: Track student progress and performance in real-time
  - Click student names to view individual progress details
  - Modal popups with detailed statistics and recent activity
- **Intelligent Grading**: AI-powered answer evaluation with semantic understanding
- **Advanced Filtering**: Filter live answers by student, game mode, and correctness
- **Content Management**: Manage questions, levels, and enemies with type-based filtering
- **🔧 Improved Developer Experience**: Clean, maintainable code with resolved syntax issues

### 🤖 AI Integration
- **OpenAI GPT Integration** for intelligent question generation
- **Multi-Type Question Creation**: Automatically generates Short Answer, Multiple Choice, and True/False questions
- **Curriculum Processing** from PDF, DOCX, TXT, and MD files
- **Question Type Selection**: Choose which types of questions to generate
- **Semantic Answer Evaluation** with enhanced fuzzy matching algorithms
- **Adaptive Difficulty** based on student performance and question type complexity

### ⚠️ **AI API Limitations Warning**
> **Important:** The AI question generation features may have limited functionality due to API restrictions:
> - **Free API Keys**: Gemini and OpenAI free tiers have aggressive rate limiting and quota controls
> - **Request Throttling**: Multiple rapid requests may trigger abuse detection
> - **Daily Limits**: Free API keys have low daily token/request allowances
> - **Recommendation**: For production use, consider upgrading to paid API tiers for reliable AI functionality
> 
> The application will function normally without AI features - questions can still be created manually through the teacher portal.

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
pip install Flask==2.3.3 Werkzeug==2.3.7 requests==2.31.0 whoosh Flask-SocketIO
```

3. **Configure AI integration (optional)**
```bash
# Create config.py and add your OpenAI API key
OPENAI_API_KEY = "your-api-key-here"
AI_MODEL = "gpt-3.5-turbo"
```
> ⚠️ **Note:** Free API keys have severe limitations - expect frequent rate limiting and quota issues

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

## 📦 Building Executable

For distribution without Python installed:

### Quick Build (Recommended)
```bash
build_exe.bat
```

### Manual Build
**⚠️ Important:** Use correct Python environment and ensure data paths are fixed.

1. **Install dependencies:**
```bash
python -m pip install -r requirements.txt
python -m pip install pyinstaller
```

2. **Build executable:**
```bash
python -m PyInstaller --onefile --noconsole --add-data "data;data" --add-data "templates;templates" --add-data "static;static" --add-data "docs;docs" app.py
```

**✅ Verified Working Result:**
- Output: `dist/QuizBattle_DungeonsOfKnowledge.exe`
- Size: ~19-20 MB (includes all dependencies + data files)
- ✅ No "module not found" errors
- ✅ Levels display correctly  
- ✅ Chapters load properly
- ✅ Game fully playable

**🚨 Critical Requirements:**
- Use `python -m PyInstaller` (not `pyinstaller` directly)
- Ensure `get_resource_path()` is used for all data file access
- Include `--add-data "data;data"` to bundle data files

## 🎯 Question Types System

### 📝 Supported Question Types

**Short Answer Questions**
- Traditional text input with enhanced fuzzy matching
- Supports alternative keywords and partial matches
- Word-based similarity matching (70% overlap threshold)
- Sequence similarity matching using advanced algorithms

**Multiple Choice Questions** 
- 2-4 answer options with letter selection (A, B, C, D)
- Students can select by clicking options or typing letters
- Visual feedback for selected answers
- Supports both letter and full text matching

**True/False Questions**
- Simple boolean questions with flexible input recognition
- Accepts multiple formats: true/t/yes/y/1 and false/f/no/n/0
- Interactive true/false buttons with visual feedback
- Ideal for concept verification and quick assessments

### 🤖 Enhanced Fuzzy Matching

The advanced answer evaluation system includes:
- **Exact matching** for precise answers
- **Partial substring matching** for incomplete but correct responses
- **Word-based analysis** with configurable similarity thresholds
- **Sequence similarity** using difflib algorithms
- **Flexible input recognition** for true/false and multiple choice
- **Semantic understanding** for natural language responses

## 🎮 Game Modes

### 🗡️ Adventure Mode
- **Structure**: Progress through 10 challenging levels
- **Mechanics**: Each level has unique enemies and 10 questions
- **Goal**: Complete all levels to become a master
- **Features**: Character selection, HP management, enemy battles

### 📚 Chapter System Integration
All game modes now integrate with the chapter management system:
- **Teacher Control**: Lock/unlock chapters independently for each mode
- **Auto-Sync**: Question pools automatically update based on chapter locks
- **Flexible Learning**: Teachers can control which content is available per mode

### ♾️ Endless Mode
- **Structure**: Continuous questions until HP reaches 0
- **Mechanics**: Random questions from unlocked chapters
- **Goal**: Achieve the highest score possible
- **Features**: Progressive difficulty, extended gameplay
- **Chapter Lock**: Teachers can lock specific chapters to control question availability

### 📝 Test Yourself Mode
- **Structure**: Comprehensive exam from unlocked chapters
- **Mechanics**: Timed assessment with performance tracking
- **Goal**: Demonstrate mastery of concepts
- **Features**: Detailed results, performance analysis
- **Chapter Lock**: Teachers can lock chapters to customize test content

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
- **API Key Validation**: Comprehensive checks with helpful error messages
  - Detects missing or invalid API keys before processing
  - User-friendly instructions for obtaining API keys
  - Support for both Gemini and OpenAI APIs
- **File Upload**: Support for PDF, DOCX, TXT, and MD files
- **Question Type Selection**: Choose Short Answer, Multiple Choice, True/False, or mixed
- **Content Analysis**: AI extracts key concepts from curriculum
- **Intelligent Generation**: Creates appropriate options for Multiple Choice, proper True/False statements
- **Quality Control**: Review and approve generated questions with type-specific validation
- **Bulk Creation**: Generate multiple question types in a single operation

### 📚 Chapter Management
- **Organize Content**: Group questions into logical chapters
- **Assign Questions**: Select which questions belong to each chapter
- **Define Level Ranges**: Set which game levels use which chapter
- **Per-Mode Locks**: Independent lock control for each game mode:
  - 🔒 Test Yourself Mode
  - 🔒 Level Mode  
  - 🔒 Endless Mode
- **Auto-Sync**: Question pools automatically update based on locks
- **Visual Management**: Chapter cards with lock status and question counts

### ⚙️ Advanced Settings
**Streamlined Configuration**:
- Game mechanics (HP, damage, timing)
- Scoring systems (points, bonuses, penalties)
- Adaptive difficulty progression
- Interface customization (sounds, animations, timers, progress bars)
- System settings (debug mode, analytics, session management)
- Removed redundant settings for better clarity

### 📊 Analytics & Reporting
- **Student Performance**: Individual and class-wide statistics
- **Click-Through Details**: Click student names to view detailed progress
  - Individual statistics modal popup
  - Recent game history
  - Performance trends
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
│   ├── 📄 chapters.json      # Chapter organization (NEW)
│   ├── 📄 question_pools.json # Question pool management (NEW)
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
// Short Answer Question
{
  "id": 101,
  "q": "Which command shows disk usage?",
  "answer": "df -h",
  "type": "short_answer",
  "keywords": ["df", "du", "disk usage"],
  "feedback": "The 'df -h' command displays filesystem disk space usage."
}

// Multiple Choice Question
{
  "id": 102,
  "q": "Which command lists directory contents?",
  "answer": "ls",
  "type": "multiple_choice",
  "options": ["ls", "dir", "list", "show"],
  "feedback": "The 'ls' command lists directory contents in Linux."
}

// True/False Question
{
  "id": 103,
  "q": "Linux is an open-source operating system.",
  "answer": "true",
  "type": "true_false",
  "feedback": "Linux is indeed open-source and freely available."
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
- Choose appropriate question type for the content
- For Multiple Choice: Provide 2-4 clear, distinct options
- For True/False: Ensure statements are definitively true or false
- For Short Answer: Include alternative answer keywords for fuzzy matching
- Provide comprehensive feedback for all question types
- Test with actual students across different question types

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

### 🔄 Teacher Reset Capabilities
- **Individual Reset**: Reset specific student progress or game sessions
- **Batch Operations**: Reset multiple students simultaneously
- **Secure Confirmations**: Type "RESET" confirmations for destructive operations
- **Detailed Logging**: All reset actions tracked for accountability

## 📡 Real-Time Monitoring

### 🔴 Live Answer Streaming
**Teachers can watch student answers in real-time as they play:**

#### **Core Features**
- **📺 Instant Visibility**: See every student answer immediately upon submission
- **🎮 Multi-Mode Support**: Monitor Adventure, Test Yourself, and Endless modes
- **🎯 Performance Tracking**: Real-time accuracy rates and engagement metrics
- **👥 Student Identification**: Clear student names and avatars for easy recognition
- **⏰ Timestamp Tracking**: Precise timing of each answer submission

#### **Advanced Filtering**
- **👤 Student Filter**: Focus on specific students
- **🎮 Game Mode Filter**: View answers from specific game modes only
- **✅❌ Correctness Filter**: Show only correct or incorrect answers
- **🔄 Auto-Scroll Toggle**: Automatically scroll to newest answers or disable for review
- **🧹 Clear Display**: Reset view while preserving stored data

#### **WebSocket Technology**
- **⚡ Real-Time Updates**: No page refresh needed - answers appear instantly
- **🔒 Secure Rooms**: Teachers join authenticated WebSocket rooms
- **📊 Connection Status**: Visual indicators showing connection state
- **💪 Graceful Fallback**: System works even without WebSocket support

#### **Answer Analysis**
```
📊 Live Statistics:
• Total Answers: 247
• Correct Answers: 189
• Accuracy Rate: 76.5%
• Active Students: 23
```

#### **Usage Instructions**
1. **Access**: Teacher Dashboard → "📡 Real-Time Monitoring"
2. **Connect**: WebSocket automatically connects upon page load
3. **Monitor**: Answers stream live as students submit responses
4. **Filter**: Use dropdown filters to focus on specific data
5. **Analyze**: Watch for patterns in student responses

#### **Visual Interface**
- **🟢 Correct Answers**: Green-highlighted with checkmark indicators
- **🔴 Incorrect Answers**: Red-highlighted with X indicators
- **🎯 Game Mode Badges**: Color-coded badges for each mode
- **📏 Level Indicators**: Show Adventure mode progression
- **⏱️ Timestamps**: Precise submission times
- **🔄 New Answer Animation**: Smooth highlighting for fresh submissions

#### **Teacher Benefits**
- **🚨 Immediate Intervention**: Spot struggling students instantly
- **📈 Engagement Monitoring**: See which students are actively participating
- **❓ Question Analysis**: Identify questions that many students miss
- **🎯 Performance Assessment**: Real-time understanding of class comprehension
- **📊 Data-Driven Decisions**: Make instructional adjustments based on live feedback

### 🛠️ Technical Implementation
- **Flask-SocketIO**: Professional WebSocket integration
- **JSON Storage**: Efficient answer logging with automatic rotation
- **Secure Authentication**: Teacher-only access with session validation
- **Error Handling**: Comprehensive fallback mechanisms
- **Performance Optimized**: Handles high-frequency answer submissions

**📡 Real-time monitoring transforms traditional teaching into dynamic, responsive instruction!**

## 📁 Data Format Reference

### 📝 questions.json Schema
```json
[
  {
    "id": 1,                    // Required: Unique integer ID
    "q": "Question text?",      // Required: The actual question
    "answer": "correct answer", // Required: Primary correct answer
    "type": "short_answer",     // Required: Question type (short_answer|multiple_choice|true_false)
    "options": ["A", "B", "C"], // Required for multiple_choice: Array of answer options
    "keywords": [               // Optional: Alternative answers (mainly for short_answer)
      "keyword1", "keyword2"
    ],
    "difficulty": "medium",     // Optional: Difficulty level (easy|medium|hard)
    "feedback": "Explanation",  // Required: Educational feedback
    "ai_generated": false       // Optional: Whether question was AI-generated
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
- **Clean JavaScript Architecture**: Separated Jinja2 templates from JavaScript for better maintainability
- **Enhanced DOM Manipulation**: Safe element creation using `createElement` and `textContent`
- **Performance Optimizations**: Eliminated unnecessary console logging and improved event handling
- **Error-Free Development**: Resolved 235+ VS Code syntax errors for better developer experience
- **Modern ES6+ Features**: Updated to use arrow functions and modern JavaScript patterns
- **Template Safety**: Proper escaping and sanitization of dynamic content
- **Session Management**: Configurable timeout and security
- **Error Handling**: Graceful degradation and user feedback

### 🎯 Accessibility Features
- **Responsive Design**: Mobile-friendly interface
- **Keyboard Navigation**: Full keyboard accessibility
- **Screen Reader Support**: Semantic HTML and ARIA labels
- **High Contrast**: Readable color combinations

## � Documentation Hub

The Quiz Battle platform includes comprehensive, organized documentation for all user types:

### 🗂️ **Documentation Structure**

#### 📖 **[User Guides](docs/user-guides/)**
- **[Complete User Guide](docs/user-guides/USER_GUIDE.md)** - Comprehensive manual for students and basic setup
- **[Quick Customization Guide](docs/user-guides/QUICK_GUIDE.md)** - Fast setup and common modifications

#### 🎓 **[Teacher Guides](docs/teacher-guides/)**
- **[Teacher Setup](docs/teacher-guides/TEACHER_SETUP.md)** - Initial configuration and account setup
- **[Teacher Portal Manual](docs/teacher-guides/TEACHER_PORTAL_README.md)** - Complete dashboard features
- **[AI Question Assignment](docs/teacher-guides/AI_QUESTION_ASSIGNMENT.md)** - Automated content generation
- **[Chapter Management](docs/teacher-guides/CHAPTER_MANAGEMENT_GUIDE.md)** - Content organization
- **[Real-Time Monitoring](docs/teacher-guides/REAL_TIME_MONITORING.md)** - Live student tracking

#### ⚙️ **[Technical References](docs/technical/)**
- **[System Documentation](docs/technical/DOCUMENTATION.md)** - Architecture and development
- **[JSON Reference](docs/technical/JSON_REFERENCE.md)** - Data formats and schemas
- **[Advanced Integration](docs/technical/CHAPTER_POOL_INTEGRATION.md)** - Custom integrations

#### 🛠️ **[Development Resources](docs/development/)**
- **[Implementation Details](docs/development/IMPLEMENTATION_COMPLETE.md)** - Feature specifications
- **[Settings System](docs/development/SETTINGS_SYSTEM_FIXED.md)** - Configuration management
- **[Build Information](docs/development/BUILD_SUMMARY.md)** - Latest release details

### 🎯 **Quick Access**
- **New Users:** Start with [docs/user-guides/USER_GUIDE.md](docs/user-guides/USER_GUIDE.md)
- **Teachers:** Begin with [docs/teacher-guides/TEACHER_SETUP.md](docs/teacher-guides/TEACHER_SETUP.md)
- **Developers:** Review [docs/technical/DOCUMENTATION.md](docs/technical/DOCUMENTATION.md)
- **All Documentation:** Browse [docs/INDEX.md](docs/INDEX.md) for complete navigation

## �🐛 Troubleshooting

### 🚨 Common Issues

**App Won't Start**
- Check Python version (3.7+ required)
- Verify all dependencies installed
- Ensure no other app using port 5000

**Questions Not Displaying**
- Validate JSON syntax in data files
- Check question IDs match between files
- Verify file permissions for read/write
- Ensure question type field is valid (short_answer, multiple_choice, true_false)
- For multiple choice questions, verify options array is properly formatted

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

## 📋 Changelog

### Version 2.1.0 (December 2025)
- **🔧 Major JavaScript Refactor**: Fixed 235+ syntax errors in teacher portal
- **⚡ Performance Improvements**: Eliminated console logging overhead
- **🎯 Enhanced Chapter Filtering**: Cleaner, more maintainable filter implementation
- **💻 Developer Experience**: Better code organization and error handling
- **🛠️ Template Architecture**: Improved separation of Jinja2 and JavaScript code
- **🚀 DOM Safety**: Replaced innerHTML with safe createElement methods

### Previous Versions
- **2.0.0**: AI Question Generation, Chapter Management System
- **1.9.0**: Real-Time Student Monitoring, Advanced Analytics  
- **1.8.0**: Multi-Type Questions (Short Answer, Multiple Choice, True/False)
- **1.7.0**: Enhanced Fuzzy Matching, Student Management Portal

---

## 🎯 Quick Links

- **🎮 Start Playing**: [http://localhost:5000](http://localhost:5000)
- **👨‍🏫 Teacher Portal**: [http://localhost:5000/teacher/login](http://localhost:5000/teacher/login)
- **📡 Real-Time Monitoring**: [http://localhost:5000/teacher/real-time-monitoring](http://localhost:5000/teacher/real-time-monitoring)
- **📊 Settings Guide**: See [Settings System](#-settings-system) section
- **📝 Question Format**: See [Data Format Reference](#-data-format-reference) section
- **🔧 Customization**: See [Customization Guide](#-customization-guide) section
- **📡 Live Monitoring**: See [Real-Time Monitoring](#-real-time-monitoring) section

---

*Ready to embark on your learning adventure? May your knowledge grow strong and your battles be victorious! ⚔️📚*

---

**Built with ❤️ for education • Powered by Flask & AI • Medieval theme by design**