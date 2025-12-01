# ------------------- ENDLESS MODE -------------------
# (Moved below app initialization)
# This code ensures Flask and Whoosh are installed before importing them, preventing runtime errors
import subprocess
import sys
import os
import json
import time
import requests
import hashlib
import difflib
from datetime import datetime
from functools import wraps
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room
from whoosh.fields import Schema, TEXT, ID
from whoosh import index
from config import TEACHER_CREDENTIALS, AI_PROVIDER, OPENAI_API_KEY, GEMINI_API_KEY, OPENAI_MODEL, GEMINI_MODEL, AI_MODEL, UPLOAD_FOLDER, ALLOWED_EXTENSIONS, MAX_CONTENT_LENGTH
import threading

# Constants
LEADERBOARD_FILE = "data/leaderboard.json"
GUEST_LEADERBOARD_FILE = "data/guest_leaderboard.json"
CHAPTERS_FILE = "data/chapters.json"

# Load game settings at startup
def load_initial_settings():
    """Load initial game settings or use defaults"""
    try:
        settings_file = 'data/game_settings.json'
        with open(settings_file, 'r', encoding='utf-8') as f:
            settings = json.load(f)
        return settings
    except (FileNotFoundError, json.JSONDecodeError):
        # Create default settings file if it doesn't exist
        default_settings = {
            'base_player_hp': 100,
            'base_enemy_hp': 50,
            'base_damage': 10,
            'question_time_limit': 30,
            'questions_per_level': 10
        }
        try:
            os.makedirs('data', exist_ok=True)
            with open('data/game_settings.json', 'w', encoding='utf-8') as f:
                json.dump(default_settings, f, indent=2)
        except Exception:
            pass
        return default_settings

# Initialize settings
initial_settings = load_initial_settings()
BASE_DAMAGE = initial_settings.get('base_damage', 10)
BASE_ENEMY_HP = initial_settings.get('base_enemy_hp', 50)
LEVEL_TIME_LIMIT = initial_settings.get('question_time_limit', 30)

# Function to generate dynamic enemy taunts based on question
def generate_enemy_taunt(question, enemy_name):
    """Generate a dynamic taunt based on the question content"""
    question_text = question.get('q', '').lower()
    keywords = question.get('keywords', [])
    
    # Extract key topics from question
    if isinstance(keywords, str):
        keywords = [k.strip().lower() for k in keywords.split(',')]
    else:
        keywords = [str(k).strip().lower() for k in keywords]
    
    # Topic-based taunts
    taunt_templates = {
        'ls': [
            "Can you even list a directory?",
            "Let's see if you know what 'ls' does!",
            "Basic commands? This should be easy... or not!"
        ],
        'cd': [
            "Lost in the filesystem already?",
            "Can you navigate directories?",
            "Where do you think you're going?"
        ],
        'chmod': [
            "Permissions confuse you, don't they?",
            "Can you handle file permissions?",
            "Let's test your permission knowledge!"
        ],
        'systemctl': [
            "Service management is my domain!",
            "Can you control system services?",
            "Let's see your systemctl skills!"
        ],
        'firewall': [
            "Your firewall knowledge is weak!",
            "Can you protect this system?",
            "Let's test your security skills!"
        ],
        'user': [
            "User management is tricky, isn't it?",
            "Can you handle users and groups?",
            "Let's see if you can manage users!"
        ],
        'network': [
            "Networking will be your downfall!",
            "Can you configure network settings?",
            "Let's test your network knowledge!"
        ],
        'mount': [
            "Can you mount filesystems?",
            "Storage management is complex!",
            "Let's see your mounting skills!"
        ],
        'selinux': [
            "SELinux is too advanced for you!",
            "Can you handle security contexts?",
            "Security-Enhanced Linux will defeat you!"
        ],
        'lvm': [
            "Logical volumes will confuse you!",
            "Can you manage LVM?",
            "Storage management is my specialty!"
        ],
        'cron': [
            "Can you schedule tasks?",
            "Time-based jobs are tricky!",
            "Let's test your automation skills!"
        ],
        'package': [
            "Package management is complex!",
            "Can you install software?",
            "Let's see your package skills!"
        ],
        'grep': [
            "Can you search through text?",
            "Let's test your pattern matching!",
            "Grep will be your challenge!"
        ],
        'find': [
            "Can you find files?",
            "Let's see your search skills!",
            "File searching will defeat you!"
        ],
        'tar': [
            "Archiving is too complex for you!",
            "Can you handle tar archives?",
            "Let's test your compression knowledge!"
        ],
        'dns': [
            "DNS will confuse you!",
            "Can you resolve hostnames?",
            "Let's test your name resolution skills!"
        ],
        'boot': [
            "Boot processes are tricky!",
            "Can you fix boot issues?",
            "System startup will challenge you!"
        ]
    }
    
    # Find matching topic
    for keyword in keywords:
        for topic, taunts in taunt_templates.items():
            if topic in keyword or topic in question_text:
                import random
                return random.choice(taunts)
    
    # Check question text for topics
    for topic, taunts in taunt_templates.items():
        if topic in question_text:
            import random
            return random.choice(taunts)
    
    # Generic taunts based on enemy name
    generic_taunts = [
        f"{enemy_name} challenges your knowledge!",
        "This question will test your skills!",
        "Can you answer this correctly?",
        "Let's see what you know!",
        "Prove your expertise!"
    ]
    
    import random
    return random.choice(generic_taunts)

# Define the schema for the Whoosh search index
schema = Schema(
    id=ID(stored=True, unique=True),
    question=TEXT(stored=True),
    answer=TEXT(stored=True),
    keywords=TEXT(stored=True)
)

# Create or open the Whoosh index directory
def create_or_open_index():
    """Open the Whoosh index if valid; otherwise recreate it."""
    try:
        if not os.path.exists("indexdir"):
            os.mkdir("indexdir")
            return index.create_in("indexdir", schema)
        try:
            return index.open_dir("indexdir")
        except Exception as e:
            print(f"Whoosh index open failed: {e}. Recreating indexdir...")
            try:
                # Remove the corrupted indexdir and recreate
                import shutil
                shutil.rmtree("indexdir")
            except Exception:
                pass
            os.mkdir("indexdir")
            return index.create_in("indexdir", schema)
    except Exception as e:
        print(f"Unexpected error creating/opening indexdir: {e}")
        raise

ix = create_or_open_index()

# Initialize the Flask app
app = Flask(__name__)
import copy

app.secret_key = "unix_rpg_secret"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# Initialize Flask-SocketIO
try:
    socketio = SocketIO(app, cors_allowed_origins="*")
except Exception as e:
    print(f"Warning: SocketIO initialization failed: {e}")
    socketio = None

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.before_request
def check_session_timeout():
    """Check if session has timed out based on settings"""
    settings = get_current_game_settings()
    session_timeout_minutes = settings.get('session_timeout', 30)
    
    # Skip timeout check for certain routes
    excluded_routes = ['static', 'teacher_login', 'teacher_logout']
    if request.endpoint in excluded_routes:
        return
    
    # Check if user has activity timestamp
    if 'last_activity' in session:
        last_activity = session['last_activity']
        current_time = time.time()
        timeout_seconds = session_timeout_minutes * 60
        
        if current_time - last_activity > timeout_seconds:
            # Session timed out - clear session and redirect
            session.clear()
            flash(f'Your session timed out after {session_timeout_minutes} minutes of inactivity.', 'warning')
            return redirect(url_for('index'))
    
    # Update last activity timestamp
    session['last_activity'] = time.time()

# Teacher authentication decorator
def teacher_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('teacher_logged_in'):
            return redirect(url_for('teacher_login'))
        return f(*args, **kwargs)
    return decorated_function

# Helper function to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# AI Integration Functions
def extract_json_from_response(response):
    """Extract JSON from AI response, handling markdown code blocks and truncation"""
    import re
    
    # If the response contains markdown code blocks, extract the JSON
    json_pattern = r'```(?:json)?\s*(\[.*\]|\{.*\})\s*```'
    match = re.search(json_pattern, response, re.DOTALL)
    
    if match:
        return match.group(1).strip()
    
    # For JSON arrays, find the opening [ and matching closing ]
    start_idx = response.find('[')
    if start_idx != -1:
        bracket_count = 0
        for i, char in enumerate(response[start_idx:], start_idx):
            if char == '[':
                bracket_count += 1
            elif char == ']':
                bracket_count -= 1
                if bracket_count == 0:
                    return response[start_idx:i+1].strip()
    
    # For JSON objects, find the opening { and matching closing }
    start_idx = response.find('{')
    if start_idx != -1:
        brace_count = 0
        for i, char in enumerate(response[start_idx:], start_idx):
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0:
                    return response[start_idx:i+1].strip()
    
    # If no JSON structure found, return the response as-is
    return response.strip()

def fix_incomplete_json(json_str):
    """Attempt to fix incomplete JSON by adding missing closing brackets/braces"""
    json_str = json_str.strip()
    
    # Count opening and closing brackets/braces
    open_brackets = json_str.count('[')
    close_brackets = json_str.count(']')
    open_braces = json_str.count('{')
    close_braces = json_str.count('}')
    
    # Add missing closing brackets
    while close_brackets < open_brackets:
        json_str += ']'
        close_brackets += 1
    
    # Add missing closing braces
    while close_braces < open_braces:
        json_str += '}'
        close_braces += 1
    
    # If the JSON ends with a comma, try to remove it
    if json_str.rstrip().endswith(','):
        json_str = json_str.rstrip()[:-1]
    
    return json_str

def call_ai_api(prompt, max_tokens=1000):
    """Call AI API (OpenAI or Gemini) with error handling"""
    if AI_PROVIDER == "gemini":
        return call_gemini_api(prompt, max_tokens)
    elif AI_PROVIDER == "openai":
        return call_openai_api(prompt, max_tokens)
    else:
        return {"error": "Invalid AI provider configured"}

def is_ai_configured():
    """Check if AI API key is properly configured"""
    if AI_PROVIDER == "gemini":
        return bool(GEMINI_API_KEY and GEMINI_API_KEY.strip() and GEMINI_API_KEY != 'your-gemini-api-key-here' and len(GEMINI_API_KEY) > 10)
    elif AI_PROVIDER == "openai":
        return bool(OPENAI_API_KEY and OPENAI_API_KEY.strip() and OPENAI_API_KEY != 'your-openai-api-key-here' and len(OPENAI_API_KEY) > 10)
    return False

def get_ai_config_error_message():
    """Get user-friendly error message for missing AI configuration"""
    if AI_PROVIDER == "gemini":
        return "Gemini API key not configured. Please set GEMINI_API_KEY in config.py. Get a free key at https://makersuite.google.com/app/apikey"
    elif AI_PROVIDER == "openai":
        return "OpenAI API key not configured. Please set OPENAI_API_KEY in config.py. Get a key at https://platform.openai.com/api-keys"
    return "AI provider not configured properly in config.py"

def call_openai_api(prompt, max_tokens=1000):
    """Call OpenAI API with error handling"""
    try:
        headers = {
            'Authorization': f'Bearer {OPENAI_API_KEY}',
            'Content-Type': 'application/json',
        }
        data = {
            'model': OPENAI_MODEL,
            'messages': [{'role': 'user', 'content': prompt}],
            'max_tokens': max_tokens,
            'temperature': 0.7
        }
        response = requests.post('https://api.openai.com/v1/chat/completions', 
                               headers=headers, json=data, timeout=60)
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        else:
            return f"Error: {response.status_code} - {response.text}"
    except Exception as e:
        return f"Error calling OpenAI API: {str(e)}"

def call_gemini_api(prompt, max_tokens=1000):
    """Call Google Gemini API with error handling"""
    try:
        if not GEMINI_API_KEY or GEMINI_API_KEY == 'your-gemini-api-key-here':
            return "Gemini API Error: API key not configured. Please set GEMINI_API_KEY in config.py"
        
        headers = {
            'Content-Type': 'application/json'
        }
        
        # Gemini API endpoint
        url = f'https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}'
        
        data = {
            'contents': [{
                'parts': [{'text': prompt}]
            }],
            'generationConfig': {
                'maxOutputTokens': max_tokens,
                'temperature': 0.7
            }
        }
        
        print(f"DEBUG: Calling Gemini API with model: {GEMINI_MODEL}")
        print(f"DEBUG: API Key configured: {bool(GEMINI_API_KEY and len(GEMINI_API_KEY) > 20)}")
        print(f"DEBUG: Max tokens requested: {max_tokens}")
        
        response = requests.post(url, headers=headers, json=data, timeout=60)
        
        print(f"DEBUG: Gemini API response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"DEBUG: Full Gemini response structure: {json.dumps(result, indent=2)[:500]}")
            
            if 'candidates' in result and len(result['candidates']) > 0:
                candidate = result['candidates'][0]
                
                # Check if response was blocked
                if 'finishReason' in candidate and candidate['finishReason'] != 'STOP':
                    return f"Gemini API Error: Response blocked or incomplete (reason: {candidate.get('finishReason', 'unknown')})"
                
                if 'content' in candidate and 'parts' in candidate['content']:
                    response_text = candidate['content']['parts'][0]['text']
                    print(f"DEBUG: Response length: {len(response_text)} characters")
                    print(f"DEBUG: Response preview: {response_text[:200]}")
                    return response_text
                else:
                    print(f"DEBUG: Unexpected candidate structure: {candidate}")
                    return "Gemini API Error: Response missing content or parts"
            else:
                print(f"DEBUG: No candidates in response: {result}")
                return f"Gemini API Error: No response generated. Full response: {json.dumps(result)[:300]}"
        else:
            error_details = response.text
            print(f"DEBUG: Gemini API Error Details: {error_details}")
            
            if response.status_code == 400:
                return "Gemini API Error: Invalid API key or request format. Please check your API key and try again."
            elif response.status_code == 403:
                return "Gemini API Error: API key doesn't have permission or quota exceeded."
            elif response.status_code == 429:
                return "Gemini API Error: Rate limit exceeded. Please try again later."
            else:
                return f"Gemini API Error: {response.status_code} - {error_details}"
            
    except Exception as e:
        print(f"DEBUG: Exception in call_gemini_api: {str(e)}")
        return f"Error calling Gemini API: {str(e)}"

def extract_text_from_file(file_path):
    """Extract text content from uploaded files"""
    try:
        if file_path.endswith('.txt') or file_path.endswith('.md'):
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        elif file_path.endswith('.pdf'):
            # You would need to install PyPDF2: pip install PyPDF2
            try:
                import PyPDF2
                with open(file_path, 'rb') as f:
                    reader = PyPDF2.PdfReader(f)
                    text = ""
                    for page in reader.pages:
                        text += page.extract_text()
                    return text
            except ImportError:
                return "PDF support requires PyPDF2. Install with: pip install PyPDF2"
        elif file_path.endswith('.docx'):
            # You would need to install python-docx: pip install python-docx
            try:
                from docx import Document
                doc = Document(file_path)
                text = ""
                for paragraph in doc.paragraphs:
                    text += paragraph.text + "\n"
                return text
            except ImportError:
                return "DOCX support requires python-docx. Install with: pip install python-docx"
        else:
            return "Unsupported file format"
    except Exception as e:
        return f"Error reading file: {str(e)}"

def generate_questions_with_ai(content, topic, difficulty, question_count, context="", question_types=None):
    """Generate questions using AI based on content"""
    
    # Check if AI is configured
    if not is_ai_configured():
        return {"error": get_ai_config_error_message()}
    
    # Default question types if none specified
    if question_types is None:
        question_types = ["short_answer", "multiple_choice", "true_false"]
    
    # Calculate appropriate content length based on question count
    # More questions need more tokens for response, so reduce content accordingly
    base_content_limit = 6000
    content_limit = max(2000, base_content_limit - (question_count * 200))
    
    # Truncate content if needed
    if len(content) > content_limit:
        content = content[:content_limit] + "\n[Content truncated for AI processing...]"
    
    question_types_str = ", ".join(question_types)
    
    prompt = f"""Based on the following educational content about {topic}, generate EXACTLY {question_count} {difficulty}-level questions.

Content:
{content}

Additional Context: {context}

Generate a mix of question types from: {question_types_str}

Generate questions in this EXACT JSON format (no deviations):
[
    {{
        "q": "Question text here?",
        "answer": "correct answer",
        "keywords": ["alternative1", "alternative2"],
        "feedback": "Educational explanation",
        "type": "short_answer|multiple_choice|true_false",
        "options": ["option1", "option2", "option3", "option4"]
    }}
]

CRITICAL REQUIREMENTS:
- Return EXACTLY {question_count} questions in the array
- Each question must have fields: q, answer, keywords, feedback, type
- For multiple_choice questions: include "options" array with 2-4 choices, answer must match one option exactly
- For true_false questions: answer must be "true" or "false", no options needed
- For short_answer questions: include keywords array for alternative answers, no options needed
- Keep answers concise (under 50 words)
- Keep feedback brief (under 100 words)
- Focus on {difficulty} difficulty level
- Questions should test understanding of {topic}
- Return ONLY the JSON array, no other text
- Do NOT use markdown code blocks
- Ensure valid JSON with proper commas and brackets

Start response with [ and end with ]"""
    
    response = call_ai_api(prompt, max_tokens=5000)
    try:
        # Extract JSON from response (handles markdown code blocks)
        clean_json = extract_json_from_response(response)
        
        # Try to fix incomplete JSON
        fixed_json = fix_incomplete_json(clean_json)
        
        print(f"DEBUG: Original response length: {len(response)}")
        print(f"DEBUG: Extracted JSON length: {len(clean_json)}")
        print(f"DEBUG: Fixed JSON: {fixed_json[:200]}...")
        
        questions_data = json.loads(fixed_json)
        return questions_data
    except json.JSONDecodeError as e:
        # If not valid JSON, return error with more details
        print(f"DEBUG: JSON Parse Error at position {e.pos}: {str(e)}")
        print(f"DEBUG: Problematic JSON section: {response[max(0, e.pos-50):e.pos+50]}")
        return {"error": f"AI returned invalid JSON: {response[:500]}... | Parse error: {str(e)}"}

def grade_answer_with_ai(question, correct_answer, student_answer, confidence_threshold=80):
    """Use AI to grade student answers with semantic understanding"""
    # Check if AI is configured
    if not is_ai_configured():
        return {
            "correct": False,
            "confidence": 0,
            "explanation": "AI grading not available - API key not configured"
        }
    
    prompt = f"""
    Grade this student answer using semantic understanding:
    
    Question: {question}
    Expected Answer: {correct_answer}
    Student Answer: {student_answer}
    
    Evaluate if the student answer is semantically correct, even if worded differently.
    Consider synonyms, alternative phrasings, and equivalent commands/concepts.
    
    Respond in this JSON format:
    {{
        "correct": true/false,
        "confidence": 0-100,
        "explanation": "Brief explanation of your decision"
    }}
    
    Be generous with partial credit for answers that show understanding.
    
    IMPORTANT: Return ONLY the JSON object. Do not use markdown code blocks. Do not include any explanatory text. Just the raw JSON object.
    """
    
    response = call_ai_api(prompt, max_tokens=200)
    
    # Check if response is an error message
    if isinstance(response, str) and ('error' in response.lower() or 'api' in response.lower()):
        return {
            "correct": False,
            "confidence": 0,
            "explanation": f"AI grading error: {response[:100]}"
        }
    
    try:
        # Extract JSON from response (handles markdown code blocks)
        clean_json = extract_json_from_response(response)
        result = json.loads(clean_json)
        # Apply confidence threshold
        if result.get('confidence', 0) < confidence_threshold:
            result['correct'] = False
            result['explanation'] += f" (Below {confidence_threshold}% confidence threshold)"
        return result
    except json.JSONDecodeError as e:
        return {
            "correct": False,
            "confidence": 0,
            "explanation": "Error: Could not parse AI response"
        }

# Helper function for fuzzy answer checking
def check_answer_fuzzy(user_answer, question_data, similarity_threshold=0.8):
    """
    Check user answer against correct answer and alternatives with fuzzy matching.
    Returns tuple: (is_correct, feedback_type, similarity_score)
    """
    question_type = question_data.get('type', 'short_answer')
    user_answer = user_answer.strip()
    correct_answer = question_data.get("answer", "").strip()
    
    # Handle different question types
    if question_type == 'true_false':
        # Normalize true/false answers
        user_normalized = normalize_true_false_answer(user_answer)
        correct_normalized = normalize_true_false_answer(correct_answer)
        
        if user_normalized == correct_normalized:
            return True, "Correct!", 1.0
        else:
            return False, "Incorrect", 0
    
    elif question_type == 'multiple_choice':
        # For multiple choice, check exact match with correct answer or option labels
        user_answer_lower = user_answer.lower().strip()
        correct_answer_lower = correct_answer.lower().strip()
        
        # Check exact match
        if user_answer_lower == correct_answer_lower:
            return True, "Correct choice!", 1.0
        
        # Check if user entered option letter (a, b, c, d)
        options = question_data.get('options', [])
        if len(user_answer) == 1 and user_answer.lower() in 'abcd':
            option_index = ord(user_answer.lower()) - ord('a')
            if 0 <= option_index < len(options):
                if options[option_index].lower().strip() == correct_answer_lower:
                    return True, "Correct choice!", 1.0
        
        # Check if user typed the full option text
        for option in options:
            if option.lower().strip() == user_answer_lower:
                if option.lower().strip() == correct_answer_lower:
                    return True, "Correct choice!", 1.0
        
        return False, "Incorrect choice", 0
    
    else:  # short_answer (default) - use enhanced fuzzy matching
        user_answer = user_answer.lower().strip()
        correct_answer = correct_answer.lower().strip()
        
        # Check exact match with correct answer
        if user_answer == correct_answer:
            return True, "Exact match!", 1.0
        
        # Check exact match with keywords (alternatives)
        keywords = question_data.get("keywords", [])
        if isinstance(keywords, str):
            keywords = [k.strip().lower() for k in keywords.split(',') if k.strip()]
        else:
            keywords = [str(k).strip().lower() for k in keywords]
        
        if user_answer in keywords:
            return True, "Correct alternative!", 1.0
        
        # Enhanced fuzzy matching for short answers
        # 1. Check for partial matches (substring)
        if len(user_answer) > 3:  # Only for longer answers
            if user_answer in correct_answer or correct_answer in user_answer:
                return True, "Partial match!", 0.8
            
            # Check partial matches with keywords
            for keyword in keywords:
                if user_answer in keyword or keyword in user_answer:
                    return True, f"Partial match with '{keyword}'!", 0.8
        
        # 2. Fuzzy matching with correct answer
        correct_similarity = difflib.SequenceMatcher(None, user_answer, correct_answer).ratio()
        if correct_similarity > similarity_threshold:
            return True, "Close enough to correct answer!", correct_similarity
        
        # 3. Fuzzy matching with alternatives
        best_similarity = 0
        best_match = ""
        for keyword in keywords:
            similarity = difflib.SequenceMatcher(None, user_answer, keyword).ratio()
            if similarity > best_similarity:
                best_similarity = similarity
                best_match = keyword
        
        if best_similarity > similarity_threshold:
            return True, f"Close enough to '{best_match}'!", best_similarity
        
        # 4. Word-based fuzzy matching (split into words)
        user_words = set(user_answer.split())
        correct_words = set(correct_answer.split())
        
        if user_words and correct_words:
            word_overlap = len(user_words.intersection(correct_words)) / len(correct_words)
            if word_overlap >= 0.7:  # 70% word overlap
                return True, "Word-based match!", word_overlap
        
        return False, "Incorrect", 0

def normalize_true_false_answer(answer):
    """Normalize true/false answers to handle various inputs"""
    answer_lower = answer.lower().strip()
    
    # True variations
    if answer_lower in ['true', 't', 'yes', 'y', '1', 'correct', 'right']:
        return 'true'
    
    # False variations
    if answer_lower in ['false', 'f', 'no', 'n', '0', 'incorrect', 'wrong']:
        return 'false'
    
    return answer_lower

# Helper function to save leaderboard data
def save_leaderboard(player_name, score, total_time, correct_answers, wrong_answers, game_mode="adventure", level=None):
    # Save to student leaderboard if it's a logged-in student
    if session.get('is_student') and session.get('student_id'):
        # Get actual student name from students.json instead of relying on player_name
        student_id = session.get('student_id')
        students = load_students()
        student = next((s for s in students if s['id'] == student_id), None)
        
        # Use student's full name if available, otherwise use the passed player_name
        if student and 'full_name' in student:
            player_name = student['full_name']
        elif session.get('student_name'):
            player_name = session.get('student_name')
        
        print(f"Saving student leaderboard data: {player_name}, mode: {game_mode}, level: {level}")
        
        record = {
            "player": player_name,
            "student_id": student_id,
            "score": score,
            "time": round(total_time, 2),
            "correct_answers": correct_answers,
            "wrong_answers": wrong_answers,
            "game_mode": game_mode,
            "date": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Add level for adventure mode
        if game_mode == "adventure" and level is not None:
            record["level"] = level
        
        try:
            with open(LEADERBOARD_FILE, "r", encoding="utf-8") as f:
                leaderboard = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            leaderboard = []

        leaderboard.append(record)

        with open(LEADERBOARD_FILE, "w", encoding="utf-8") as f:
            json.dump(leaderboard, f, indent=4)
    
    # Save to guest leaderboard if it's a guest player (not a student)
    else:
        print(f"Saving guest leaderboard data: {player_name}, mode: {game_mode}, level: {level}")
        
        record = {
            "player": player_name,
            "score": score,
            "time": round(total_time, 2),
            "correct_answers": correct_answers,
            "wrong_answers": wrong_answers,
            "game_mode": game_mode,
            "date": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Add level for adventure mode
        if game_mode == "adventure" and level is not None:
            record["level"] = level
        
        try:
            with open(GUEST_LEADERBOARD_FILE, "r", encoding="utf-8") as f:
                guest_leaderboard = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            guest_leaderboard = []

        guest_leaderboard.append(record)

        with open(GUEST_LEADERBOARD_FILE, "w", encoding="utf-8") as f:
            json.dump(guest_leaderboard, f, indent=4)

def load_leaderboard():
    """Load leaderboard data from file"""
    try:
        with open(LEADERBOARD_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def reset_test_yourself_session():
    """Completely reset Test Yourself mode session data"""
    test_keys = ['test_question_ids', 'test_q_index', 'test_correct', 
                'test_start_time', 'test_time_limit', 'test_user_answers']
    for key in test_keys:
        session.pop(key, None)

def reset_endless_mode_session():
    """Completely reset Endless mode session data"""
    endless_keys = ['endless_score', 'endless_hp', 'endless_streak', 'endless_highest_streak',
                   'endless_total_answered', 'endless_correct', 'endless_wrong', 'endless_start_time',
                   'endless_score_initialized', 'endless_question_start', 'endless_current_question',
                   'endless_feedback_list']
    for key in endless_keys:
        session.pop(key, None)

# Auto-save functionality
def log_analytics_event(event_type, data=None):
    """Log analytics event if analytics are enabled"""
    settings = get_current_game_settings()
    if not settings.get('analytics_enabled', True):
        return
    
    try:
        analytics_data = {
            'timestamp': time.time(),
            'event_type': event_type,
            'player_name': session.get('player_name', 'Anonymous'),
            'session_id': session.get('_id', 'unknown'),
            'data': data or {}
        }
        
        # Append to analytics file
        analytics_file = 'data/analytics.json'
        analytics_log = []
        
        # Load existing analytics
        try:
            with open(analytics_file, 'r', encoding='utf-8') as f:
                analytics_log = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            analytics_log = []
        
        analytics_log.append(analytics_data)
        
        # Keep only last 1000 events to prevent file from growing too large
        if len(analytics_log) > 1000:
            analytics_log = analytics_log[-1000:]
        
        # Save analytics
        os.makedirs('data', exist_ok=True)
        with open(analytics_file, 'w', encoding='utf-8') as f:
            json.dump(analytics_log, f, indent=2)
            
    except Exception as e:
        print(f"Analytics logging failed: {e}")

def log_student_answer(student_id, student_name, question_id, question_text, student_answer, correct_answer, is_correct, game_mode, level=None):
    """Log student answers in real-time and notify teachers via WebSocket"""
    try:
        # Create answer log entry
        answer_log = {
            'timestamp': datetime.now().isoformat(),
            'student_id': student_id,
            'student_name': student_name,
            'question_id': question_id,
            'question_text': question_text[:100] + '...' if len(question_text) > 100 else question_text,
            'student_answer': student_answer,
            'correct_answer': correct_answer,
            'is_correct': is_correct,
            'game_mode': game_mode,
            'level': level
        }
        
        # Load existing answer logs
        try:
            with open('data/student_answers_log.json', 'r') as f:
                answers_data = json.load(f)
        except FileNotFoundError:
            answers_data = []
        
        # Add new answer log
        answers_data.append(answer_log)
        
        # Keep only last 500 answers to prevent file from growing too large
        if len(answers_data) > 500:
            answers_data = answers_data[-500:]
        
        # Save updated answer logs
        os.makedirs('data', exist_ok=True)
        with open('data/student_answers_log.json', 'w') as f:
            json.dump(answers_data, f, indent=2)
        
        # Emit real-time update to teachers (only if socketio is available)
        try:
            socketio.emit('student_answer', answer_log, room='teachers')
        except:
            pass  # SocketIO not available, skip real-time update
        
    except Exception as e:
        print(f"Error logging student answer: {e}")

def auto_save_progress():
    """Auto-save player progress if enabled in settings"""
    settings = get_current_game_settings()
    if not settings.get('auto_save', True):
        return
    
    # Only save if we have meaningful progress to save
    if not session.get('player_name') or not session.get('selected_level'):
        return
    
    try:
        progress_data = {
            'player_name': session.get('player_name', 'Anonymous'),
            'selected_level': session.get('selected_level'),
            'score': session.get('score', 0),
            'player_hp': session.get('player_hp', 100),
            'enemy_hp': session.get('enemy_hp', 50),
            'q_index': session.get('q_index', 0),
            'correct_answers': session.get('correct_answers', 0),
            'wrong_answers': session.get('wrong_answers', 0),
            'highest_unlocked': session.get('highest_unlocked', 1),
            'level_completed': session.get('level_completed', False),
            'character': session.get('character'),
            'timestamp': time.time()
        }
        
        # Save to auto-save file
        auto_save_file = f"data/autosave_{session.get('player_name', 'anonymous')}.json"
        os.makedirs('data', exist_ok=True)
        with open(auto_save_file, 'w', encoding='utf-8') as f:
            json.dump(progress_data, f, indent=2)
            
        print(f"Auto-saved progress for {session.get('player_name')}")
        
    except Exception as e:
        print(f"Auto-save failed: {e}")

def load_auto_save_progress(player_name):
    """Load auto-saved progress for a player"""
    try:
        auto_save_file = f"data/autosave_{player_name}.json"
        if not os.path.exists(auto_save_file):
            return None
            
        with open(auto_save_file, 'r', encoding='utf-8') as f:
            progress_data = json.load(f)
            
        # Check if save is recent (within 24 hours)
        if time.time() - progress_data.get('timestamp', 0) > 86400:
            return None
            
        return progress_data
        
    except Exception as e:
        print(f"Failed to load auto-save: {e}")
        return None

# Define the function to get questions for a specific level
def get_questions_for_level(level_number, levels):
    level_info = next((lvl for lvl in levels if lvl["level"] == level_number), None)
    if level_info:
        base_questions = [q for q in questions if q.get("id") in level_info["questions"]]
        
        # Filter by chapter if a specific chapter is selected
        if 'selected_chapter' in session:
            try:
                chapters_data = load_chapters()
                selected_chapter = next((ch for ch in chapters_data.get("chapters", []) 
                                       if ch.get("id") == session['selected_chapter']), None)
                if selected_chapter:
                    chapter_question_ids = set(selected_chapter.get("question_ids", []))
                    base_questions = [q for q in base_questions if q.get("id") in chapter_question_ids]
            except Exception as e:
                print(f"Error filtering by chapter: {e}")
        
        # Apply adaptive difficulty if enabled
        settings = get_current_game_settings()
        if settings.get('adaptive_difficulty', False):
            return apply_adaptive_difficulty(base_questions, level_number)
        return base_questions
    return []

def apply_adaptive_difficulty(base_questions, level_number):
    """Adjust question difficulty based on player performance"""
    # Calculate player's recent accuracy
    correct = session.get('correct_answers', 0)
    wrong = session.get('wrong_answers', 0)
    total = correct + wrong
    
    if total == 0:
        return base_questions  # No performance data yet
    
    accuracy = correct / total
    
    # Adjust difficulty based on performance
    if accuracy > 0.8:  # Player doing very well - increase difficulty
        # Try to get harder questions from higher levels
        try:
            with open("data/levels.json", "r", encoding="utf-8") as f:
                all_levels = json.load(f)
            
            harder_questions = []
            for lvl in all_levels:
                if lvl["level"] > level_number:
                    harder_questions.extend([q for q in questions if q.get("id") in lvl["questions"]])
            
            if harder_questions:
                # Mix 70% base questions with 30% harder questions
                base_count = int(len(base_questions) * 0.7)
                hard_count = min(len(harder_questions), len(base_questions) - base_count)
                return base_questions[:base_count] + random.sample(harder_questions, hard_count)
                
        except Exception:
            pass
            
    elif accuracy < 0.5:  # Player struggling - decrease difficulty
        # Try to get easier questions from lower levels
        try:
            with open("data/levels.json", "r", encoding="utf-8") as f:
                all_levels = json.load(f)
            
            easier_questions = []
            for lvl in all_levels:
                if lvl["level"] < level_number:
                    easier_questions.extend([q for q in questions if q.get("id") in lvl["questions"]])
            
            if easier_questions:
                # Mix 70% base questions with 30% easier questions
                base_count = int(len(base_questions) * 0.7)
                easy_count = min(len(easier_questions), len(base_questions) - base_count)
                return base_questions[:base_count] + random.sample(easier_questions, easy_count)
                
        except Exception:
            pass
    
    return base_questions  # No adjustment needed or possible


# Route for level selection
@app.route('/select_level', methods=['GET', 'POST'])
def select_level():
    try:
        with open("data/levels.json", "r", encoding="utf-8") as f:
            levels = json.load(f)
    except Exception:
        levels = []
    
    # Load chapters for level mode
    chapters_data = load_chapters()
    all_chapters = sorted(chapters_data.get("chapters", []), key=lambda x: x.get("order", 0))
    
    # Group levels by chapters
    chapter_levels = {}
    for chapter in all_chapters:
        chapter_id = chapter.get('id')
        level_range = chapter.get('level_range', [])
        chapter_levels[chapter_id] = {
            'chapter': chapter,
            'levels': [l for l in levels if l.get('level') in level_range]
        }

    # Determine highest unlocked level (simple: highest completed in session, or 1 if none)
    highest_unlocked = session.get('highest_unlocked', 1)
    # Optionally, you could use leaderboard or persistent storage for this

    if request.method == 'POST':
        selected_level = int(request.form.get('level', 1))
        selected_chapter = request.form.get('chapter_id')
        if selected_chapter:
            session['selected_chapter'] = int(selected_chapter)
        session['selected_level'] = selected_level
        # Reset session variables for a new game
        settings = get_current_game_settings()
        session['score'] = 0
        session['player_hp'] = settings['base_player_hp']
        session['enemy_level'] = selected_level
        # Set enemy HP to the current setting
        session['enemy_hp'] = settings['base_enemy_hp']
        
        # Ensure HP values are properly set and not zero
        if session['player_hp'] <= 0:
            session['player_hp'] = settings['base_player_hp']
        if session['enemy_hp'] <= 0:
            session['enemy_hp'] = settings['base_enemy_hp']
        
        # Log level selection
        log_analytics_event('level_selected', {
            'level': selected_level,
            'player_hp': settings['base_player_hp'],
            'enemy_hp': settings['base_enemy_hp']
        })
        

        session['q_index'] = 0
        session['feedback'] = None
        session['correct_answers'] = 0
        session['wrong_answers'] = 0
        session["level_start_time"] = time.time()
        session["game_start_time"] = time.time()
        session['level_completed'] = False
        session['enemy_defeated'] = False  # Reset enemy defeated status for new level
        session['current_timer'] = settings.get('question_time_limit', 30)  # Use configurable time limit
        
        # Initialize enemy progression index based on selected level and current progress
        # Only reset to novice if playing level 1 or if no enemy index exists
        try:
            current_enemy_index = session.get('enemy_index')
            
            # If no enemy index exists, start with novice
            # Only reset to novice for level 1 if player hasn't progressed yet
            if current_enemy_index is None or (selected_level == 1 and current_enemy_index == 0):
                novice_idx = 0
                try:
                    with open('data/enemies.json', encoding='utf-8') as ef:
                        enemies_list = json.load(ef)
                    # Look for an enemy by name or level that indicates the novice gnome
                    for i, e in enumerate(enemies_list):
                        name = str(e.get('name', '')).strip().lower()
                        level = e.get('level')
                        if name == 'novice gnome' or level == 1:
                            novice_idx = i
                            break
                except Exception:
                    # If we can't read the file, default to index 0
                    novice_idx = 0
                session['enemy_index'] = int(novice_idx)
            else:
                # Set enemy to match the selected level
                try:
                    with open('data/enemies.json', encoding='utf-8') as ef:
                        enemies_list = json.load(ef)
                    
                    # Set enemy index to match the selected level
                    level_based_index = min(selected_level - 1, len(enemies_list) - 1)
                    session['enemy_index'] = level_based_index
                except Exception:
                    # Keep current enemy index if file can't be read
                    pass
        except Exception:
            session['enemy_index'] = 0
        # Auto-save initial game state
        auto_save_progress()
        
        # Check if student is logged in and has a character
        if session.get('is_student') and 'student_id' in session:
            students = load_students()
            student = next((s for s in students if s['id'] == session['student_id']), None)
            if student and 'selected_character' in student:
                # Student has a character, use it and go to game
                session['character'] = student['selected_character']
                return redirect(url_for('game'))
            else:
                # Student needs to choose a character
                session['redirect_after_character'] = 'game'
                return redirect(url_for('choose_character'))
        else:
            # Non-student user (guest) - always let them choose/change character for each new game
            session['redirect_after_character'] = 'game'
            return redirect(url_for('choose_character'))

    # Pass unlocked info to template (GET request) along with chapters
    return render_template('select_level.html', levels=levels, highest_unlocked=highest_unlocked, 
                         chapters=all_chapters, chapter_levels=chapter_levels)

# Route for the home page
@app.route('/')
def index():
    # Get settings to control feature visibility
    settings = get_current_game_settings()
    # Always redirect to level selection if no level is selected
    # If no selected level, show the merged landing page
    if 'selected_level' not in session:
        return render_template('index.html', settings=settings)
    # If a selected level exists, render the index page
    return render_template('index.html', settings=settings)


# Home route (explicit)
@app.route('/home')
def home():
    return render_template('home.html')


# How-to-play route (ensure it exists)
@app.route('/howto')
def howto():
    # Check if student is logged in to provide proper navigation context
    is_student = session.get('is_student', False)
    return render_template('howto.html', is_student=is_student)


@app.route('/choose_character', methods=['GET', 'POST'])
def choose_character():
    total_characters = 16
    
    # Check if student is logged in
    if session.get('is_student') and 'student_id' in session:
        student_id = session['student_id']
        students = load_students()
        student = next((s for s in students if s['id'] == student_id), None)
        
        if request.method == 'POST':
            char = request.form.get('character') or request.form.get('character_id')
            try:
                char_id = int(char)
            except (TypeError, ValueError):
                char_id = None
            if char_id and 1 <= char_id <= total_characters:
                # Save character to student profile
                if student:
                    student['selected_character'] = char_id
                    save_students(students)
                session['character'] = char_id
                flash(f'Character {char_id} selected!', 'success')
                # After choosing a character, redirect based on where they came from
                next_url = request.args.get('next') or session.get('redirect_after_character') or 'student_dashboard'
                session.pop('redirect_after_character', None)
                return redirect(url_for(next_url))
        
        # Check if student already has a character
        if student and 'selected_character' in student:
            session['character'] = student['selected_character']
            # Show current character selection
            return render_template('choose_character.html', 
                                 total_characters=total_characters,
                                 current_character=student['selected_character'],
                                 student_name=student['full_name'])
    
    # For non-logged in users or new character selection
    if request.method == 'POST':
        char = request.form.get('character') or request.form.get('character_id')
        try:
            char_id = int(char)
        except (TypeError, ValueError):
            char_id = None
        if char_id and 1 <= char_id <= total_characters:
            session['character'] = char_id
            # After choosing a character, start the game
            return redirect(url_for('game'))
    
    # Check if guest player has a current character to display
    current_char = session.get('character')
    return render_template('choose_character.html', 
                         total_characters=total_characters,
                         current_character=current_char)

# Route for the game page
@app.route('/game', methods=['GET', 'POST'])
def game():
    # Ensure player has selected a level and has basic session data initialized
    if 'selected_level' not in session:
        flash('Please select a level first.', 'warning')
        return redirect(url_for('select_level'))
    
    # Ensure player has a name
    if not session.get('player_name'):
        flash('Please set your name first.', 'warning')
        return redirect(url_for('index'))
    
    # Get settings (needed for both initialization and debug checks)
    settings = get_current_game_settings()
    
    # Initialize HP if not set (for new games)
    if 'player_hp' not in session:
        session['player_hp'] = settings['base_player_hp']
        session['enemy_hp'] = settings['base_enemy_hp']
        session['score'] = 0
        session['q_index'] = 0
        session['correct_answers'] = 0
        session['wrong_answers'] = 0
        session['level_completed'] = False
        session['enemy_defeated'] = False
    
    # Check if the game is over (only after ensuring HP is initialized)
    if session.get('q_index', 0) >= len(questions):
        return redirect(url_for('result'))
    
    # Debug HP check
    current_hp = session.get('player_hp', 100)
    if settings.get('debug_mode', False):
        print(f"DEBUG: HP Check - current_hp: {current_hp}, q_index: {session.get('q_index', 0)}")
    
    if current_hp <= 0:
        if settings.get('debug_mode', False):
            print(f"DEBUG: Redirecting to you_lose due to HP <= 0 (HP: {current_hp})")
        return redirect(url_for('you_lose'))


    # Use selected level from session
    selected_level = session.get('selected_level', 1)
    try:
        with open("data/levels.json", "r", encoding="utf-8") as f:
            levels = json.load(f)
    except FileNotFoundError:
        return "Error: levels.json file not found."
    except json.JSONDecodeError as e:
        return f"Error: Failed to decode levels.json - {e}"

    # Only allow playing the selected level
    current_level = selected_level
    level_questions = get_questions_for_level(current_level, levels)
    print(f"DEBUG: Level {current_level} questions: {len(level_questions)} questions loaded")  # Debugging
    if not level_questions:
        flash(f'No questions available for level {current_level}. Please contact your teacher.', 'error')
        return redirect(url_for('select_level'))

    # Check if we've exceeded max questions
    questions_per_level = settings.get('questions_per_level', 10)
    
    # Mark enemy as defeated if HP <= 0 but continue playing
    if session.get('enemy_hp', BASE_ENEMY_HP) <= 0:
        session['enemy_defeated'] = True
        session['level_completed'] = True
    
    # Only end the level when all questions are answered
    if session['q_index'] >= questions_per_level:
        return redirect(url_for('result'))
    
    # Get question with proper bounds checking
    question_index = session['q_index'] % len(level_questions) if level_questions else 0
    if question_index >= len(level_questions):
        return redirect(url_for('result'))
    question = level_questions[question_index]

    # Always reload enemies from JSON for each game session
    try:
        with open('data/enemies.json', encoding='utf-8') as f:
            enemies = json.load(f)
    except Exception:
        enemies = []
    # Select enemy based on progression index, with fallbacks
    enemy = None
    enemy_index = session.get('enemy_index', 0)
    
    # Try to get enemy by progression index first
    if isinstance(enemies, list) and enemies and 0 <= int(enemy_index) < len(enemies):
        try:
            enemy = enemies[int(enemy_index)]
            print(f"DEBUG: Using enemy from index {enemy_index}: {enemy.get('name', 'Unknown')}")
        except Exception:
            enemy = None

    # Fallback 1: try to find an enemy that matches the current level
    if not enemy:
        enemy = next((e for e in enemies if e.get("level") == current_level), None)
        if enemy:
            print(f"DEBUG: Found level-based enemy for level {current_level}: {enemy.get('name', 'Unknown')}")
    
    # Fallback 2: use enemy based on level progression (level-1 as index)
    if not enemy and isinstance(enemies, list) and enemies:
        level_based_index = min(max(current_level - 1, 0), len(enemies) - 1)
        try:
            enemy = enemies[level_based_index]
            # Update session to match this enemy for consistency
            session['enemy_index'] = level_based_index
            print(f"DEBUG: Using level-based index {level_based_index} for level {current_level}: {enemy.get('name', 'Unknown')}")
        except Exception:
            enemy = None
    
    # Final fallback: default enemy
    if not enemy:
        enemy = {"name": "Unknown Enemy", "avatar": "❓", "taunt": "No enemies found for this level."}
    
    print(f"DEBUG: Final selected enemy for level {current_level}: {enemy.get('name', 'Unknown')} (enemy_index: {session.get('enemy_index')})")

    # Determine enemy image URL to mirror how player avatar images are used
    enemy_image = None
    # If the enemy JSON includes an explicit image field, use it (assume path under static/)
    if isinstance(enemy, dict) and enemy.get('image'):
        enemy_image = url_for('static', filename=enemy.get('image'))
    else:
        # Attempt to find an image in static/enemies matching the enemy name (safe fallback)
        # Create a safe filename from the enemy name (lowercase, replace spaces with underscores)
        if isinstance(enemy, dict) and enemy.get('name'):
            safe_base = ''.join(c if c.isalnum() else '_' for c in enemy.get('name').lower()).strip('_')
            # Check common extensions
            for ext in ['.png', '.jpg', '.jpeg', '.gif']:
                candidate = f'enemies/{safe_base}{ext}'
                candidate_path = os.path.join(os.path.dirname(__file__), 'static', candidate)
                if os.path.exists(candidate_path):
                    enemy_image = url_for('static', filename=candidate)
                    break

            # If not found by safe name, try fuzzy matching against files in static/enemies
            if not enemy_image:
                try:
                    enemy_tokens = [t for t in ''.join(c if c.isalnum() else ' ' for c in enemy.get('name').lower()).split() if t]
                    enemies_dir = os.path.join(os.path.dirname(__file__), 'static', 'enemies')
                    best_match = None
                    best_score = 0
                    if os.path.isdir(enemies_dir):
                        for fn in os.listdir(enemies_dir):
                            fn_lower = fn.lower()
                            name_part = os.path.splitext(fn_lower)[0]
                            file_tokens = [t for t in ''.join(c if c.isalnum() else ' ' for c in name_part).split() if t]
                            # score = number of matching tokens
                            score = sum(1 for t in enemy_tokens if t in file_tokens)
                            # if all tokens match, immediate perfect match
                            if score == len(enemy_tokens) and score > 0:
                                best_match = fn
                                best_score = score
                                break
                            if score > best_score:
                                best_score = score
                                best_match = fn
                        # accept best match if it matches at least one token
                        if best_match and best_score > 0:
                            candidate = f'enemies/{best_match}'
                            enemy_image = url_for('static', filename=candidate)
                except Exception:
                    enemy_image = None

    # Attach enemy_image into the template context

    # Initialize or reset the timer for the current question
    # Always reset timer on GET request
    if request.method == 'GET' or "level_start_time" not in session:
        session["level_start_time"] = time.time()
        # Initialize current_timer if not set
        if "current_timer" not in session:
            session["current_timer"] = settings.get('question_time_limit', 30)

    # Calculate remaining time
    settings = get_current_game_settings()
    elapsed = time.time() - session["level_start_time"]
    time_left = max(0, session.get("current_timer", settings.get('question_time_limit', 30)) - int(elapsed))

    # Debug timer info
    if settings.get('debug_mode', False):
        print(f"DEBUG: Timer - elapsed: {elapsed:.2f}s, time_left: {time_left}s, question_time_limit: {settings.get('question_time_limit', 30)}s, current_timer: {session.get('current_timer', 'not set')}")

    if time_left == 0:
        # Time expired → check timeout behavior setting
        settings = get_current_game_settings()
        session['wrong_answers'] = session.get('wrong_answers', 0) + 1  # Track timeouts as wrong answers
        
        # Check timeout behavior setting
        timeout_behavior = settings.get('timeout_behavior', 'penalty')
        
        if timeout_behavior == 'fail':
            # Immediate fail on timeout
            session['feedback'] = "⏳ Time's up! Timeout results in immediate failure."
            return redirect(url_for('you_lose'))
        else:
            # Apply penalty and continue (default behavior) - use base damage only, not multiplied by level
            timeout_damage = settings['base_damage']
            current_hp = session.get('player_hp', settings['base_player_hp'])
            
            # Ensure HP is properly initialized
            if 'player_hp' not in session:
                session['player_hp'] = settings['base_player_hp']
                current_hp = settings['base_player_hp']
            
            # Apply damage
            session['player_hp'] = current_hp - timeout_damage
            
            # Debug info
            if settings.get('debug_mode', False):
                print(f"DEBUG: Timeout - HP before: {current_hp}, damage: {timeout_damage}, HP after: {session['player_hp']}")
            
            # Check if player has failed due to low HP
            if session['player_hp'] <= 0:
                session['feedback'] = f"⏳ Time's up! You took {timeout_damage} damage and your HP reached 0. Game Over!"
                return redirect(url_for('you_lose'))
            
            session['feedback'] = f"⏳ Time's up! You took {timeout_damage} damage for running out of time. HP: {session['player_hp']}"
            session['q_index'] += 1
            session["level_start_time"] = time.time()  # Reset timer for the next question
            session["current_timer"] = max(10, session.get("current_timer", settings.get('question_time_limit', 30)) - 5)  # Deduct 5s for next question, min 10s
            
            # Auto-save progress after timeout
            auto_save_progress()
            
            return redirect(url_for('feedback'))

    if request.method == 'POST':
        user_answer = request.form.get('answer', '').strip().lower()
        correct_answer = question.get('answer', '').strip().lower()

        # Normalize keywords
        raw_keywords = question.get('keywords', [])
        if isinstance(raw_keywords, str):
            keywords = [k.strip().lower() for k in raw_keywords.split(',') if k.strip()]
        else:
            keywords = [str(k).strip().lower() for k in raw_keywords]

        # Calculate time taken to answer
        time_taken = time.time() - session["level_start_time"]

        # Determine damage and score based on time taken
        if time_taken <= 5:  # First 5 seconds → double damage and double score
            damage = 20
            score = 20
        elif time_taken <= 15:  # Within 15 seconds → regular damage and score
            damage = 10
            score = 10
        else:  # Remaining time → half damage and low score
            damage = 5
            score = 5

        # Only apply this block for the main game mode, not endless or test yourself
        if not session.get('endless_questions') and not session.get('test_questions'):
            # Get current game settings
            settings = get_current_game_settings()
            base_damage = settings['base_damage']
            points_correct = settings['points_correct']
            points_wrong = settings['points_wrong']
            
            # Debug logging if enabled
            if settings.get('debug_mode', False):
                print(f"[DEBUG] Player answer: '{user_answer}' for question: '{question.get('q', 'N/A')[:50]}...'")
                print(f"[DEBUG] Expected answer: '{correct_answer}', Keywords: {keywords}")
                print(f"[DEBUG] Time taken: {time_taken:.2f}s, Damage: {damage}, Score: {score}")
            
            # Get the question feedback
            question_feedback = question.get('feedback', 'No additional information available.')