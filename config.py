# Teacher Portal Configuration
TEACHER_CREDENTIALS = {
    "admin": "teacher123",  # Default credentials - change in production
    "teacher1": "password1",
    "teacher2": "password2"
}

# AI API Configuration
AI_PROVIDER = "gemini"  # Options: "openai" or "gemini"

# OpenAI Configuration
OPENAI_API_KEY = ""  # Set this if using OpenAI
OPENAI_MODEL = "gpt-3.5-turbo"  # or "gpt-4" for better results

# Gemini Configuration  
GEMINI_API_KEY = "your-gemini-api-key-here"  # Set this if using Gemini
GEMINI_MODEL = "gemini-1.5-flash"  # or "gemini-1.5-pro" for better results

# Legacy support (will use the provider specified above)
AI_MODEL = GEMINI_MODEL if AI_PROVIDER == "gemini" else OPENAI_MODEL

# File upload configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'docx', 'md'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size