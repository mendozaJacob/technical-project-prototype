# Teacher Portal Setup & Usage Guide

## Overview
The Teacher Portal is an AI-powered management system that allows educators to efficiently manage questions, generate new content, and analyze student performance in the Medieval RPG Learning Game.

## 🚀 Quick Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure AI Integration
1. Copy `config.py` and update your settings:
   - Add your OpenAI API key
   - Set up teacher credentials
   - Configure AI model preferences

2. Example configuration:
```python
# AI Configuration
OPENAI_API_KEY = "your-actual-api-key-here"
AI_MODEL = "gpt-3.5-turbo"  # or "gpt-4"
AI_MAX_TOKENS = 2000

# Teacher Credentials
TEACHER_CREDENTIALS = {
    "teacher1": "password123",
    "admin": "admin456"
}
```

### 3. Create Upload Directory
```bash
mkdir uploads
```

## 🎯 Teacher Portal Features

### Dashboard
- View student statistics
- Monitor AI-generated questions
- Quick access to all tools

### AI Question Generator
**Upload curriculum files and automatically generate questions!**

**Supported file formats:**
- PDF documents
- Word documents (.docx)
- Text files (.txt)
- Markdown files (.md)

**How it works:**
1. Upload your curriculum document
2. Specify topic, difficulty level, and question count
3. AI analyzes the content and generates contextual questions
4. Review and select questions to add to your question bank

### AI Grading System
**Intelligent answer evaluation for open-ended questions!**

**Features:**
- Semantic understanding of student answers
- Confidence scoring
- Detailed explanations for grading decisions
- Customizable grading prompts
- Test mode for fine-tuning

**Configuration options:**
- Choose AI model (GPT-3.5 or GPT-4)
- Set confidence threshold
- Custom grading prompts
- Enable/disable AI grading

## 🔧 Usage Instructions

### Accessing the Teacher Portal
1. Navigate to `/teacher/login`
2. Use your configured credentials
3. Access the dashboard at `/teacher/dashboard`

### Generating Questions from Curriculum
1. Go to "AI Generator" from the dashboard
2. Upload your curriculum file (PDF, DOCX, TXT, or MD)
3. Fill in the form:
   - **Topic**: Subject area (e.g., "Medieval History")
   - **Difficulty**: Easy, Medium, or Hard
   - **Question Count**: Number of questions to generate (1-20)
   - **Question Types**: Select which types to generate (Short Answer, Multiple Choice, True/False)
   - **Context**: Additional context for question generation
4. Click "Generate Questions"
5. Review the generated questions (including options for multiple choice)
6. Select which questions to add to your question bank
7. Click "Save Selected Questions"

### Setting Up AI Grading
1. Go to "AI Grading" from the dashboard
2. Configure your settings:
   - **AI Model**: Choose between GPT-3.5 (faster, cheaper) or GPT-4 (more accurate)
   - **Confidence Threshold**: Minimum confidence level to auto-grade (0-100%)
   - **Custom Prompt**: Optional custom instructions for the AI grader
3. Test the system with sample questions
4. Enable AI grading when satisfied with results

### Managing Existing Questions
- **Question Library**: View all questions with type-specific indicators
- **Type-based Filtering**: Filter questions by Short Answer, Multiple Choice, or True/False
- **Visual Type Badges**: Color-coded badges for easy identification
- **Edit Capabilities**: Modify question text, answers, options, and feedback
- **Type Conversion**: Change question types while preserving content
- **AI Generation Tracking**: Track which questions were AI-generated vs manual
- **Bulk Operations**: Select and manage multiple questions simultaneously

## 🧠 AI Integration Details

### Question Generation Process
1. **Text Extraction**: Content is extracted from uploaded files
2. **Context Analysis**: AI analyzes the curriculum content for key concepts
3. **Question Type Selection**: Teachers choose which types to generate
4. **Intelligent Question Creation**: AI generates contextually appropriate questions:
   - **Short Answer**: With alternative keywords for flexible grading
   - **Multiple Choice**: With plausible distractors and correct answers
   - **True/False**: With definitively true or false statements
5. **Answer Validation**: AI ensures answers match question types correctly
6. **Quality Control**: Each question includes comprehensive feedback and difficulty rating

### AI Grading Process
1. **Answer Analysis**: AI compares student answer to expected answer
2. **Semantic Understanding**: Goes beyond exact matches
3. **Confidence Scoring**: Provides confidence level for each grade
4. **Explanation**: Explains reasoning for the grade

### Supported Question Types
- **Short Answer**: Open-ended text responses with enhanced fuzzy matching
  - Supports alternative keywords and partial matches
  - Word-based similarity analysis with configurable thresholds
  - Intelligent semantic understanding for natural responses
- **Multiple Choice**: Interactive A/B/C/D format questions
  - 2-4 customizable answer options
  - Students can click buttons or type letter choices
  - Visual feedback for selected answers
  - AI generates appropriate distractors automatically
- **True/False**: Binary choice questions with flexible input
  - Accepts multiple input formats (true/t/yes/y/1, false/f/no/n/0)
  - Interactive true/false buttons with visual confirmation
  - Perfect for concept verification and quick assessments

## 🔒 Security & Privacy

### Authentication
- Session-based authentication
- Password-protected access
- Automatic session timeout

### Data Protection
- Uploaded files are temporarily stored and automatically deleted
- No curriculum content is permanently stored
- AI API calls are made securely

### Access Control
- Students cannot access teacher portal
- Teachers can only access their authorized features
- Separate authentication from student game

## 🛠️ Troubleshooting

### Common Issues

**"OpenAI API Key not configured"**
- Update `config.py` with your actual API key
- Ensure the key has sufficient credits

**"Error uploading file"**
- Check file format (PDF, DOCX, TXT, MD only)
- Ensure file size is under the limit
- Verify upload directory exists

**"AI grading not working"**
- Check API key configuration
- Verify internet connection
- Check AI model availability

**"Questions not saving"**
- Ensure write permissions on data/questions.json
- Check JSON format validity
- Verify search index rebuild

### Getting Help
1. Check the error messages in the browser console
2. Review the Flask application logs
3. Verify all dependencies are installed
4. Ensure config.py is properly configured

## 📊 Analytics & Reporting

### Student Performance Tracking
- Average scores across all students
- Question difficulty analysis
- AI grading accuracy metrics

### Question Bank Statistics
- Total questions in database
- AI-generated vs manually created questions
- Most frequently missed questions

## 🔄 Updates & Maintenance

### Adding New Teachers
1. Update `TEACHER_CREDENTIALS` in `config.py`
2. Restart the application

### Updating AI Models
1. Modify `AI_MODEL` in `config.py`
2. Test with sample questions
3. Update confidence thresholds if needed

### Backing Up Data
- Regularly backup `data/questions.json`
- Save `data/leaderboard.json` for student records
- Keep config.py secure and backed up

## 🎮 Integration with Game

The teacher portal seamlessly integrates with the main game:
- New questions appear immediately in gameplay
- AI grading works for all question types
- Student progress is tracked automatically
- Leaderboard data informs teaching decisions

## 📚 Best Practices

### Question Generation Tips
1. **Content Preparation**: Use clear, well-structured curriculum documents
2. **Type Selection**: Choose question types appropriate for your content:
   - Short Answer for complex concepts requiring explanation
   - Multiple Choice for factual recall and concept identification
   - True/False for verification of key principles
3. **Context Specificity**: Provide specific topics and learning objectives
4. **Quality Review**: Always review generated questions, especially:
   - Multiple choice options for clarity and plausibility
   - True/false statements for accuracy and definitiveness
   - Short answer keywords for comprehensive coverage
5. **Balanced Mix**: Combine different question types for engaging gameplay
6. **Difficulty Progression**: Mix difficulty levels within each question type

### AI Grading Guidelines
1. Start with high confidence thresholds (80%+)
2. Test with known good/bad answers
3. Adjust thresholds based on subject matter
4. Use custom prompts for specialized topics

### Curriculum Management
1. Organize files by subject/topic
2. Use descriptive filenames
3. Update questions regularly
4. Archive old content appropriately

---

**Happy Teaching! 🎓⚔️**

For technical support or feature requests, please refer to the main project documentation or contact your system administrator.