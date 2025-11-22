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
from whoosh.fields import Schema, TEXT, ID
from whoosh import index
from config import TEACHER_CREDENTIALS, AI_PROVIDER, OPENAI_API_KEY, GEMINI_API_KEY, OPENAI_MODEL, GEMINI_MODEL, AI_MODEL, UPLOAD_FOLDER, ALLOWED_EXTENSIONS, MAX_CONTENT_LENGTH

# Constants
LEADERBOARD_FILE = "data/leaderboard.json"
GUEST_LEADERBOARD_FILE = "data/guest_leaderboard.json"

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
            if 'candidates' in result and len(result['candidates']) > 0:
                if 'content' in result['candidates'][0] and 'parts' in result['candidates'][0]['content']:
                    response_text = result['candidates'][0]['content']['parts'][0]['text']
                    print(f"DEBUG: Response length: {len(response_text)} characters")
                    print(f"DEBUG: Response ends with: ...{response_text[-50:]}")
                    return response_text
                else:
                    return "Gemini API Error: Unexpected response format"
            else:
                return f"Gemini API Error: No response generated. Full response: {result}"
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
                return True, "Partial match!", 0.9
            
            # Check partial matches with keywords
            for keyword in keywords:
                if user_answer in keyword or keyword in user_answer:
                    return True, f"Partial match with '{keyword}'!", 0.9
        
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
def save_leaderboard(player_name, score, total_time, correct_answers, wrong_answers, game_mode="adventure"):
    # Save to student leaderboard if it's a logged-in student
    if session.get('is_student') and session.get('student_id'):
        print(f"Saving student leaderboard data: {player_name}, mode: {game_mode}")
        
        # Get student information for better leaderboard display
        student_id = session.get('student_id')
        
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
        print(f"Saving guest leaderboard data: {player_name}, mode: {game_mode}")
        
        record = {
            "player": player_name,
            "score": score,
            "time": round(total_time, 2),
            "correct_answers": correct_answers,
            "wrong_answers": wrong_answers,
            "game_mode": game_mode,
            "date": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
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

    # Determine highest unlocked level (simple: highest completed in session, or 1 if none)
    highest_unlocked = session.get('highest_unlocked', 1)
    # Optionally, you could use leaderboard or persistent storage for this

    if request.method == 'POST':
        selected_level = int(request.form.get('level', 1))
        session['selected_level'] = selected_level
        # Reset session variables for a new game
        settings = get_current_game_settings()
        session['score'] = 0
        session['player_hp'] = settings['base_player_hp']
        session['enemy_level'] = selected_level
        # Set enemy HP to the current setting
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
                # Keep current enemy progression when selecting different levels
                # But ensure enemy index corresponds roughly to the selected level
                try:
                    with open('data/enemies.json', encoding='utf-8') as ef:
                        enemies_list = json.load(ef)
                    
                    # Try to find an enemy that matches the selected level
                    level_based_index = min(selected_level - 1, len(enemies_list) - 1)
                    
                    # Use the higher of current progression or level-based index
                    session['enemy_index'] = max(current_enemy_index, level_based_index)
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
            # Non-student user (guest) - check if they already have a character
            if session.get('character'):
                # Guest already has a character, go directly to game
                return redirect(url_for('game'))
            else:
                # Guest needs to choose a character first
                return redirect(url_for('choose_character'))

    # Pass unlocked info to template (GET request)
    return render_template('select_level.html', levels=levels, highest_unlocked=highest_unlocked)

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
    
    return render_template('choose_character.html', total_characters=total_characters)

# Route for the game page
@app.route('/game', methods=['GET', 'POST'])
def game():
    # Check if the game is over
    # Use safe gets to avoid KeyError from malformed sessions
    if session.get('q_index', 0) >= len(questions):
        return redirect(url_for('result'))
    if session.get('player_hp', 0) <= 0:
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
    print(f"DEBUG: Level {current_level} questions: {level_questions}")  # Debugging
    if not level_questions:
        return "No questions available for this level. Please check levels.json."

    # Check if we've exceeded max questions
    settings = get_current_game_settings()
    questions_per_level = settings.get('questions_per_level', 10)
    question_index = session['q_index'] % questions_per_level
    
    # Mark enemy as defeated if HP <= 0 but continue playing
    if session.get('enemy_hp', BASE_ENEMY_HP) <= 0:
        session['enemy_defeated'] = True
        session['level_completed'] = True
    
    # Only end the level when all questions are answered
    if session['q_index'] >= questions_per_level:
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

    # Initialize the timer for the current question
    if "level_start_time" not in session:
        session["level_start_time"] = time.time()

    # Calculate remaining time
    settings = get_current_game_settings()
    elapsed = time.time() - session["level_start_time"]
    time_left = max(0, session.get("current_timer", settings.get('question_time_limit', 30)) - int(elapsed))

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
            session['player_hp'] -= timeout_damage
            
            # Check if player has failed due to low HP
            if session.get('player_hp', 0) <= 0:
                session['feedback'] = f"⏳ Time's up! You took {timeout_damage} damage and your HP reached 0. Game Over!"
                return redirect(url_for('you_lose'))
            
            session['feedback'] = f"⏳ Time's up! You took {timeout_damage} damage for running out of time."
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
            
            # Use fuzzy matching for answer checking
            is_correct, feedback_type, similarity_score = check_answer_fuzzy(user_answer, question)
            
            # Log answer attempt
            log_analytics_event('answer_submitted', {
                'question_id': question.get('id'),
                'user_answer': user_answer,
                'correct_answer': correct_answer,
                'is_correct': is_correct,
                'time_taken': time_taken,
                'similarity_score': similarity_score,
                'level': current_level
            })
            
            if is_correct:
                # Calculate speed bonus if enabled
                speed_multiplier = 1.0
                speed_message = ""
                if settings.get('speed_bonus', True) and time_taken <= 10:
                    if time_taken <= 5:
                        speed_multiplier = 2.0
                        speed_message = " (🚀 Lightning bonus: x2 points!)"
                    elif time_taken <= 10:
                        speed_multiplier = 1.5
                        speed_message = " (⚡ Speed bonus: x1.5 points!)"
                
                points_awarded = int(points_correct * speed_multiplier)
                
                # Check if enemy is already defeated for bonus scoring
                enemy_already_defeated = session.get('enemy_defeated', False)
                
                if "Exact answer" in feedback_type or similarity_score == 1.0:
                    # Exact match gets triple damage or bonus points
                    if enemy_already_defeated:
                        # Enemy already defeated - give bonus points instead of damage
                        bonus_points = points_awarded * 2  # Double bonus for exact match after defeat
                        session['score'] += bonus_points
                        session['feedback'] = f"🏆 {feedback_type} Enemy already defeated! Bonus points: {bonus_points} in {time_taken:.2f} seconds{speed_message}.<br><br>✅ {question_feedback}"
                    else:
                        # Normal damage to enemy
                        session['score'] += points_awarded
                        session['enemy_hp'] -= (base_damage * 3)
                        # Ensure enemy HP doesn't go below 0
                        if session['enemy_hp'] <= 0:
                            session['enemy_hp'] = 0
                            session['enemy_defeated'] = True
                        session['feedback'] = f"🔥 {feedback_type} Triple damage: {base_damage*3} and {points_awarded} points in {time_taken:.2f} seconds{speed_message}.<br><br>✅ {question_feedback}"
                else:
                    # Fuzzy match gets regular damage or normal points
                    similarity_percent = int(similarity_score * 100)
                    if enemy_already_defeated:
                        # Enemy already defeated - give normal points (same as regular scoring)
                        session['score'] += points_awarded
                        session['feedback'] = f"🏆 {feedback_type} ({similarity_percent}% match) Enemy already defeated! Earned {points_awarded} points in {time_taken:.2f} seconds{speed_message}.<br><br>✅ {question_feedback}"
                    else:
                        # Normal damage to enemy
                        session['score'] += points_awarded
                        session['enemy_hp'] -= base_damage
                        # Ensure enemy HP doesn't go below 0
                        if session['enemy_hp'] <= 0:
                            session['enemy_hp'] = 0
                            session['enemy_defeated'] = True
                        session['feedback'] = f"🎯 {feedback_type} ({similarity_percent}% match) You dealt {base_damage} damage and earned {points_awarded} points in {time_taken:.2f} seconds{speed_message}.<br><br>✅ {question_feedback}"
                
                session["current_timer"] = min(settings.get('question_time_limit', 30) * 2, session.get("current_timer", settings.get('question_time_limit', 30)) + 5)  # Add 5s to timer for next question, max 2x base limit
                session['correct_answers'] = session.get('correct_answers', 0) + 1  # Track correct answers
            else:
                session['player_hp'] -= base_damage  # Use base damage only, not multiplied by level
                session['score'] -= points_wrong  # Deduct points for wrong answer
                session['feedback'] = f"❌ Incorrect! You took {base_damage} damage.<br><br>💡 {question_feedback}"
                session["current_timer"] = max(10, session.get("current_timer", settings.get('question_time_limit', 30)) - 5)  # Deduct 5s from timer for next question, min 10s
                session['wrong_answers'] = session.get('wrong_answers', 0) + 1  # Track wrong answers

        # Auto-save progress after each question
        auto_save_progress()

        # Reset timer for the next question
        session['level_start_time'] = time.time()

        # Move to the next question
        session['q_index'] += 1
        return redirect(url_for('feedback'))

    # Get current settings for display options
    settings = get_current_game_settings()
    
    return render_template('game.html',
                           question=question,
                           score=session['score'],
                           player_hp=session['player_hp'],
                           enemy_hp=session['enemy_hp'],
                           enemy_defeated=session.get('enemy_defeated', False),
                           q_number=question_index + 1,
                           total=questions_per_level,  # Use configurable questions per level
                           level=current_level,
                           enemy=enemy,
                           enemy_image=enemy_image,
                           time_left=time_left,
                           settings=settings)

# Route for the feedback page
@app.route('/feedback')
def feedback():
    # If player's HP reached 0, go straight to defeat
    if session.get('player_hp', 0) <= 0:
        return redirect(url_for('you_lose'))
    if not session.get('feedback'):
        return redirect(url_for('game'))  # Redirect to the game page if no feedback
    feedback = session['feedback']
    session['feedback'] = None  # Clear feedback after rendering
    return render_template('feedback.html',
                           feedback=feedback,
                           player_hp=session['player_hp'],
                           enemy_hp=session['enemy_hp'],
                           score=session['score'],
                           level=session['enemy_level'])

# Route for the result page
@app.route('/result')
def result():
    # Calculate the final score
    settings = get_current_game_settings()
    bonus = settings['level_bonus'] if session.get('level_completed', False) and session['player_hp'] > 0 else 0
    final_score = session['score'] + bonus

    # Save the player's performance to the leaderboard
    total_time = time.time() - session.get("game_start_time", time.time())
    save_leaderboard(
        player_name=session.get("player_name", "Anonymous"),
        score=final_score,
        total_time=total_time,
        correct_answers=session.get('correct_answers', 0),
        wrong_answers=session.get('wrong_answers', 0),
        game_mode="adventure"
    )
    
    # Save student progress if logged in
    if session.get('is_student') and session.get('student_id'):
        student_id = session.get('student_id')
        level = session.get('selected_level')
        correct_answers = session.get('correct_answers', 0)
        wrong_answers = session.get('wrong_answers', 0)
        total_questions = correct_answers + wrong_answers
        
        update_student_progress(
            student_id=student_id,
            game_type='adventure_mode',
            level=level,
            score=final_score,
            correct_answers=correct_answers,
            total_questions=total_questions,
            time_taken=total_time
        )

    # If the player died, show lose page
    if session.get('player_hp', 0) <= 0:
        return redirect(url_for('you_lose'))

    # Log level completion
    log_analytics_event('level_completed', {
        'level': session.get('selected_level', 1),
        'final_score': final_score,
        'player_hp': session.get('player_hp', 0),
        'enemy_hp': session.get('enemy_hp', 0),
        'total_time': total_time,
        'correct_answers': session.get('correct_answers', 0),
        'wrong_answers': session.get('wrong_answers', 0),
        'level_completed': session.get('level_completed', False)
    })

    # If the level is completed, allow to select next level
    next_level = session.get('selected_level', 1) + 1
    try:
        with open("data/levels.json", "r", encoding="utf-8") as f:
            levels = json.load(f)
    except Exception:
        levels = []
    max_level = max([lvl['level'] for lvl in levels], default=1)
    
    # Calculate required accuracy based on settings
    settings = get_current_game_settings()
    total_questions = session.get('correct_answers', 0) + session.get('wrong_answers', 0)
    current_accuracy = (session.get('correct_answers', 0) / total_questions * 100) if total_questions > 0 else 0
    required_accuracy = settings.get('min_accuracy', 70)
    
    can_advance = (
        session.get('level_completed', False)
        and current_accuracy >= required_accuracy
        and next_level <= max_level
    )

    # Unlock the next level if completed
    if session.get('level_completed', False):
        prev_highest = session.get('highest_unlocked', 1)
        if next_level > prev_highest:
            session['highest_unlocked'] = next_level

        # Auto-save progress after level completion
        auto_save_progress()

        # Advance the enemy_index so a new enemy appears after each completed level
        try:
            with open('data/enemies.json', encoding='utf-8') as f:
                enemies_list = json.load(f)
        except Exception:
            enemies_list = []
        
        if isinstance(enemies_list, list) and enemies_list:
            current_idx = session.get('enemy_index', 0) or 0
            try:
                current_idx = int(current_idx)
            except Exception:
                current_idx = 0
            
            # Advance to next enemy, but don't exceed the list bounds
            next_idx = min(current_idx + 1, len(enemies_list) - 1)
            
            # Also ensure the enemy progression matches or exceeds the level progression
            # Each completed level should advance at least to that level's enemy
            level_based_idx = min(next_level - 1, len(enemies_list) - 1) if next_level <= max_level else len(enemies_list) - 1
            
            # Use the higher of the two indices to ensure proper progression
            final_idx = max(next_idx, level_based_idx)
            session['enemy_index'] = final_idx
            
            print(f"DEBUG: Enemy progression - Level: {next_level}, Current idx: {current_idx}, Next idx: {next_idx}, Level-based idx: {level_based_idx}, Final idx: {final_idx}")
        # If we've unlocked past the maximum level, the player beat the game
        try:
            with open("data/levels.json", "r", encoding="utf-8") as f:
                levels = json.load(f)
        except Exception:
            levels = []
        max_level = max([lvl['level'] for lvl in levels], default=1)
        if session.get('highest_unlocked', 1) > max_level:
            # Player has unlocked beyond max level -> they completed all levels
            return redirect(url_for('you_win'))

    return render_template('result.html', score=final_score,
                           player_hp=session['player_hp'],
                           enemy_hp=session['enemy_hp'],
                           outcome="Game Over",
                           level=session['enemy_level'],
                           enemy={"name": "Unknown Enemy", "avatar": "❓"},
                           can_advance=can_advance,
                           next_level=next_level)

# Route for the search functionality
from whoosh.qparser import QueryParser

@app.route('/search', methods=['GET'])
def search():
    query_text = request.args.get('q', '').strip()
    results = []
    
    if query_text:
        query_lower = query_text.lower()
        # Search through questions using multiple criteria
        for question in questions:
            match_found = False
            
            # Search in question text
            if query_lower in question.get('q', '').lower():
                match_found = True
            
            # Search in answer
            elif query_lower in question.get('answer', '').lower():
                match_found = True
            
            # Search in keywords
            elif question.get('keywords'):
                keywords = question['keywords']
                if isinstance(keywords, str):
                    if query_lower in keywords.lower():
                        match_found = True
                elif isinstance(keywords, list):
                    if any(query_lower in keyword.lower() for keyword in keywords):
                        match_found = True
            
            # Search in feedback/explanation
            elif question.get('feedback') and query_lower in question.get('feedback', '').lower():
                match_found = True
            
            if match_found:
                results.append(question)
    
    return render_template('search.html', results=results)

# Route for the leaderboard page
@app.route('/leaderboard')
def leaderboard():
    try:
        with open(LEADERBOARD_FILE, "r", encoding="utf-8") as f:
            all_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        all_data = []

    # Separate leaderboards by game mode
    adventure_data = [entry for entry in all_data if entry.get("game_mode", "adventure") == "adventure"]
    test_yourself_data = [entry for entry in all_data if entry.get("game_mode") == "test_yourself"]
    endless_data = [entry for entry in all_data if entry.get("game_mode") == "endless"]
    
    # Sort each category by score (highest first), then by time (lowest first)
    adventure_leaderboard = sorted(adventure_data, key=lambda x: (-x["score"], x["time"]))[:10]
    test_yourself_leaderboard = sorted(test_yourself_data, key=lambda x: (-x["score"], x["time"]))[:10]
    endless_leaderboard = sorted(endless_data, key=lambda x: (-x["score"], x["time"]))[:10]

    # Check if student is logged in to provide proper navigation context
    is_student = session.get('is_student', False)

    return render_template("leaderboard.html", 
                         adventure_leaderboard=adventure_leaderboard,
                         test_yourself_leaderboard=test_yourself_leaderboard,
                         endless_leaderboard=endless_leaderboard,
                         is_student=is_student)


@app.route('/guest_leaderboard')
def guest_leaderboard():
    try:
        with open(GUEST_LEADERBOARD_FILE, "r", encoding="utf-8") as f:
            all_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        all_data = []

    # Separate guest leaderboards by game mode
    adventure_data = [entry for entry in all_data if entry.get("game_mode", "adventure") == "adventure"]
    test_yourself_data = [entry for entry in all_data if entry.get("game_mode") == "test_yourself"]
    endless_data = [entry for entry in all_data if entry.get("game_mode") == "endless"]
    
    # Sort each category by score (highest first), then by time (lowest first)
    adventure_leaderboard = sorted(adventure_data, key=lambda x: (-x["score"], x["time"]))[:10]
    test_yourself_leaderboard = sorted(test_yourself_data, key=lambda x: (-x["score"], x["time"]))[:10]
    endless_leaderboard = sorted(endless_data, key=lambda x: (-x["score"], x["time"]))[:10]

    return render_template("guest_leaderboard.html", 
                         adventure_leaderboard=adventure_leaderboard,
                         test_yourself_leaderboard=test_yourself_leaderboard,
                         endless_leaderboard=endless_leaderboard)


@app.route('/you_win')
def you_win():
    # Simple win page when all levels are completed
    # Reset enemy state to original when the player finishes the game
    try:
        settings = get_current_game_settings()
        session['enemy_index'] = 0
        session['enemy_hp'] = settings['base_enemy_hp']
        session.pop('enemy_level', None)
    except Exception:
        pass
    
    # Check if student is logged in to provide proper navigation context
    is_student = session.get('is_student', False)
    return render_template('you_win.html', is_student=is_student)


@app.route('/you_lose')
def you_lose():
    # Simple lose page when player HP hits 0
    # Reset enemy state to original when the player loses
    try:
        settings = get_current_game_settings()
        session['enemy_index'] = 0
        session['enemy_hp'] = settings['base_enemy_hp']
        session.pop('enemy_level', None)
    except Exception:
        pass
    return render_template('you_lose.html')

# ------------------- TEST YOURSELF MODE -------------------
import random

@app.route('/test_yourself', methods=['GET', 'POST'])
def test_yourself():
    # Check if Test Yourself mode is enabled
    settings = get_current_game_settings()
    if not settings.get('test_yourself_enabled', True):
        flash('Test Yourself mode is currently disabled.', 'error')
        return redirect(url_for('index'))
    
    # Only reset test state for a true new start (GET with ?new=1)
    if request.method == 'GET' and request.args.get('new') == '1':
        session.pop('test_question_ids', None)
        session.pop('test_q_index', None)
        session.pop('test_correct', None)
        session.pop('test_start_time', None)
        session.pop('test_time_limit', None)
        session['test_user_answers'] = []
        print(f"[DEBUG] questions list length at test start: {len(questions)}")
        
        # Use questions from test_yourself pool
        test_pool_questions = get_questions_for_pool('test_yourself')
        if not test_pool_questions:
            test_pool_questions = questions  # Fallback to all questions
        
        valid_questions = [q for q in test_pool_questions if q.get('q') and str(q.get('q')).strip()]
        if not valid_questions:
            session['test_question_ids'] = []
        elif len(valid_questions) >= 40:
            session['test_question_ids'] = [q['id'] for q in random.sample(valid_questions, 40)]
        else:
            session['test_question_ids'] = [random.choice(valid_questions)['id'] for _ in range(40)]
        while len(session['test_question_ids']) > 40:
            session['test_question_ids'].pop()
        while len(session['test_question_ids']) < 40 and valid_questions:
            session['test_question_ids'].append(random.choice(valid_questions)['id'])
        session['test_q_index'] = 0
        session['test_correct'] = 0
        session['test_start_time'] = time.time()
        session['test_time_limit'] = 60 * 60  # 1 hour in seconds

    # Calculate timer
    total_seconds_left = max(0, int(session.get('test_time_limit', 3600) - (time.time() - session.get('test_start_time', time.time()))))
    time_left_min = total_seconds_left // 60
    time_left_sec = total_seconds_left % 60
    q_index = session.get('test_q_index', 0)
    test_question_ids = session.get('test_question_ids', [])
    # Rebuild the test_questions list from global questions using IDs
    id_to_question = {q['id']: q for q in questions}
    test_questions = [id_to_question[qid] for qid in test_question_ids if qid in id_to_question]
    if not test_questions or q_index >= 40 or total_seconds_left <= 0:
        print(f"[DEBUG] REDIRECT TO RESULT: test_q_index={q_index}, test_questions={len(test_questions)}, total_seconds_left={total_seconds_left}, test_user_answers={len(session.get('test_user_answers', []))}")
        session['test_q_index'] = 40
        return redirect(url_for('test_yourself_result'))

    # Skip invalid questions
    while q_index < len(test_questions) and not test_questions[q_index].get('q'):
        q_index += 1
        session['test_q_index'] = q_index
    if q_index >= len(test_questions):
        session['test_q_index'] = 40
        return redirect(url_for('test_yourself_result'))
    question = test_questions[q_index]

    correct_count = session.get('test_correct', 0)
    if request.method == 'POST':
        user_answer = request.form.get('answer', '').strip().lower()
        correct_answer = question.get('answer', '').strip().lower()
        # Normalize keywords
        raw_keywords = question.get('keywords', [])
        if isinstance(raw_keywords, str):
            keywords = [k.strip().lower() for k in raw_keywords.split(',') if k.strip()]
        else:
            keywords = [str(k).strip().lower() for k in raw_keywords]
        # Use fuzzy matching for test mode
        is_correct, feedback_type, similarity_score = check_answer_fuzzy(user_answer, question)
        
        session['test_user_answers'].append({
            'question': question.get('q', ''),
            'user_answer': user_answer,
            'correct_answer': correct_answer,
            'correct': is_correct,
            'feedback': question.get('feedback', 'No additional information available.'),
            'match_type': feedback_type,
            'similarity': similarity_score
        })
        if is_correct:
            session['test_correct'] = correct_count + 1
        session['test_q_index'] = q_index + 1
        print(f"[DEBUG] POST: test_q_index={session['test_q_index']}, test_questions={len(test_questions)}, test_user_answers={len(session['test_user_answers'])}")
        return redirect(url_for('test_yourself'))

    return render_template('test_yourself.html',
                          question=question,
                          q_number=q_index + 1,
                          q_index=q_index,
                          test_questions=test_questions,
                          correct_count=correct_count,
                          time_left_min=time_left_min,
                          time_left_sec=time_left_sec,
                          total_seconds_left=total_seconds_left)

@app.route('/test_yourself_result')
def test_yourself_result():
    # Check if Test Yourself mode is enabled
    settings = get_current_game_settings()
    if not settings.get('test_yourself_enabled', True):
        flash('Test Yourself mode is currently disabled.', 'error')
        return redirect(url_for('index'))
    
    # Use the question IDs to determine total
    total = len(session.get('test_question_ids', []))
    correct = session.get('test_correct', 0)
    percent = int((correct / total) * 100) if total else 0
    passed = percent >= 75
    # Get user answers for review
    user_answers = session.get('test_user_answers', [])
    
    # Save student progress and leaderboard if logged in
    if session.get('is_student') and session.get('student_id'):
        student_id = session.get('student_id')
        test_start_time = session.get('test_start_time', time.time())
        time_taken = time.time() - test_start_time
        score = correct * 10  # Simple scoring system
        
        # Save to leaderboard
        save_leaderboard(
            player_name=session.get("player_name", "Anonymous"),
            score=score,
            total_time=time_taken,
            correct_answers=correct,
            wrong_answers=total - correct,
            game_mode="test_yourself"
        )
        
        update_student_progress(
            student_id=student_id,
            game_type='test_yourself',
            level=None,
            score=score,
            correct_answers=correct,
            total_questions=total,
            time_taken=time_taken
        )
    
    # Clear session state for test mode
    session.pop('test_question_ids', None)
    session.pop('test_q_index', None)
    session.pop('test_correct', None)
    session.pop('test_start_time', None)
    session.pop('test_time_limit', None)
    session.pop('test_user_answers', None)
    return render_template('test_yourself_result.html',
                          correct_count=correct,
                          percent=percent,
                          passed=passed,
                          user_answers=user_answers)

# Load enemies from enemies.json
try:
    with open('data/enemies.json', encoding='utf-8') as f:
        enemies = json.load(f)
    print(f"DEBUG: Enemies loaded successfully: {enemies}")  # Debugging
except FileNotFoundError:
    print("Error: enemies.json file not found.")
    enemies = []
except json.JSONDecodeError as e:
    print(f"Error: Failed to decode enemies.json - {e}")
    enemies = []

# Load questions from the JSON file
try:
    questions_file = os.path.join(os.path.dirname(__file__), 'data', 'questions.json')
    with open(questions_file, encoding='utf-8') as f:
        questions = json.load(f)
    print(f"Questions loaded successfully! Loaded {len(questions)} questions.")
except FileNotFoundError:
    print("Error: questions.json file not found.")
    questions = []
except json.JSONDecodeError as e:
    print(f"Error: Failed to decode questions.json - {e}")
    questions = []

# Add questions to the Whoosh index
from whoosh.writing import AsyncWriter
writer = AsyncWriter(ix)
for question in questions:
    # Normalize keywords: accept either a list or a comma-separated string
    raw_keywords = question.get('keywords', [])
    if isinstance(raw_keywords, str):
        keywords = [k.strip().lower() for k in raw_keywords.split(',') if k.strip()]
    else:
        keywords = [str(k).strip().lower() for k in raw_keywords]
    writer.add_document(
        id=str(question.get("id", "")),
        question=question.get("q", ""),
        answer=question.get("answer", ""),
        keywords=keywords
    )
try:
    writer.commit()
except Exception as e:
    print(f"Whoosh writer.commit() failed: {e}. Attempting to recreate index and retry...")
    try:
        import shutil
        if os.path.exists("indexdir"):
            shutil.rmtree("indexdir")
    except Exception:
        pass
    # Recreate index and re-add documents
    ix = create_or_open_index()
    writer = AsyncWriter(ix)
    for question in questions:
        raw_keywords = question.get('keywords', [])
        if isinstance(raw_keywords, str):
            keywords = [k.strip().lower() for k in raw_keywords.split(',') if k.strip()]
        else:
            keywords = [str(k).strip().lower() for k in raw_keywords]
        writer.add_document(
            id=str(question.get("id", "")),
            question=question.get("q", ""),
            answer=question.get("answer", ""),
            keywords=keywords
        )
    writer.commit()

# ------------------- ENDLESS MODE -------------------
import random

@app.route('/endless')
def endless():
    # Check if Endless Mode is enabled
    settings = get_current_game_settings()
    if not settings.get('endless_mode_enabled', True):
        flash('Endless Mode is currently disabled.', 'error')
        return redirect(url_for('index'))
    
    # Show setup page if no player name is set or if this is a fresh start
    if not session.get('player_name') or not session.get('endless_score_initialized'):
        return render_template('endless_setup.html')
    
    # If player has died, redirect to results
    if session.get('endless_hp', 0) <= 0:
        return redirect(url_for('endless_result'))
        
    # Continue with existing game
    return redirect(url_for('endless_game'))

@app.route('/endless/start', methods=['POST'])
def endless_start():
    # Check if Endless Mode is enabled
    settings = get_current_game_settings()
    if not settings.get('endless_mode_enabled', True):
        flash('Endless Mode is currently disabled.', 'error')
        return redirect(url_for('index'))
    # Get player name from form
    player_name = request.form.get('player_name', '').strip()
    if not player_name:
        player_name = 'Anonymous Warrior'
    
    # Set player name in session
    session['player_name'] = player_name
    
    # Initialize endless mode session state
    session['endless_score'] = 0
    session['endless_hp'] = 100
    session['endless_streak'] = 0
    session['endless_highest_streak'] = 0
    session['endless_total_answered'] = 0
    session['endless_correct'] = 0
    session['endless_wrong'] = 0
    session['endless_start_time'] = time.time()
    session['endless_question_start'] = time.time()
    
    # Use questions from endless mode pool
    endless_questions = get_questions_for_pool('endless_mode')
    if endless_questions:
        session['endless_current_question'] = random.choice(endless_questions)
    else:
        # Fallback to all questions if pool is empty
        session['endless_current_question'] = random.choice(questions)
    
    session['endless_score_initialized'] = True
    
    return redirect(url_for('endless_game'))

@app.route('/endless/game', methods=['GET', 'POST'])
def endless_game():
    # Check if Endless Mode is enabled
    settings = get_current_game_settings()
    if not settings.get('endless_mode_enabled', True):
        flash('Endless Mode is currently disabled.', 'error')
        return redirect(url_for('index'))
    # Check if player name is set, if not redirect to setup
    if not session.get('player_name'):
        return redirect(url_for('endless'))
        
    # Check if game is over
    if session.get('endless_hp', 0) <= 0:
        return redirect(url_for('endless_result'))
        
    # Timer logic
    if 'endless_question_start' not in session:
        session['endless_question_start'] = time.time()
    elapsed = time.time() - session['endless_question_start']
    time_left = max(0, 45 - int(elapsed))
    
    # Pick or keep the current question
    if 'endless_current_question' not in session:
        endless_questions = get_questions_for_pool('endless_mode')
        if endless_questions:
            session['endless_current_question'] = random.choice(endless_questions)
        else:
            session['endless_current_question'] = random.choice(questions)
    question = session['endless_current_question']
    
    # Get session variables
    streak = session.get('endless_streak', 0)
    score = session.get('endless_score', 0)
    player_hp = session.get('endless_hp', 100)
    highest_streak = session.get('endless_highest_streak', 0)
    total_answered = session.get('endless_total_answered', 0)
    
    # Handle timeout
    if time_left == 0:
        session['endless_hp'] = session.get('endless_hp', 100) - 10
        session['endless_streak'] = 0
        session['endless_wrong'] = session.get('endless_wrong', 0) + 1
        session['endless_total_answered'] = session.get('endless_total_answered', 0) + 1
        
        # Check if HP reached 0 after timeout penalty
        if session.get('endless_hp', 0) <= 0:
            return redirect(url_for('endless_result'))
        
        session['endless_question_start'] = time.time()
        endless_questions = get_questions_for_pool('endless_mode')
        if endless_questions:
            session['endless_current_question'] = random.choice(endless_questions)
        else:
            session['endless_current_question'] = random.choice(questions)
        return redirect(url_for('endless_game'))
    
    # Handle answer submission
    if request.method == 'POST':
        user_answer = request.form.get('answer', '').strip().lower()
        correct_answer = question.get('answer', '').strip().lower()
        raw_keywords = question.get('keywords', [])
        if isinstance(raw_keywords, str):
            keywords = [k.strip().lower() for k in raw_keywords.split(',') if k.strip()]
        else:
            keywords = [str(k).strip().lower() for k in raw_keywords]
        # Use fuzzy matching for endless mode
        is_correct, feedback_type, similarity_score = check_answer_fuzzy(user_answer, question)
        
        # Store feedback for this question
        question_feedback = question.get('feedback', 'No additional information available.')
        if 'endless_feedback_list' not in session:
            session['endless_feedback_list'] = []
        
        feedback_entry = {
            'question': question.get('q', ''),
            'user_answer': user_answer,
            'correct_answer': correct_answer,
            'correct': is_correct,
            'feedback': question_feedback,
            'match_type': feedback_type,
            'similarity': similarity_score
        }
        session['endless_feedback_list'].append(feedback_entry)
        
        session['endless_total_answered'] = session.get('endless_total_answered', 0) + 1
        if is_correct:
            session['endless_score'] = session.get('endless_score', 0) + 10
            session['endless_streak'] = session.get('endless_streak', 0) + 1
            session['endless_correct'] = session.get('endless_correct', 0) + 1
            if session['endless_streak'] > session.get('endless_highest_streak', 0):
                session['endless_highest_streak'] = session['endless_streak']
            # HP regen after 5 correct in a row
            if session['endless_streak'] % 5 == 0:
                session['endless_hp'] = min(100, session.get('endless_hp', 100) + 20)
        else:
            session['endless_hp'] = session.get('endless_hp', 100) - 10
            session['endless_streak'] = 0
            session['endless_wrong'] = session.get('endless_wrong', 0) + 1
        session['endless_question_start'] = time.time()
        endless_questions = get_questions_for_pool('endless_mode')
        if endless_questions:
            session['endless_current_question'] = random.choice(endless_questions)
        else:
            session['endless_current_question'] = random.choice(questions)
        return redirect(url_for('endless_game'))
    
    return render_template('endless.html',
                          question=question,
                          q_number=total_answered + 1,
                          streak=streak,
                          score=score,
                          player_hp=player_hp,
                          highest_streak=highest_streak,
                          total_questions=100,
                          time_left=time_left)

@app.route('/endless_result', methods=['GET', 'POST'])
def endless_result():
    # Check if Endless Mode is enabled
    settings = get_current_game_settings()
    if not settings.get('endless_mode_enabled', True):
        flash('Endless Mode is currently disabled.', 'error')
        return redirect(url_for('index'))
    
    score = session.get('endless_score', 0)
    highest_streak = session.get('endless_highest_streak', 0)
    total_answered = session.get('endless_total_answered', 0)
    correct = session.get('endless_correct', 0)
    wrong = session.get('endless_wrong', 0)
    total_time = time.time() - session.get('endless_start_time', time.time())
    player_name = session.get('player_name', None)
    feedback_list = session.get('endless_feedback_list', [])
    
    if request.method == 'POST':
        if not player_name:
            player_name = request.form.get('player_name', 'Anonymous')
            session['player_name'] = player_name
        save_leaderboard(player_name, score, total_time, correct, wrong, "endless")
        
        # Save student progress if logged in
        if session.get('is_student') and session.get('student_id'):
            student_id = session.get('student_id')
            update_student_progress(
                student_id=student_id,
                game_type='endless_mode',
                level=None,
                score=score,
                correct_answers=correct,
                total_questions=total_answered,
                time_taken=total_time
            )
        
        # Clear session state for endless mode
        session.pop('endless_score', None)
        session.pop('endless_hp', None)
        session.pop('endless_streak', None)
        session.pop('endless_highest_streak', None)
        session.pop('endless_total_answered', None)
        session.pop('endless_correct', None)
        session.pop('endless_wrong', None)
        session.pop('endless_start_time', None)
        session.pop('endless_score_initialized', None)
        session.pop('endless_question_start', None)
        session.pop('endless_current_question', None)
        session.pop('endless_feedback_list', None)
        session.pop('player_name', None)
        return redirect(url_for('leaderboard'))
    return render_template('endless_result.html',
                          score=score,
                          highest_streak=highest_streak,
                          total_questions=total_answered,
                          correct=correct,
                          wrong=wrong,
                          total_time=round(total_time, 2),
                          player_name=player_name,
                          feedback_list=feedback_list)


@app.route('/set_name', methods=['POST'])
def set_name():
    # Simple endpoint to set player's name in session
    name = request.form.get('player_name', '').strip()
    if not name:
        name = 'Anonymous'
    session['player_name'] = name
    # Return to the referring page (or index)
    return redirect(request.referrer or url_for('index'))

@app.route('/check_guest_name')
def check_guest_name():
    """Check if guest player already has a name stored in session"""
    # If user is a student, they don't need a guest name
    if session.get('is_student'):
        return jsonify({'has_name': True})
    
    # Check if guest has a name stored (and it's not just "Anonymous")
    player_name = session.get('player_name', '')
    has_name = bool(player_name and player_name.strip() and player_name.strip() != 'Anonymous')
    
    return jsonify({'has_name': has_name, 'name': player_name if has_name else None})

@app.route('/change_guest_name', methods=['GET', 'POST'])
def change_guest_name():
    """Allow guest players to change their name"""
    if request.method == 'POST':
        name = request.form.get('player_name', '').strip()
        if not name:
            name = 'Anonymous'
        session['player_name'] = name
        flash(f'Name updated to: {name}', 'success')
        return redirect(url_for('index'))
    
    current_name = session.get('player_name', 'Anonymous')
    return render_template('change_name.html', current_name=current_name)

@app.route('/load_progress', methods=['POST'])
def load_progress():
    """Load auto-saved progress for a player"""
    player_name = request.form.get('player_name', '').strip()
    if not player_name:
        return redirect(url_for('index'))
    
    settings = get_current_game_settings()
    if not settings.get('auto_save', True):
        return redirect(url_for('index'))
    
    progress_data = load_auto_save_progress(player_name)
    if progress_data:
        # Restore session state from auto-save
        session['player_name'] = progress_data['player_name']
        session['selected_level'] = progress_data['selected_level']
        session['score'] = progress_data['score']
        session['player_hp'] = progress_data['player_hp']
        session['enemy_hp'] = progress_data['enemy_hp']
        session['q_index'] = progress_data['q_index']
        session['correct_answers'] = progress_data['correct_answers']
        session['wrong_answers'] = progress_data['wrong_answers']
        session['highest_unlocked'] = progress_data['highest_unlocked']
        session['level_completed'] = progress_data.get('level_completed', False)
        # Restore character selection if it was saved
        if progress_data.get('character'):
            session['character'] = progress_data['character']
        
        # Reset timing info for current session
        session["level_start_time"] = time.time()
        session["game_start_time"] = time.time()
        settings = get_current_game_settings()
        session['current_timer'] = settings.get('question_time_limit', 30)
        
        flash('Progress loaded successfully!', 'success')
        
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
            # Non-student user (guest) - check if they already have a character
            if session.get('character'):
                # Guest already has a character, go directly to game
                return redirect(url_for('game'))
            else:
                # Guest needs to choose a character first
                return redirect(url_for('choose_character'))
    else:
        flash('No saved progress found or save file too old.', 'error')
        return redirect(url_for('index'))

@app.route('/check_auto_save/<player_name>')
def check_auto_save(player_name):
    """Check if auto-save exists for a player (AJAX endpoint)"""
    settings = get_current_game_settings()
    if not settings.get('auto_save', True):
        return jsonify({'exists': False})
    
    progress_data = load_auto_save_progress(player_name)
    return jsonify({
        'exists': progress_data is not None,
        'level': progress_data['selected_level'] if progress_data else None,
        'score': progress_data['score'] if progress_data else None,
        'timestamp': progress_data['timestamp'] if progress_data else None
    })

# =============== TEACHER PORTAL ROUTES ===============

@app.route('/teacher/login', methods=['GET', 'POST'])
def teacher_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username in TEACHER_CREDENTIALS and TEACHER_CREDENTIALS[username] == password:
            session['teacher_logged_in'] = True
            session['teacher_username'] = username
            return redirect(url_for('teacher_dashboard'))
        else:
            return render_template('teacher_login.html', error='Invalid credentials')
    
    return render_template('teacher_login.html')

@app.route('/teacher/logout')
def teacher_logout():
    session.pop('teacher_logged_in', None)
    session.pop('teacher_username', None)
    return redirect(url_for('index'))

@app.route('/teacher/dashboard')
@teacher_required
def teacher_dashboard():
    # Calculate statistics
    stats = {
        'total_questions': len(questions),
        'total_students': len(get_leaderboard_data()),
        'avg_score': calculate_average_score(),
        'ai_questions': count_ai_generated_questions()
    }
    return render_template('teacher_dashboard.html', stats=stats)

@app.route('/teacher/ai-generator', methods=['GET', 'POST'])
@teacher_required
def teacher_ai_generator():
    if request.method == 'POST':
        if 'file' not in request.files:
            return render_template('teacher_ai_generator.html', error='No file selected')
        
        file = request.files['file']
        if file.filename == '':
            return render_template('teacher_ai_generator.html', error='No file selected')
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            
            # Extract content from file
            content = extract_text_from_file(file_path)
            
            # Truncate content if too long to prevent token issues
            max_content_length = 8000  # Leave room for prompt and response
            if len(content) > max_content_length:
                content = content[:max_content_length] + "\n[Content truncated for processing...]"
                print(f"DEBUG: Content truncated from {len(extract_text_from_file(file_path))} to {len(content)} characters")
            
            print(f"DEBUG: Processing file content of {len(content)} characters")
            
            # Get form data
            topic = request.form.get('topic')
            difficulty = request.form.get('difficulty')
            question_count = int(request.form.get('question_count', 10))
            context = request.form.get('context', '')
            
            # Get selected question types
            selected_question_types = request.form.getlist('question_types')
            if not selected_question_types:
                selected_question_types = ["short_answer", "multiple_choice", "true_false"]
            
            # Generate questions with AI
            generated_questions = generate_questions_with_ai(content, topic, difficulty, question_count, context, selected_question_types)
            
            # Clean up uploaded file
            os.remove(file_path)
            
            if isinstance(generated_questions, dict) and 'error' in generated_questions:
                return render_template('teacher_ai_generator.html', error=generated_questions['error'])
            
            return render_template('teacher_ai_generator.html', generated_questions=generated_questions)
        else:
            return render_template('teacher_ai_generator.html', error='Invalid file type')
    
    return render_template('teacher_ai_generator.html')

@app.route('/teacher/save-questions', methods=['POST'])
@teacher_required
def teacher_save_questions():
    print("DEBUG: teacher_save_questions function called!")
    try:
        # Get all questions as one JSON string and selected indices
        all_questions_json = request.form.get('all_questions', '[]')
        selected_indices = request.form.getlist('selected_questions')
        
        print(f"DEBUG: Saving questions - {len(selected_indices)} selected")
        print(f"DEBUG: Selected indices: {selected_indices}")
        print(f"DEBUG: All questions JSON length: {len(all_questions_json)}")
        print(f"DEBUG: First 200 chars of JSON: {repr(all_questions_json[:200])}")
        print(f"DEBUG: Last 100 chars of JSON: {repr(all_questions_json[-100:])}")
        
        # Try to parse the questions JSON
        try:
            all_questions = json.loads(all_questions_json)
            print(f"DEBUG: Successfully parsed {len(all_questions)} questions from JSON")
        except json.JSONDecodeError as e:
            print(f"DEBUG: JSON parse error: {e}")
            print(f"DEBUG: Error at position {e.pos}")
            print(f"DEBUG: Context around error: {repr(all_questions_json[max(0, e.pos-50):e.pos+50])}")
            # Try to fix common HTML encoding issues
            import html
            decoded_json = html.unescape(all_questions_json)
            print(f"DEBUG: Trying HTML decoded version: {repr(decoded_json[:200])}")
            all_questions = json.loads(decoded_json)
            print(f"DEBUG: Successfully parsed after HTML decode: {len(all_questions)} questions")
        
        # Load existing questions
        with open('data/questions.json', 'r', encoding='utf-8') as f:
            existing_questions = json.load(f)
        
        print(f"DEBUG: Loaded {len(existing_questions)} existing questions")
        
        # Find the next available ID
        next_id = max([q.get('id', 0) for q in existing_questions]) + 1
        
        # Add selected questions
        saved_count = 0
        for index_str in selected_indices:
            try:
                index = int(index_str)
                if index < len(all_questions):
                    question_data = all_questions[index]
                    print(f"DEBUG: Processing question {index}: {question_data.get('q', 'No question text')[:50]}...")
                    
                    # Create properly formatted question (matching standard format)
                    formatted_question = {
                        "id": next_id,
                        "q": question_data.get('q'),
                        "answer": question_data.get('answer'),
                        "keywords": question_data.get('keywords', []),
                        "feedback": question_data.get('feedback', ''),
                        "type": question_data.get('type', 'short_answer'),
                        "options": question_data.get('options', []),
                        "difficulty": question_data.get('difficulty', 'medium'),
                        "ai_generated": True
                    }
                    
                    existing_questions.append(formatted_question)
                    next_id += 1
                    saved_count += 1
                    print(f"DEBUG: Successfully processed question {index}")
                else:
                    print(f"DEBUG: Index {index} out of range (max: {len(all_questions)-1})")
                
            except Exception as e:
                print(f"DEBUG: Error processing question {index}: {str(e)}")
                continue
        
        # Save updated questions
        with open('data/questions.json', 'w', encoding='utf-8') as f:
            json.dump(existing_questions, f, indent=2, ensure_ascii=False)
        
        print(f"DEBUG: Saved {saved_count} questions to file")
        
        # Reload global questions variable
        global questions
        questions = existing_questions
        print(f"DEBUG: Reloaded global questions, now {len(questions)} total")
        print(f"DEBUG: AI questions count: {sum(1 for q in questions if q.get('ai_generated', False))}")
        
        # Recreate search index
        recreate_search_index()
        
        flash(f'Successfully added {saved_count} questions to the question bank!')
        return redirect(url_for('teacher_dashboard'))
        
    except Exception as e:
        print(f"DEBUG: Error in save_questions: {str(e)}")
        return render_template('teacher_ai_generator.html', error=f'Error saving questions: {str(e)}')

@app.route('/teacher/ai-grading')
@teacher_required
def teacher_ai_grading():
    config = {
        'ai_model': session.get('ai_model', AI_MODEL),
        'confidence_threshold': session.get('confidence_threshold', 80),
        'custom_prompt': session.get('custom_prompt', '')
    }
    
    ai_grading_enabled = session.get('ai_grading_enabled', False)
    
    # Check if AI API is properly configured based on provider
    if AI_PROVIDER == "gemini":
        api_key_configured = bool(GEMINI_API_KEY and GEMINI_API_KEY != 'your-gemini-api-key-here')
    elif AI_PROVIDER == "openai":
        api_key_configured = bool(OPENAI_API_KEY and OPENAI_API_KEY != 'your-openai-api-key-here')
    else:
        api_key_configured = False
    
    return render_template('teacher_ai_grading.html', 
                         config=config, 
                         ai_grading_enabled=ai_grading_enabled,
                         api_key_configured=api_key_configured)

@app.route('/teacher/toggle-ai-grading', methods=['POST'])
@teacher_required
def teacher_toggle_ai_grading():
    enabled = 'ai_grading_enabled' in request.form
    session['ai_grading_enabled'] = enabled
    flash(f'AI Grading {"enabled" if enabled else "disabled"}!')
    return redirect(url_for('teacher_ai_grading'))

@app.route('/teacher/update-ai-config', methods=['POST'])
@teacher_required
def teacher_update_ai_config():
    session['ai_model'] = request.form.get('ai_model', AI_MODEL)
    session['confidence_threshold'] = int(request.form.get('confidence_threshold', 80))
    session['custom_prompt'] = request.form.get('custom_prompt', '')
    flash('AI configuration updated!')
    return redirect(url_for('teacher_ai_grading'))

@app.route('/teacher/test-ai-grading', methods=['POST'])
@teacher_required
def teacher_test_ai_grading():
    question = request.form.get('test_question')
    correct_answer = request.form.get('correct_answer')
    student_answer = request.form.get('student_answer')
    confidence_threshold = session.get('confidence_threshold', 80)
    
    # Test AI grading
    result = grade_answer_with_ai(question, correct_answer, student_answer, confidence_threshold)
    
    test_result = {
        'question': question,
        'expected': correct_answer,
        'student_answer': student_answer,
        'correct': result.get('correct', False),
        'confidence': result.get('confidence', 0),
        'explanation': result.get('explanation', 'No explanation provided')
    }
    
    config = {
        'ai_model': session.get('ai_model', AI_MODEL),
        'confidence_threshold': confidence_threshold,
        'custom_prompt': session.get('custom_prompt', '')
    }
    
    ai_grading_enabled = session.get('ai_grading_enabled', False)
    
    # Check if AI API is properly configured based on provider
    if AI_PROVIDER == "gemini":
        api_key_configured = bool(GEMINI_API_KEY and GEMINI_API_KEY != 'your-gemini-api-key-here')
    elif AI_PROVIDER == "openai":
        api_key_configured = bool(OPENAI_API_KEY and OPENAI_API_KEY != 'your-openai-api-key-here')
    else:
        api_key_configured = False
    
    return render_template('teacher_ai_grading.html', 
                         config=config, 
                         ai_grading_enabled=ai_grading_enabled,
                         api_key_configured=api_key_configured,
                         test_result=test_result)

# Placeholder routes for other teacher features
@app.route('/teacher/questions')
@teacher_required
def teacher_questions():
    # Make sure we have the latest questions
    global questions
    print(f"DEBUG: teacher_questions - using {len(questions)} questions")
    
    # Load questions and statistics
    stats = {
        'total_questions': len(questions),
        'ai_questions': sum(1 for q in questions if q.get('ai_generated', False)),
        'manual_questions': len(questions) - sum(1 for q in questions if q.get('ai_generated', False)),
        'levels_count': len(set(q.get('level', 1) for q in questions))
    }
    print(f"DEBUG: Stats - Total: {stats['total_questions']}, AI: {stats['ai_questions']}, Manual: {stats['manual_questions']}")
    return render_template('teacher_questions.html', questions=questions, **stats)

@app.route('/teacher/analytics')
@teacher_required
def teacher_analytics():
    # Load leaderboard and calculate analytics
    leaderboard = get_leaderboard_data()
    
    # Load registered students
    registered_students = load_students()
    registered_usernames = set(student.get('username', '') for student in registered_students)
    
    # Filter leaderboard to only include registered students
    registered_leaderboard = [
        entry for entry in leaderboard 
        if entry.get('player', 'Anonymous') in registered_usernames
    ]
    
    # Calculate statistics for registered students only
    total_students = len(set(entry.get('player', 'Anonymous') for entry in registered_leaderboard))
    total_attempts = len(registered_leaderboard)
    
    if registered_leaderboard:
        avg_score = sum(entry.get('score', 0) for entry in registered_leaderboard) / len(registered_leaderboard)
        avg_time = sum(entry.get('time', 0) for entry in registered_leaderboard) / len(registered_leaderboard) / 60  # in minutes
        
        # Performance distribution
        excellent_students = len([e for e in registered_leaderboard if e.get('score', 0) >= 80])
        good_students = len([e for e in registered_leaderboard if 60 <= e.get('score', 0) < 80])
        poor_students = len([e for e in registered_leaderboard if e.get('score', 0) < 60])
    else:
        avg_score = avg_time = 0
        excellent_students = good_students = poor_students = 0
    
    completion_rate = 85  # Placeholder
    engagement_score = 7.2  # Placeholder
    
    # Mock difficulty performance data
    easy_success = 78
    medium_success = 65
    hard_success = 45
    easy_attempts = medium_attempts = hard_attempts = 150
    
    # Question Pool Analytics
    pools_data = load_question_pools()
    pool_analytics = {}
    
    for pool_name, pool in pools_data["pools"].items():
        pool_questions = get_questions_for_pool(pool_name)
        pool_analytics[pool_name] = {
            "name": pool["name"],
            "enabled": pool.get("enabled", True),
            "total_questions": len(pool_questions),
            "assigned_questions": len(pool.get("question_ids", [])),
            "usage_stats": {
                "total_attempts": len([e for e in registered_leaderboard if e.get('game_mode') == pool_name]),
                "avg_performance": sum([e.get('score', 0) for e in registered_leaderboard if e.get('game_mode') == pool_name]) / max(1, len([e for e in registered_leaderboard if e.get('game_mode') == pool_name]))
            }
        }
    
    # Mock challenging questions
    challenging_questions = []
    for i, question in enumerate(questions[:5]):
        challenging_questions.append({
            'id': question.get('id', i+1),
            'q': question.get('q', ''),
            'answer': question.get('answer', ''),
            'success_rate': 45 + i * 5,
            'total_attempts': 25 - i * 2
        })
    
    # Recent activity (only registered students)
    recent_activity = []
    for i, entry in enumerate(registered_leaderboard[-10:]):
        recent_activity.append({
            'date': '2025-11-04',
            'player': entry.get('player', 'Anonymous'),
            'score': entry.get('score', 0),
            'mode': 'Main Game',
            'time': entry.get('time', 0),
            'completed': entry.get('score', 0) > 50
        })
    
    analytics_data = {
        'total_students': total_students,
        'total_registered_students': len(registered_students),
        'avg_score': int(avg_score) if avg_score else 0,
        'total_attempts': total_attempts,
        'avg_time': int(avg_time) if avg_time else 0,
        'completion_rate': completion_rate,
        'engagement_score': engagement_score,
        'excellent_students': excellent_students,
        'good_students': good_students,
        'poor_students': poor_students,
        'easy_success': easy_success,
        'medium_success': medium_success,
        'hard_success': hard_success,
        'easy_attempts': easy_attempts,
        'medium_attempts': medium_attempts,
        'hard_attempts': hard_attempts,
        'leaderboard': sorted(registered_leaderboard, key=lambda x: x.get('score', 0), reverse=True),
        'challenging_questions': challenging_questions,
        'recent_activity': recent_activity,
        'pool_analytics': pool_analytics,
        'show_registered_only': True
    }
    
    return render_template('teacher_analytics.html', **analytics_data)

@app.route('/teacher/levels')
@teacher_required
def teacher_levels():
    # Load levels and enemies
    try:
        with open("data/levels.json", "r", encoding="utf-8") as f:
            levels = json.load(f)
    except:
        levels = []
    
    try:
        with open('data/enemies.json', encoding='utf-8') as f:
            enemies = json.load(f)
    except:
        enemies = []
    
    # Create a question dictionary for lookup
    questions_dict = {q.get('id'): q for q in questions}
    
    # Calculate statistics
    total_questions = len(questions)
    avg_questions_per_level = total_questions / len(levels) if levels else 0
    available_questions = [q for q in questions if q.get('id')]
    
    template_data = {
        'levels': levels,
        'enemies': enemies,
        'questions_dict': questions_dict,
        'total_questions': total_questions,
        'avg_questions_per_level': int(avg_questions_per_level),
        'available_questions': available_questions
    }
    
    return render_template('teacher_levels.html', **template_data)

@app.route('/teacher/settings')
@teacher_required
def teacher_settings():
    # Load current settings from file
    settings = load_game_settings()
    return render_template('teacher_settings.html', settings=settings)

# Additional teacher portal routes for full functionality
@app.route('/teacher/add-question', methods=['POST'])
@teacher_required
def teacher_add_question():
    try:
        # Get form data
        question_text = request.form.get('question')
        answer = request.form.get('answer')
        keywords = request.form.get('keywords', '')
        difficulty = request.form.get('difficulty', 'medium')
        feedback = request.form.get('feedback', '')
        
        # Load existing questions
        with open('data/questions.json', 'r', encoding='utf-8') as f:
            existing_questions = json.load(f)
        
        # Find next ID
        next_id = max([q.get('id', 0) for q in existing_questions]) + 1
        
        # Get question type and options
        question_type = request.form.get('question_type', 'short_answer')
        options = []
        if question_type == 'multiple_choice':
            # Get multiple choice options
            for i in range(1, 5):  # Support up to 4 options
                option = request.form.get(f'option_{i}', '').strip()
                if option:
                    options.append(option)
        
        # Create new question
        new_question = {
            'id': next_id,
            'q': question_text,
            'answer': answer,
            'keywords': [k.strip() for k in keywords.split(',') if k.strip()],
            'difficulty': difficulty,
            'feedback': feedback,
            'type': question_type,
            'options': options if question_type == 'multiple_choice' else [],
            'ai_generated': False
        }
        
        existing_questions.append(new_question)
        
        # Save questions
        with open('data/questions.json', 'w', encoding='utf-8') as f:
            json.dump(existing_questions, f, indent=2, ensure_ascii=False)
        
        flash('Question added successfully!')
        return redirect(url_for('teacher_questions'))
        
    except Exception as e:
        flash(f'Error adding question: {str(e)}')
        return redirect(url_for('teacher_questions'))

@app.route('/teacher/get-question/<int:question_id>')
@teacher_required
def teacher_get_question(question_id):
    question = next((q for q in questions if q.get('id') == question_id), None)
    if question:
        return jsonify(question)
    return jsonify({'error': 'Question not found'}), 404

@app.route('/teacher/edit-question', methods=['POST'])
@teacher_required
def teacher_edit_question():
    try:
        question_id = int(request.form.get('question_id'))
        
        # Load questions
        with open('data/questions.json', 'r', encoding='utf-8') as f:
            all_questions = json.load(f)
        
        # Get question type and options for editing
        question_type = request.form.get('question_type', 'short_answer')
        options = []
        if question_type == 'multiple_choice':
            # Get multiple choice options
            for i in range(1, 5):  # Support up to 4 options
                option = request.form.get(f'option_{i}', '').strip()
                if option:
                    options.append(option)
        
        # Find and update question
        for i, q in enumerate(all_questions):
            if q.get('id') == question_id:
                all_questions[i].update({
                    'q': request.form.get('question'),
                    'answer': request.form.get('answer'),
                    'keywords': [k.strip() for k in request.form.get('keywords', '').split(',') if k.strip()],
                    'difficulty': request.form.get('difficulty', 'medium'),
                    'feedback': request.form.get('feedback', ''),
                    'type': question_type,
                    'options': options if question_type == 'multiple_choice' else []
                })
                break
        
        # Save questions
        with open('data/questions.json', 'w', encoding='utf-8') as f:
            json.dump(all_questions, f, indent=2, ensure_ascii=False)
        
        flash('Question updated successfully!')
        return redirect(url_for('teacher_questions'))
        
    except Exception as e:
        flash(f'Error updating question: {str(e)}')
        return redirect(url_for('teacher_questions'))

@app.route('/teacher/delete-question/<int:question_id>', methods=['POST'])
@teacher_required
def teacher_delete_question(question_id):
    try:
        # Load questions
        with open('data/questions.json', 'r', encoding='utf-8') as f:
            all_questions = json.load(f)
        
        # Remove question
        all_questions = [q for q in all_questions if q.get('id') != question_id]
        
        # Save questions
        with open('data/questions.json', 'w', encoding='utf-8') as f:
            json.dump(all_questions, f, indent=2, ensure_ascii=False)
        
        return jsonify({'success': True})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/teacher/update-settings', methods=['POST'])
@teacher_required
def teacher_update_settings():
    try:
        # Load current settings to compare changes
        current_settings = load_game_settings()
        
        # Get form data and create settings dictionary
        new_settings = {
            'base_player_hp': int(request.form.get('base_player_hp', 100)),
            'base_enemy_hp': int(request.form.get('base_enemy_hp', 50)),
            'base_damage': int(request.form.get('base_damage', 10)),
            'question_time_limit': int(request.form.get('question_time_limit', 30)),
            'questions_per_level': int(request.form.get('questions_per_level', 10)),
            'points_correct': int(request.form.get('points_correct', 10)),
            'points_wrong': int(request.form.get('points_wrong', 5)),
            'speed_bonus': 'speed_bonus' in request.form,
            'level_bonus': int(request.form.get('level_bonus', 20)),
            'adaptive_difficulty': 'adaptive_difficulty' in request.form,
            'min_accuracy': int(request.form.get('min_accuracy', 70)),
            'sound_effects': 'sound_effects' in request.form,
            'show_timer': 'show_timer' in request.form,
            'show_progress': 'show_progress' in request.form,
            'animation_speed': request.form.get('animation_speed', 'normal'),
            'debug_mode': 'debug_mode' in request.form,
            'analytics_enabled': 'analytics_enabled' in request.form,
            'auto_save': 'auto_save' in request.form,
            'session_timeout': int(request.form.get('session_timeout', 30)),
            'timeout_behavior': request.form.get('timeout_behavior', 'penalty')
        }
        
        # Compare settings to find changes
        changed_settings = []
        for key, new_value in new_settings.items():
            if current_settings.get(key) != new_value:
                changed_settings.append(key)
        
        # Save settings to file
        settings_file = 'data/game_settings.json'
        with open(settings_file, 'w', encoding='utf-8') as f:
            json.dump(new_settings, f, indent=2, ensure_ascii=False)
        
        # Update global constants
        global BASE_DAMAGE, BASE_ENEMY_HP, LEVEL_TIME_LIMIT
        BASE_DAMAGE = new_settings['base_damage']
        BASE_ENEMY_HP = new_settings['base_enemy_hp']
        LEVEL_TIME_LIMIT = new_settings['question_time_limit']
        
        flash('Settings updated successfully!')
        return jsonify({'success': True, 'changed_settings': changed_settings})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/teacher/clear-progress', methods=['POST'])
@teacher_required
def teacher_clear_progress():
    try:
        # Clear leaderboard
        with open('data/leaderboard.json', 'w', encoding='utf-8') as f:
            json.dump([], f)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/teacher/clear-leaderboard', methods=['POST'])
@teacher_required
def teacher_clear_leaderboard():
    try:
        with open('data/leaderboard.json', 'w', encoding='utf-8') as f:
            json.dump([], f)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/teacher/add-level', methods=['POST'])
@teacher_required
def teacher_add_level():
    try:
        # Get form data
        difficulty = request.form.get('difficulty', 'Easy')
        selected_questions = request.form.getlist('questions')
        
        # Load existing levels
        with open('data/levels.json', 'r', encoding='utf-8') as f:
            levels = json.load(f)
        
        # Find the next level number
        next_level = max([level['level'] for level in levels]) + 1
        
        # Convert question IDs to integers
        question_ids = [int(qid) for qid in selected_questions]
        
        # Create new level
        new_level = {
            "level": next_level,
            "difficulty": difficulty,
            "questions": question_ids
        }
        
        levels.append(new_level)
        
        # Save updated levels
        with open('data/levels.json', 'w', encoding='utf-8') as f:
            json.dump(levels, f, indent=2, ensure_ascii=False)
        
        flash(f'Level {next_level} added successfully with {len(question_ids)} questions!')
        return redirect(url_for('teacher_levels'))
    except Exception as e:
        flash(f'Error adding level: {str(e)}')
        return redirect(url_for('teacher_levels'))

@app.route('/teacher/edit-level', methods=['POST'])
@teacher_required
def teacher_edit_level():
    try:
        # Get form data
        level_id = int(request.form.get('level_number'))  # HTML template uses 'level_number'
        difficulty = request.form.get('difficulty', 'Easy')
        selected_questions = request.form.getlist('questions')
        
        print(f"DEBUG: Edit level {level_id}")
        print(f"DEBUG: New difficulty: {difficulty}")
        print(f"DEBUG: Selected questions: {selected_questions}")
        
        # Load existing levels
        with open('data/levels.json', 'r', encoding='utf-8') as f:
            levels = json.load(f)
        
        print(f"DEBUG: Loaded {len(levels)} levels")
        
        # Find and update the level
        level_found = False
        for level in levels:
            if level['level'] == level_id:
                print(f"DEBUG: Found level {level_id}, old questions: {level['questions']}")
                level['difficulty'] = difficulty
                level['questions'] = [int(qid) for qid in selected_questions]
                level_found = True
                print(f"DEBUG: Updated level {level_id}, new questions: {level['questions']}")
                break
        
        if not level_found:
            print(f"DEBUG: Level {level_id} not found in levels!")
            flash(f'Level {level_id} not found!')
            return redirect(url_for('teacher_levels'))
        
        # Save updated levels
        with open('data/levels.json', 'w', encoding='utf-8') as f:
            json.dump(levels, f, indent=2, ensure_ascii=False)
        
        print(f"DEBUG: Saved levels.json successfully")
        flash(f'Level {level_id} updated successfully with {len(selected_questions)} questions!')
        return redirect(url_for('teacher_levels'))
    except Exception as e:
        flash(f'Error updating level: {str(e)}')
        return redirect(url_for('teacher_levels'))

@app.route('/teacher/get-level/<int:level_id>')
@teacher_required
def teacher_get_level(level_id):
    try:
        # Load levels and return specific level data
        with open("data/levels.json", "r", encoding="utf-8") as f:
            levels = json.load(f)
        
        level = next((l for l in levels if l.get('level') == level_id), None)
        if level:
            return jsonify(level)
        return jsonify({'error': 'Level not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/teacher/level-questions', methods=['POST'])
@teacher_required
def teacher_level_questions():
    try:
        # Get form data
        level_id = int(request.form.get('level_number'))  # HTML template uses 'level_number'
        selected_questions = request.form.getlist('questions')
        
        # Load existing levels
        with open('data/levels.json', 'r', encoding='utf-8') as f:
            levels = json.load(f)
        
        # Find and update the level's questions
        level_found = False
        for level in levels:
            if level['level'] == level_id:
                level['questions'] = [int(qid) for qid in selected_questions]
                level_found = True
                break
        
        if not level_found:
            flash(f'Level {level_id} not found!')
            return redirect(url_for('teacher_levels'))
        
        # Save updated levels
        with open('data/levels.json', 'w', encoding='utf-8') as f:
            json.dump(levels, f, indent=2, ensure_ascii=False)
        
        flash(f'Questions for Level {level_id} updated successfully! Now has {len(selected_questions)} questions.')
        return redirect(url_for('teacher_levels'))
    except Exception as e:
        flash(f'Error updating level questions: {str(e)}')
        return redirect(url_for('teacher_levels'))

@app.route('/teacher/delete-level/<int:level_id>', methods=['POST'])
@teacher_required
def teacher_delete_level(level_id):
    try:
        # Load existing levels
        with open('data/levels.json', 'r', encoding='utf-8') as f:
            levels = json.load(f)
        
        # Find and remove the level
        original_count = len(levels)
        levels = [level for level in levels if level['level'] != level_id]
        
        if len(levels) == original_count:
            return jsonify({'success': False, 'error': f'Level {level_id} not found'})
        
        # Save updated levels
        with open('data/levels.json', 'w', encoding='utf-8') as f:
            json.dump(levels, f, indent=2, ensure_ascii=False)
        
        return jsonify({'success': True, 'message': f'Level {level_id} deleted successfully'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# Student Management Routes
@app.route('/teacher/students')
@teacher_required
def teacher_students():
    students = load_students()
    progress_data = load_student_progress()
    
    # Add progress summary to each student
    for student in students:
        student_progress = progress_data.get(student['id'], {})
        student['games_played'] = student_progress.get('games_played', 0)
        student['best_score'] = student_progress.get('best_score', 0)
        student['average_accuracy'] = student_progress.get('stats', {}).get('average_accuracy', 0)
    
    return render_template('teacher_students.html', students=students)

@app.route('/teacher/add-student', methods=['POST'])
@teacher_required
def teacher_add_student():
    try:
        username = request.form['username'].strip()
        password = request.form['password'].strip()
        full_name = request.form['full_name'].strip()
        email = request.form.get('email', '').strip()
        
        if not username or not password or not full_name:
            flash('Username, password, and full name are required.', 'error')
            return redirect(url_for('teacher_students'))
        
        success, result = create_student(username, password, full_name, email)
        
        if success:
            flash(f'Student "{full_name}" created successfully! Student ID: {result}', 'success')
        else:
            flash(f'Error creating student: {result}', 'error')
    
    except Exception as e:
        flash(f'Error adding student: {str(e)}', 'error')
    
    return redirect(url_for('teacher_students'))

@app.route('/teacher/edit-student', methods=['POST'])
@teacher_required
def teacher_edit_student():
    try:
        student_id = request.form['student_id']
        username = request.form['username'].strip()
        password = request.form['password'].strip()
        full_name = request.form['full_name'].strip()
        email = request.form.get('email', '').strip()
        active = request.form.get('active') == 'on'
        
        students = load_students()
        student = next((s for s in students if s['id'] == student_id), None)
        
        if not student:
            flash('Student not found.', 'error')
            return redirect(url_for('teacher_students'))
        
        # Check if username is already taken by another student
        if any(s['username'] == username and s['id'] != student_id for s in students):
            flash('Username already exists.', 'error')
            return redirect(url_for('teacher_students'))
        
        # Update student data
        student['username'] = username
        if password:  # Only update password if provided
            student['password'] = password
        student['full_name'] = full_name
        student['email'] = email
        student['active'] = active
        
        if save_students(students):
            flash(f'Student "{full_name}" updated successfully!', 'success')
        else:
            flash('Error saving student data.', 'error')
    
    except Exception as e:
        flash(f'Error updating student: {str(e)}', 'error')
    
    return redirect(url_for('teacher_students'))

@app.route('/teacher/delete-student/<student_id>', methods=['POST'])
@teacher_required
def teacher_delete_student(student_id):
    try:
        students = load_students()
        original_count = len(students)
        students = [s for s in students if s['id'] != student_id]
        
        if len(students) == original_count:
            return jsonify({'success': False, 'error': 'Student not found'})
        
        if save_students(students):
            # Also remove student's progress data
            progress_data = load_student_progress()
            if student_id in progress_data:
                del progress_data[student_id]
                save_student_progress(progress_data)
            
            return jsonify({'success': True, 'message': 'Student deleted successfully'})
        else:
            return jsonify({'success': False, 'error': 'Error saving data'})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/teacher/student-progress/<student_id>')
@teacher_required
def teacher_student_progress(student_id):
    student = get_student_by_id(student_id)
    if not student:
        flash('Student not found.', 'error')
        return redirect(url_for('teacher_students'))
    
    progress = get_student_progress(student_id)
    return render_template('teacher_student_progress.html', student=student, progress=progress)

# Student Authentication Routes
@app.route('/student/login', methods=['GET', 'POST'])
def student_login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()
        
        student = authenticate_student(username, password)
        if student:
            session['student_id'] = student['id']
            session['student_username'] = student['username']
            session['student_name'] = student['full_name']
            session['is_student'] = True
            
            # Load their saved character if they have one
            if 'selected_character' in student:
                session['character'] = student['selected_character']
            
            flash(f'Welcome back, {student["full_name"]}!', 'success')
            return redirect(url_for('student_dashboard'))
        else:
            flash('Invalid username or password.', 'error')
    
    return render_template('student_login.html')

@app.route('/student/logout')
def student_logout():
    # Clear student session
    for key in list(session.keys()):
        if key.startswith('student_') or key == 'is_student':
            session.pop(key, None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('student_login'))

@app.route('/check_student_session')
def check_student_session():
    """Check if a student is currently logged in"""
    is_logged_in = session.get('is_student', False) and 'student_id' in session
    return jsonify({
        'logged_in': is_logged_in,
        'student_name': session.get('student_name', '') if is_logged_in else ''
    })

@app.route('/student/dashboard')
def student_dashboard():
    if not session.get('is_student'):
        flash('Please log in to access your dashboard.', 'error')
        return redirect(url_for('student_login'))
    
    student_id = session.get('student_id')
    student = get_student_by_id(student_id)
    progress = get_student_progress(student_id)
    
    # Get settings to check available game modes
    settings = get_current_game_settings()
    
    # Get selected character info
    selected_character = student.get('selected_character') if student else None
    
    return render_template('student_dashboard.html', 
                         student=student, 
                         progress=progress, 
                         settings=settings,
                         selected_character=selected_character)

@app.route('/student/profile', methods=['GET', 'POST'])
def student_profile():
    if not session.get('is_student'):
        flash('Please log in to access your profile.', 'error')
        return redirect(url_for('student_login'))
    
    student_id = session.get('student_id')
    student = get_student_by_id(student_id)
    
    if not student:
        flash('Student account not found.', 'error')
        return redirect(url_for('student_login'))
    
    if request.method == 'POST':
        # Get form data
        new_username = request.form.get('username', '').strip()
        new_email = request.form.get('email', '').strip()
        current_password = request.form.get('current_password', '').strip()
        new_password = request.form.get('new_password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()
        
        # Validate current password
        if current_password != student['password']:
            flash('Current password is incorrect.', 'error')
            return render_template('student_profile.html', student=student)
        
        # Track username change for success message
        username_changed = False
        old_username = student['username']
        
        # Validate and update username
        if new_username != student['username']:
            if len(new_username) < 3 or len(new_username) > 50:
                flash('Username must be between 3-50 characters long.', 'error')
                return render_template('student_profile.html', student=student)
            
            # Check if username is already taken
            students = load_students()
            if any(s['username'].lower() == new_username.lower() and s['id'] != student_id for s in students):
                flash('Username is already taken. Please choose a different one.', 'error')
                return render_template('student_profile.html', student=student)
            
            # Update username
            student['username'] = new_username
            username_changed = True
            
            # Update leaderboard entries with new username
            update_leaderboard_username(old_username, new_username)
            
        # Update email
        student['email'] = new_email
        
        # Update password if provided
        if new_password:
            if new_password != confirm_password:
                flash('New passwords do not match.', 'error')
                return render_template('student_profile.html', student=student)
            
            if len(new_password) < 6:
                flash('Password must be at least 6 characters long.', 'error')
                return render_template('student_profile.html', student=student)
            
            student['password'] = new_password
        
        # Save updated student data
        students = load_students()
        for i, s in enumerate(students):
            if s['id'] == student_id:
                students[i] = student
                break
        
        if save_students(students):
            if username_changed:
                flash(f'Profile updated successfully! Username changed to "{new_username}"', 'success')
            else:
                flash('Profile updated successfully!', 'success')
        else:
            flash('Error updating profile. Please try again.', 'error')
    
    return render_template('student_profile.html', student=student)

# Helper functions for teacher portal
def load_game_settings():
    """Load game settings from JSON file or return defaults"""
    default_settings = {
        'base_player_hp': 100,
        'base_enemy_hp': 50,
        'base_damage': 10,
        'question_time_limit': 30,
        'questions_per_level': 10,
        'points_correct': 10,
        'points_wrong': 5,
        'speed_bonus': True,
        'level_bonus': 20,
        'adaptive_difficulty': False,
        'min_accuracy': 70,
        'sound_effects': False,
        'show_timer': True,
        'show_progress': True,
        'animation_speed': 'normal',
        'debug_mode': False,
        'analytics_enabled': True,
        'auto_save': True,
        'session_timeout': 30,
        'timeout_behavior': 'penalty',  # 'penalty' or 'fail'
        'test_yourself_enabled': True,
        'endless_mode_enabled': True
    }
    
    try:
        settings_file = 'data/game_settings.json'
        with open(settings_file, 'r', encoding='utf-8') as f:
            saved_settings = json.load(f)
        # Merge with defaults to ensure all keys exist
        default_settings.update(saved_settings)
        return default_settings
    except (FileNotFoundError, json.JSONDecodeError):
        return default_settings

def get_current_game_settings():
    """Get current game settings for use in game logic"""
    return load_game_settings()

def get_leaderboard_data():
    try:
        with open('data/leaderboard.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return []

def calculate_average_score():
    leaderboard = get_leaderboard_data()
    if not leaderboard:
        return 0
    total_score = sum(entry.get('score', 0) for entry in leaderboard)
    return round(total_score / len(leaderboard))

def count_ai_generated_questions():
    return sum(1 for q in questions if q.get('ai_generated', False))

# Student Management Functions
def load_students():
    """Load students from JSON file"""
    try:
        with open('data/students.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_students(students):
    """Save students to JSON file"""
    try:
        os.makedirs('data', exist_ok=True)
        with open('data/students.json', 'w', encoding='utf-8') as f:
            json.dump(students, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error saving students: {e}")
        return False

def create_student(username, password, full_name, email=None):
    """Create a new student account"""
    students = load_students()
    
    # Check if username already exists
    if any(s['username'] == username for s in students):
        return False, "Username already exists"
    
    # Generate unique student ID
    student_id = str(len(students) + 1).zfill(4)
    
    new_student = {
        'id': student_id,
        'username': username,
        'password': password,  # In production, this should be hashed
        'full_name': full_name,
        'email': email or '',
        'created_date': datetime.now().isoformat(),
        'last_login': None,
        'active': True
    }
    
    students.append(new_student)
    if save_students(students):
        return True, student_id
    return False, "Failed to save student"

def authenticate_student(username, password):
    """Authenticate student login"""
    students = load_students()
    for student in students:
        if student['username'] == username and student['password'] == password and student['active']:
            # Update last login
            student['last_login'] = datetime.now().isoformat()
            save_students(students)
            return student
    return None

def get_student_by_id(student_id):
    """Get student by ID"""
    students = load_students()
    return next((s for s in students if s['id'] == student_id), None)

def update_leaderboard_username(old_username, new_username):
    """Update username in leaderboard entries"""
    try:
        # Update main leaderboard
        leaderboard = load_leaderboard()
        updated = False
        for entry in leaderboard:
            if entry.get('player') == old_username:
                entry['player'] = new_username
                updated = True
        
        if updated:
            with open(LEADERBOARD_FILE, "w", encoding="utf-8") as f:
                json.dump(leaderboard, f, indent=4)
        
        # Update guest leaderboard if it exists
        try:
            with open('data/guest_leaderboard.json', 'r') as f:
                guest_leaderboard = json.load(f)
            for entry in guest_leaderboard:
                if entry.get('player') == old_username:
                    entry['player'] = new_username
            with open('data/guest_leaderboard.json', 'w') as f:
                json.dump(guest_leaderboard, f, indent=2)
        except FileNotFoundError:
            pass
            
    except Exception as e:
        print(f"Error updating leaderboard username: {e}")

def load_student_progress():
    """Load all student progress data"""
    try:
        with open('data/student_progress.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_student_progress(progress_data):
    """Save student progress data"""
    try:
        os.makedirs('data', exist_ok=True)
        with open('data/student_progress.json', 'w', encoding='utf-8') as f:
            json.dump(progress_data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error saving student progress: {e}")
        return False

def update_student_progress(student_id, game_type, level, score, correct_answers, total_questions, time_taken):
    """Update progress for a specific student"""
    progress_data = load_student_progress()
    
    if student_id not in progress_data:
        progress_data[student_id] = {
            'games_played': 0,
            'total_score': 0,
            'best_score': 0,
            'levels_completed': [],
            'game_history': [],
            'stats': {
                'total_correct': 0,
                'total_questions': 0,
                'average_accuracy': 0,
                'total_time': 0
            }
        }
    
    student_progress = progress_data[student_id]
    
    # Update game history
    game_record = {
        'date': datetime.now().isoformat(),
        'game_type': game_type,
        'level': level,
        'score': score,
        'correct_answers': correct_answers,
        'total_questions': total_questions,
        'time_taken': time_taken,
        'accuracy': round((correct_answers / total_questions) * 100, 2) if total_questions > 0 else 0
    }
    
    student_progress['game_history'].append(game_record)
    student_progress['games_played'] += 1
    student_progress['total_score'] += score
    
    # Update best score
    if score > student_progress['best_score']:
        student_progress['best_score'] = score
    
    # Update level completion
    if level and level not in student_progress['levels_completed']:
        student_progress['levels_completed'].append(level)
        student_progress['levels_completed'].sort()
    
    # Update stats
    student_progress['stats']['total_correct'] += correct_answers
    student_progress['stats']['total_questions'] += total_questions
    student_progress['stats']['total_time'] += time_taken
    
    if student_progress['stats']['total_questions'] > 0:
        student_progress['stats']['average_accuracy'] = round(
            (student_progress['stats']['total_correct'] / student_progress['stats']['total_questions']) * 100, 2
        )
    
    # Keep only last 50 games to prevent file from growing too large
    if len(student_progress['game_history']) > 50:
        student_progress['game_history'] = student_progress['game_history'][-50:]
    
    progress_data[student_id] = student_progress
    return save_student_progress(progress_data)

def get_student_progress(student_id):
    """Get progress for a specific student"""
    progress_data = load_student_progress()
    return progress_data.get(student_id, {
        'games_played': 0,
        'total_score': 0,
        'best_score': 0,
        'levels_completed': [],
        'game_history': [],
        'stats': {
            'total_correct': 0,
            'total_questions': 0,
            'average_accuracy': 0,
            'total_time': 0
        }
    })

def recreate_search_index():
    """Recreate the search index after adding new questions"""
    global ix
    try:
        # Remove existing index
        import shutil
        if os.path.exists("indexdir"):
            shutil.rmtree("indexdir")
        
        # Create new index
        ix = create_or_open_index()
        
        # Reload questions
        global questions
        with open('data/questions.json', 'r', encoding='utf-8') as f:
            questions = json.load(f)
        
        # Rebuild index
        from whoosh.writing import AsyncWriter
        writer = AsyncWriter(ix)
        for question in questions:
            raw_keywords = question.get('keywords', [])
            if isinstance(raw_keywords, str):
                keywords = [k.strip().lower() for k in raw_keywords.split(',') if k.strip()]
            else:
                keywords = [str(k).strip().lower() for k in raw_keywords]
            writer.add_document(
                id=str(question.get("id", "")),
                question=question.get("q", ""),
                answer=question.get("answer", ""),
                keywords=keywords
            )
        writer.commit()
    except Exception as e:
        print(f"Error recreating search index: {e}")

# Add teacher portal link to main navigation
@app.context_processor
def inject_teacher_link():
    return dict(show_teacher_link=True)

# ------------------- QUESTION POOL MANAGEMENT -------------------

def load_question_pools():
    """Load question pools configuration"""
    try:
        pools_file = os.path.join(os.path.dirname(__file__), 'data', 'question_pools.json')
        with open(pools_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # Return default pools if file doesn't exist
        return {
            "pools": {
                "endless_mode": {
                    "name": "Endless Mode Questions",
                    "description": "Questions used in endless survival mode",
                    "enabled": True,
                    "question_ids": [],
                    "settings": {
                        "difficulty_range": ["easy", "medium", "hard"],
                        "topics": ["all"],
                        "exclude_level_questions": False,
                        "randomize": True
                    }
                },
                "test_yourself": {
                    "name": "Test Yourself Questions",
                    "description": "Questions used in 40-question assessment mode", 
                    "enabled": True,
                    "question_ids": [],
                    "settings": {
                        "question_count": 40,
                        "difficulty_distribution": {"easy": 50, "medium": 35, "hard": 15},
                        "topics": ["all"],
                        "time_limit": 3600,
                        "randomize": True
                    }
                },
                "level_based": {
                    "name": "Level-Based Questions",
                    "description": "Questions organized by difficulty levels 1-10",
                    "enabled": True, 
                    "question_ids": [],
                    "settings": {
                        "questions_per_level": 10,
                        "adaptive_difficulty": True,
                        "unlock_progression": True
                    }
                }
            },
            "metadata": {
                "last_updated": datetime.now().isoformat(),
                "version": "1.0.0", 
                "total_pools": 3
            }
        }

def save_question_pools(pools_data):
    """Save question pools configuration"""
    pools_file = os.path.join(os.path.dirname(__file__), 'data', 'question_pools.json')
    pools_data["metadata"]["last_updated"] = datetime.now().isoformat()
    with open(pools_file, 'w', encoding='utf-8') as f:
        json.dump(pools_data, f, indent=2, ensure_ascii=False)

def get_questions_for_pool(pool_name):
    """Get questions assigned to a specific pool"""
    pools_data = load_question_pools()
    pool = pools_data["pools"].get(pool_name, {})
    
    if not pool.get("enabled", True):
        return []
    
    question_ids = pool.get("question_ids", [])
    
    # If no specific questions assigned, use all questions based on settings
    if not question_ids:
        pool_questions = []
        settings = pool.get("settings", {})
        
        for question in questions:
            # Apply difficulty filter if specified
            difficulty_range = settings.get("difficulty_range", ["easy", "medium", "hard"])
            question_difficulty = question.get("difficulty", "medium")
            
            if question_difficulty not in difficulty_range:
                continue
                
            # Apply topic filter if specified  
            topics = settings.get("topics", ["all"])
            if "all" not in topics:
                question_keywords = question.get("keywords", [])
                if isinstance(question_keywords, str):
                    question_keywords = [k.strip() for k in question_keywords.split(',')]
                
                if not any(topic.lower() in [k.lower() for k in question_keywords] for topic in topics):
                    continue
                    
            pool_questions.append(question)
            
        return pool_questions
    else:
        # Return questions with specific IDs
        id_to_question = {q['id']: q for q in questions}
        return [id_to_question[qid] for qid in question_ids if qid in id_to_question]

def initialize_question_pools():
    """Initialize question pools with existing questions if not already configured"""
    pools_data = load_question_pools()
    modified = False
    
    # Auto-assign questions to pools if they're empty
    for pool_name, pool in pools_data["pools"].items():
        if not pool.get("question_ids"):
            # Auto-assign based on question difficulty and level
            assigned_questions = []
            
            if pool_name == "endless_mode":
                # Assign questions from levels 1-8 (easier questions for endless mode)
                assigned_questions = [q["id"] for q in questions if q.get("id", 0) <= 80]
            elif pool_name == "test_yourself": 
                # Assign all questions for comprehensive testing
                assigned_questions = [q["id"] for q in questions]
            elif pool_name == "level_based":
                # Assign all questions (will be filtered by level system)
                assigned_questions = [q["id"] for q in questions]
                
            pool["question_ids"] = assigned_questions
            modified = True
    
    if modified:
        save_question_pools(pools_data)
    
    return pools_data

# Load question pools on startup
question_pools = initialize_question_pools()

# ------------------- TEACHER POOL MANAGEMENT ROUTES -------------------

@app.route('/teacher/question-pools')
@teacher_required
def teacher_question_pools():
    
    pools_data = load_question_pools()
    
    # Get statistics for each pool
    for pool_name, pool in pools_data["pools"].items():
        pool_questions = get_questions_for_pool(pool_name)
        pool["stats"] = {
            "total_questions": len(pool_questions),
            "assigned_questions": len(pool.get("question_ids", [])),
            "enabled": pool.get("enabled", True)
        }
    
    return render_template('teacher_question_pools.html', 
                         pools=pools_data["pools"], 
                         metadata=pools_data["metadata"],
                         all_questions=questions)

@app.route('/teacher/update-pool-settings', methods=['POST'])
@teacher_required
def teacher_update_pool_settings():
    
    try:
        pool_name = request.form.get('pool_name')
        pools_data = load_question_pools()
        
        if pool_name not in pools_data["pools"]:
            return jsonify({"error": "Pool not found"}), 404
            
        pool = pools_data["pools"][pool_name]
        
        # Update basic settings
        pool["enabled"] = request.form.get('enabled') == 'true'
        pool["name"] = request.form.get('name', pool["name"])
        pool["description"] = request.form.get('description', pool["description"])
        
        # Update pool-specific settings
        if pool_name == "test_yourself":
            pool["settings"]["question_count"] = int(request.form.get('question_count', 40))
            pool["settings"]["time_limit"] = int(request.form.get('time_limit', 3600))
        elif pool_name == "level_based":
            pool["settings"]["questions_per_level"] = int(request.form.get('questions_per_level', 10))
            pool["settings"]["adaptive_difficulty"] = request.form.get('adaptive_difficulty') == 'true'
        
        save_question_pools(pools_data)
        flash(f'Pool settings updated successfully for {pool["name"]}!', 'success')
        
    except Exception as e:
        flash(f'Error updating pool settings: {str(e)}', 'error')
    
    return redirect(url_for('teacher_question_pools'))

@app.route('/teacher/assign-questions-to-pool', methods=['POST'])
@teacher_required
def teacher_assign_questions_to_pool():
    
    try:
        pool_name = request.form.get('pool_name')
        question_ids = request.form.getlist('question_ids')
        question_ids = [int(qid) for qid in question_ids if qid.isdigit()]
        
        pools_data = load_question_pools()
        
        if pool_name not in pools_data["pools"]:
            return jsonify({"error": "Pool not found"}), 404
        
        pools_data["pools"][pool_name]["question_ids"] = question_ids
        save_question_pools(pools_data)
        
        flash(f'Successfully assigned {len(question_ids)} questions to {pools_data["pools"][pool_name]["name"]}!', 'success')
        
    except Exception as e:
        flash(f'Error assigning questions to pool: {str(e)}', 'error')
    
    return redirect(url_for('teacher_question_pools'))

# Run the Flask app
if __name__ == "__main__":
    print("🎮 Starting Quiz Battle: Dungeons of Knowledge")
    print("🌐 Server running at: http://127.0.0.1:5000")
    print("🎯 Ready for educational adventures!")
    app.run(debug=True, host='127.0.0.1', port=5000)
