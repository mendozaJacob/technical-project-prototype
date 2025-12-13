# 🎮 Quiz Battle: Dungeons of Knowledge - User Guide
*Updated: December 2025*

## 📥 Getting Started with the Executable

### **Step 1: Download and Run**
1. **Download** the `QuizBattle_DungeonsOfKnowledge.exe` file (approximately 8MB)
2. **Extract** if downloaded as a ZIP archive
3. **Right-click** the executable → **Properties** → **Unblock** (if applicable)
4. **Double-click** the executable file to launch
5. **Wait** 3-5 seconds for the application to start
6. **Your web browser will automatically open** to `http://127.0.0.1:5000`
7. **Ready to play!** 🚀

### **System Requirements**
- **Operating System**: Windows 10/11 (64-bit)
- **RAM**: Minimum 2GB, Recommended 4GB+
- **Storage**: 100MB free space (for temporary files)
- **Browser**: Chrome, Firefox, Edge, Safari (latest versions)
- **Internet**: Required for AI features only
- **Antivirus**: May require whitelisting the executable

---

## 👨‍🏫 Teacher Login & Access

### **Accessing Teacher Portal**
1. **Start the application** (double-click the .exe file)
2. **Navigate to** `http://127.0.0.1:5000/teacher_login` in your browser
   - OR click "Teacher Login" if available on the main page
3. **Enter teacher credentials:**
   - Username: `admin`
   - Password: `teacher123`
4. **Click "Login"** to access the teacher dashboard

### **Default Teacher Credentials**
```
Username: admin
Password: teacher123
```
⚠️ **Security Note:** Change these credentials in the [config.py](../../config.py) file for production use

### **First-Time Setup**
1. **Run the executable** for the first time
2. **Access teacher portal** to verify functionality
3. **Review and update** default settings in Teacher → Settings
4. **Import or create** initial question pools
5. **Set up student accounts** or use guest mode

---

## 🎯 Teacher Dashboard Guide

### **Main Dashboard Features**

#### **📊 Analytics & Monitoring**
- **Real-time Monitoring**: View active students and their progress
- **Analytics Dashboard**: See detailed statistics and performance data
- **Student Progress**: Track individual student advancement through levels

#### **👥 Student Management**
- **Add/Edit Students**: Create and manage student accounts
- **View Student Profiles**: See detailed student information and progress
- **Student Progress Tracking**: Monitor completion rates and scores

#### **📝 Question Management**
- **Add Questions**: Create new quiz questions with multiple choice answers
- **Edit Questions**: Modify existing questions and answers
- **Question Pools**: Organize questions by topic or difficulty
- **Import Questions**: Upload questions from files (TXT, PDF, DOCX)

#### **🎮 Level & Chapter Management**
- **Create Levels**: Design new game levels with custom questions
- **Edit Chapters**: Organize content into chapters and topics
- **Level Configuration**: Set difficulty, question count, and requirements

#### **🤖 AI Question Generation**
- **Auto-Generate Questions**: Use AI to create questions from uploaded content
- **Smart Grading**: AI-powered answer evaluation and feedback
- **Content Analysis**: Extract key concepts for question generation

### **Teacher Dashboard Navigation**

1. **📈 Analytics** - View performance statistics and reports
2. **👥 Students** - Manage student accounts and progress
3. **❓ Questions** - Create and edit quiz questions
4. **📚 Chapters** - Organize content by topics
5. **🎯 Levels** - Design and configure game levels
6. **🎱 Question Pools** - Group questions by category
7. **🤖 AI Generator** - Generate questions using AI
8. **📊 Real-time Monitoring** - Watch live student activity
9. **⚙️ Settings** - Configure game parameters

### **Quick Start Tasks for Teachers**

#### **🚀 Essential Setup (First 5 Minutes)**
1. **Login** with default credentials (`admin` / `teacher123`)
2. **Navigate to Settings** → Update game parameters as needed
3. **Check Student Management** → Add or verify student accounts
4. **Review Question Pools** → Import or create basic questions
5. **Test a Level** → Ensure everything works properly

#### **👥 Adding New Students**
1. Go to **Students** section in teacher dashboard
2. Click **"Add New Student"** button
3. Fill in required fields:
   - Student name (required)
   - Grade level (optional)
   - Unique student ID (auto-generated)
4. **Set initial progress** (optional)
5. **Save student profile**

#### **❓ Creating Questions**
1. Navigate to **Questions** section
2. Click **"Add New Question"**
3. **Enter question details:**
   - Question text (clear and concise)
   - 4 multiple choice answers (A, B, C, D)
   - Mark the correct answer
   - Assign difficulty level (1-5)
   - Choose category/chapter
4. **Preview question** before saving
5. **Save and test** in game mode

#### **🎯 Setting Up New Levels**
1. Go to **Levels** section
2. Click **"Create New Level"**
3. **Configure level parameters:**
   - Level number and display name
   - Minimum questions required (5-20 recommended)
   - Difficulty range (1-5 scale)
   - Time limits per question (10-60 seconds)
   - Experience points awarded
   - Enemy types for this level
4. **Assign questions** from pools or create new ones
5. **Test the level** before publishing to students

#### **🤖 AI Question Generation (Advanced)**
1. **Ensure internet connection** for OpenAI API access
2. Access **AI Generator** section
3. **Upload content files:**
   - Supported formats: PDF, DOCX, TXT
   - Maximum file size: 10MB
   - Content should be educational text
4. **Configure generation settings:**
   - Number of questions (1-50)
   - Difficulty level (1-5)
   - Question type (multiple choice)
   - Focus topics (optional keywords)
5. **Review AI-generated content** carefully
6. **Edit and refine** questions as needed
7. **Approve and add** to question pools

---

## 🎮 Student Experience

### **For Students (No Login Required)**
1. **Choose Character**: Select your avatar
2. **Select Level**: Pick difficulty and topic
3. **Battle Enemies**: Answer questions to defeat monsters
4. **Progress**: Advance through levels and chapters
5. **Leaderboard**: Compare scores with other players

### **Game Modes Available**
- **📚 Chapter Mode**: Progress through structured lessons
- **🎯 Level Mode**: Choose specific difficulty levels
- **♾️ Endless Mode**: Continuous challenge mode
- **📝 Test Yourself**: Practice mode with immediate feedback

---

## 🔧 Troubleshooting & FAQ

### **Common Issues & Solutions**

#### **🚫 Executable Won't Start**
**Problem:** Application doesn't launch or crashes immediately
**Solutions:**
- **Windows Defender:** Add executable to antivirus exclusions
- **Permissions:** Right-click executable → Run as Administrator
- **Storage:** Ensure 100MB+ free disk space for temporary files
- **Corrupted Download:** Re-download the executable file
- **Windows Version:** Verify Windows 10/11 compatibility
- **Missing Dependencies:** All required libraries are bundled in the executable

#### **🌐 Browser Issues**
**Problem:** Browser doesn't open automatically
**Solutions:**
- **Manual Access:** Navigate directly to `http://127.0.0.1:5000`
- **Port Conflict:** Check if port 5000 is already in use
- **Different Browser:** Try Chrome, Firefox, or Edge
- **Firewall:** Allow application through Windows Firewall
- **Local Network:** Ensure localhost access isn't blocked

#### **🔑 Login Problems**
**Problem:** Can't access teacher dashboard
**Solutions:**
- **Default Credentials:** Use exactly `admin` / `teacher123`
- **Case Sensitive:** Ensure correct capitalization
- **Browser Cache:** Clear cookies and cache, try incognito mode
- **Session Timeout:** Refresh page and login again
- **Database Issues:** Restart the application completely

#### **❓ Content Not Loading**
**Problem:** Questions, levels, or data not displaying
**Solutions:**
- **Data Files:** Ensure all JSON files are in the data/ directory
- **File Permissions:** Check read permissions on data files
- **Corrupted Data:** Restore from backup or reinstall
- **Memory Issues:** Close other applications to free RAM
- **Restart Application:** Complete restart often resolves loading issues

#### **🤖 AI Features Not Working**
**Problem:** AI question generation or grading fails
**Solutions:**
- **Internet Connection:** Verify stable internet access
- **API Configuration:** Check OpenAI API key in config.py
- **File Formats:** Ensure uploaded files are PDF, DOCX, or TXT
- **File Size:** Keep uploads under 10MB
- **API Limits:** Check OpenAI account status and usage limits

### **Performance Optimization**

#### **🚀 For Better Performance:**
- **Close unnecessary applications** (especially browsers with many tabs)
- **Use latest browser versions** (Chrome 120+, Firefox 121+, Edge 120+)
- **Ensure 4GB+ RAM** for smooth operation with AI features
- **Stable internet** for real-time monitoring and AI features
- **Regular restarts** after heavy usage sessions

#### **📊 Monitoring Performance:**
- **Task Manager:** Monitor CPU and memory usage
- **Network Usage:** Check for excessive data consumption
- **Browser Console:** Check for JavaScript errors (F12 key)
- **Application Logs:** Review console output for warnings

### **💾 Data Management**

#### **Backup Important Data:**
- **Student Progress:** Export from Student Management section
- **Custom Questions:** Backup questions.json regularly
- **Settings:** Save custom configurations
- **Generated Content:** Export AI-generated questions before major updates

#### **Regular Maintenance:**
- **Weekly:** Backup student data and custom content
- **Monthly:** Clean temporary files and restart application
- **Update Cycle:** Keep the executable updated for bug fixes

---

## � Complete Feature Reference

### **✅ Core Features**
- **🎮 Single Executable**: No installation, portable application
- **🌐 Automatic Browser Launch**: Seamless startup experience
- **👨‍🏫 Teacher Dashboard**: Comprehensive management portal
- **👥 Student Management**: Individual progress tracking
- **❓ Question Engine**: Multiple choice quiz system
- **🎯 Level Progression**: RPG-style advancement system
- **📊 Real-Time Analytics**: Live performance monitoring
- **🤖 AI Integration**: OpenAI-powered content generation
- **📁 Import/Export**: Multiple file format support
- **🏆 Leaderboards**: Competitive scoring system
- **♾️ Multiple Game Modes**: Chapter, Level, Endless, Test modes
- **💾 Data Persistence**: Automatic progress saving

### **🎓 Educational Benefits**

#### **For Students:**
- **Engaging Learning**: RPG mechanics make studying fun
- **Immediate Feedback**: Instant results and explanations
- **Progress Visualization**: Clear advancement tracking
- **Competitive Elements**: Leaderboards motivate improvement
- **Self-Paced Learning**: Multiple difficulty levels available
- **Character Customization**: Personal avatar selection

#### **For Teachers:**
- **Easy Content Creation**: Intuitive question authoring tools
- **Advanced Analytics**: Detailed performance insights
- **Real-Time Monitoring**: Live classroom oversight
- **AI-Assisted Grading**: Automated answer evaluation
- **Flexible Assessment**: Multiple question pools and difficulty levels
- **Progress Documentation**: Comprehensive student reports
- **Curriculum Integration**: Chapter-based organization system

### **📊 Technical Specifications**

#### **Application Details:**
- **File Size**: ~45-50MB executable
- **Platform**: Windows 10/11 (64-bit)
- **Runtime**: Python 3.13 (embedded)
- **Web Framework**: Flask with SocketIO
- **Database**: JSON-based file storage
- **Search Engine**: Whoosh full-text indexing
- **AI Provider**: OpenAI GPT integration
- **Browser Support**: All modern browsers

#### **Network Configuration:**
- **Local Server**: Runs on 127.0.0.1:5000
- **External Access**: Not configured by default
- **API Endpoints**: RESTful design with WebSocket support
- **Security**: Session-based authentication
- **Data Transfer**: JSON format for all communications

### **🔄 Version Information**

#### **Current Build (December 2025):**
- **Build Date**: December 12, 2025
- **Python Version**: 3.13.7
- **PyInstaller Version**: 6.17.0
- **Key Dependencies**: Flask 2.3.3, Whoosh 2.7.4, OpenAI 1.6.1

#### **Recent Improvements:**
- Enhanced AI question generation accuracy
- Improved real-time monitoring performance  
- Better error handling and user feedback
- Optimized executable size and startup time
- Updated security measures and session management

### **📞 Support & Resources**

#### **Documentation:**
- **Quick Guide**: [QUICK_GUIDE.md](QUICK_GUIDE.md)
- **Teacher Setup**: [../teacher-guides/TEACHER_SETUP.md](../teacher-guides/TEACHER_SETUP.md)  
- **API Reference**: [../technical/JSON_REFERENCE.md](../technical/JSON_REFERENCE.md)
- **Implementation Details**: [../development/IMPLEMENTATION_COMPLETE.md](../development/IMPLEMENTATION_COMPLETE.md)

#### **Getting Help:**
- **Check Documentation**: Comprehensive guides in docs/ folder
- **Review Logs**: Check console output for error messages
- **Restart Application**: Often resolves temporary issues
- **System Administrator**: Contact your IT department for infrastructure issues
- **Community Forums**: Share experiences with other educators

---

*Quiz Battle: Dungeons of Knowledge - Making education engaging through gamification*  
*Last Updated: December 12, 2025 | Build Version: 2025.12.12*