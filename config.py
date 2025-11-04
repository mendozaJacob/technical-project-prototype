# Teacher Portal Configuration
TEACHER_CREDENTIALS = {
    "admin": "teacher123",  # Default credentials - change in production
    "teacher1": "password1",
    "teacher2": "password2"
}

# AI API Configuration (you'll need to set these)
OPENAI_API_KEY = "your-api-key-here"  # Set this in environment variables
AI_MODEL = "gpt-3.5-turbo"  # or "gpt-4" for better results

# File upload configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'docx', 'md'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size