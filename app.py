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
from functools import wraps
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from whoosh.fields import Schema, TEXT, ID
from whoosh import index
from config import TEACHER_CREDENTIALS, OPENAI_API_KEY, AI_MODEL, UPLOAD_FOLDER, ALLOWED_EXTENSIONS, MAX_CONTENT_LENGTH

# Constants
LEADERBOARD_FILE = "data/leaderboard.json"
BASE_DAMAGE = 10
BASE_ENEMY_HP = 50
LEVEL_TIME_LIMIT = 30

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
def call_openai_api(prompt, max_tokens=1000):
    """Call OpenAI API with error handling"""
    try:
        headers = {
            'Authorization': f'Bearer {OPENAI_API_KEY}',
            'Content-Type': 'application/json',
        }
        data = {
            'model': AI_MODEL,
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
        return f"Error calling AI API: {str(e)}"

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

def generate_questions_with_ai(content, topic, difficulty, question_count, context=""):
    """Generate questions using AI based on content"""
    prompt = f"""
    Based on the following educational content about {topic}, generate {question_count} {difficulty}-level questions.
    
    Content:
    {content[:3000]}  # Limit content to avoid token limits
    
    Additional Context: {context}
    
    Please generate questions in this exact JSON format:
    [
        {{
            "q": "Question text here?",
            "answer": "correct answer",
            "keywords": ["alternative1", "alternative2"],
            "feedback": "Educational explanation of the answer"
        }}
    ]
    
    Requirements:
    - Questions should be practical and test understanding
    - Answers should be concise and specific
    - Include 1-3 alternative acceptable answers in keywords
    - Feedback should explain why the answer is correct
    - Focus on {difficulty} level difficulty
    - Make questions relevant to {topic}
    
    Return only the JSON array, no other text.
    """
    
    response = call_openai_api(prompt, max_tokens=2000)
    try:
        # Try to parse the JSON response
        questions_data = json.loads(response)
        return questions_data
    except json.JSONDecodeError:
        # If not valid JSON, return error
        return {"error": f"AI returned invalid JSON: {response[:200]}..."}

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
    """
    
    response = call_openai_api(prompt, max_tokens=200)
    try:
        result = json.loads(response)
        # Apply confidence threshold
        if result.get('confidence', 0) < confidence_threshold:
            result['correct'] = False
            result['explanation'] += f" (Below {confidence_threshold}% confidence threshold)"
        return result
    except json.JSONDecodeError:
        return {
            "correct": False,
            "confidence": 0,
            "explanation": "Error: Could not parse AI response"
        }

# Helper function to save leaderboard data
def save_leaderboard(player_name, score, total_time, correct_answers, wrong_answers):
    print("Saving leaderboard data...")  # Debugging
    record = {
        "player": player_name,
        "score": score,
        "time": round(total_time, 2),
        "correct_answers": correct_answers,
        "wrong_answers": wrong_answers
    }
    try:
        with open(LEADERBOARD_FILE, "r", encoding="utf-8") as f:
            leaderboard = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        leaderboard = []

    leaderboard.append(record)

    with open(LEADERBOARD_FILE, "w", encoding="utf-8") as f:
        json.dump(leaderboard, f, indent=4)

# Define the function to get questions for a specific level
def get_questions_for_level(level_number, levels):
    level_info = next((lvl for lvl in levels if lvl["level"] == level_number), None)
    if level_info:
        return [q for q in questions if q.get("id") in level_info["questions"]]
    return []


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
        session['score'] = 0
        session['player_hp'] = 100  # Set player HP to 100
        session['enemy_level'] = selected_level
        # Set enemy HP to the base enemy HP constant
        session['enemy_hp'] = BASE_ENEMY_HP
        session['q_index'] = 0
        session['feedback'] = None
        session['correct_answers'] = 0
        session['wrong_answers'] = 0
        session["level_start_time"] = time.time()
        session["game_start_time"] = time.time()
        session['level_completed'] = False
        session['current_timer'] = 45  # Default timer is 45 seconds
        # Initialize enemy progression index to the Novice Gnome every time a new
        # game is started. This ensures each new game begins against the Novice Gnome
        # regardless of previous session state.
        try:
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
        except Exception:
            session['enemy_index'] = 0
        # After the player selects a level, send them to choose their character
        return redirect(url_for('choose_character'))

    # Pass unlocked info to template (GET request)
    return render_template('select_level.html', levels=levels, highest_unlocked=highest_unlocked)

# Route for the home page
@app.route('/')
def index():
    # Always redirect to level selection if no level is selected
    # If no selected level, show the merged landing page
    if 'selected_level' not in session:
        return render_template('index.html')
    # If a selected level exists, render the index page
    return render_template('index.html')
    return render_template('index.html')


# Home route (explicit)
@app.route('/home')
def home():
    return render_template('home.html')


# How-to-play route (ensure it exists)
@app.route('/howto')
def howto():
    return render_template('howto.html')


@app.route('/choose_character', methods=['GET', 'POST'])
def choose_character():
    total_characters = 16
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

    # Only allow up to 10 questions per level
    question_index = session['q_index'] % 10
    if session['q_index'] >= 10:
        # Level completed
        session['level_completed'] = True
        return redirect(url_for('result'))
    question = level_questions[question_index]

    # Always reload enemies from JSON for each game session
    try:
        with open('data/enemies.json', encoding='utf-8') as f:
            enemies = json.load(f)
    except Exception:
        enemies = []
    # Prefer ordered progression using session['enemy_index'] if present
    enemy = None
    enemy_index = session.get('enemy_index')
    if enemy_index is not None and isinstance(enemies, list) and 0 <= int(enemy_index) < len(enemies):
        try:
            enemy = enemies[int(enemy_index)]
        except Exception:
            enemy = None

    # Fallback: try to find an enemy that matches the current level
    if not enemy:
        enemy = next((e for e in enemies if e.get("level") == current_level), None)
    if not enemy:
        enemy = {"name": "Unknown Enemy", "avatar": "❓", "taunt": "No enemies found for this level."}
    print(f"DEBUG: Selected enemy for level {current_level}: {enemy}")  # Debugging

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
    elapsed = time.time() - session["level_start_time"]
    time_left = max(0, session.get("current_timer", 45) - int(elapsed))

    if time_left == 0:
        # Time expired → apply penalty & move on
        session['player_hp'] -= BASE_DAMAGE * current_level
        session['feedback'] = "⏳ Time's up! You took too long."
        session['q_index'] += 1
        session["level_start_time"] = time.time()  # Reset timer for the next question
        session["current_timer"] = max(10, session.get("current_timer", 45) - 5)  # Deduct 5s for next question, min 10s
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
            # Get the question feedback
            question_feedback = question.get('feedback', 'No additional information available.')
            
            if user_answer == correct_answer:
                session['score'] += score  # Add score
                session['enemy_hp'] -= (damage * 3)
                session['feedback'] = f"🔥 Exact answer! Triple damage: {damage*3} and {score} points in {time_taken:.2f} seconds.<br><br>✅ {question_feedback}"
                session["current_timer"] = min(60, session.get("current_timer", 45) + 5)  # Add 5s to timer for next question, max 60s
                session['correct_answers'] = session.get('correct_answers', 0) + 1  # Track correct answers
            elif user_answer in keywords:
                session['score'] += score  # Add score
                session['enemy_hp'] -= damage
                session['feedback'] = f"✅ Correct! You dealt {damage} damage and earned {score} points in {time_taken:.2f} seconds.<br><br>✅ {question_feedback}"
                session["current_timer"] = min(60, session.get("current_timer", 45) + 5)  # Add 5s to timer for next question, max 60s
                session['correct_answers'] = session.get('correct_answers', 0) + 1  # Track correct answers
            else:
                session['player_hp'] -= BASE_DAMAGE * current_level
                session['score'] -= 5  # Deduct points for wrong answer
                session['feedback'] = f"❌ Incorrect!<br><br>💡 {question_feedback}"
                session["current_timer"] = max(10, session.get("current_timer", 45) - 5)  # Deduct 5s from timer for next question, min 10s
                session['wrong_answers'] = session.get('wrong_answers', 0) + 1  # Track wrong answers

        # Reset timer for the next question
        session['level_start_time'] = time.time()

        # Move to the next question
        session['q_index'] += 1
        return redirect(url_for('feedback'))

    return render_template('game.html',
                           question=question,
                           score=session['score'],
                           player_hp=session['player_hp'],
                           enemy_hp=session['enemy_hp'],
                           q_number=question_index + 1,
                           total=10,  # Only 10 questions per level
                           level=current_level,
                           enemy=enemy,
                           enemy_image=enemy_image,
                           time_left=time_left)

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
    bonus = 20 if session.get('level_completed', False) and session['player_hp'] > 0 else 0
    final_score = session['score'] + bonus

    # Save the player's performance to the leaderboard
    total_time = time.time() - session.get("game_start_time", time.time())
    save_leaderboard(
        player_name=session.get("player_name", "Anonymous"),
        score=final_score,
        total_time=total_time,
        correct_answers=session.get('correct_answers', 0),
        wrong_answers=session.get('wrong_answers', 0)
    )

    # If the player died, show lose page
    if session.get('player_hp', 0) <= 0:
        return redirect(url_for('you_lose'))

    # If the level is completed, allow to select next level
    next_level = session.get('selected_level', 1) + 1
    try:
        with open("data/levels.json", "r", encoding="utf-8") as f:
            levels = json.load(f)
    except Exception:
        levels = []
    max_level = max([lvl['level'] for lvl in levels], default=1)
    can_advance = (
        session.get('level_completed', False)
        and session.get('correct_answers', 0) >= 7
        and next_level <= max_level
    )

    # Unlock the next level if completed
    if session.get('level_completed', False):
        prev_highest = session.get('highest_unlocked', 1)
        if next_level > prev_highest:
            session['highest_unlocked'] = next_level

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
            # Move to next enemy but don't exceed list bounds (wrap to last)
            next_idx = min(current_idx + 1, len(enemies_list) - 1)
            session['enemy_index'] = next_idx
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
    query_text = request.args.get('q', '').strip().lower()  # Get the search query
    results = []
    with ix.searcher() as searcher:
        query = QueryParser("keywords", ix.schema).parse(query_text)
        results = searcher.search(query)  # Perform the search
    return render_template('search.html', results=results)

# Route for the leaderboard page
@app.route('/leaderboard')
def leaderboard():
    try:
        with open(LEADERBOARD_FILE, "r", encoding="utf-8") as f:
            leaderboard = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        leaderboard = []

    # Sort by score (highest first), then by time (lowest first)
    leaderboard = sorted(leaderboard, key=lambda x: (-x["score"], x["time"]))

    return render_template("leaderboard.html", leaderboard=leaderboard)


@app.route('/you_win')
def you_win():
    # Simple win page when all levels are completed
    # Reset enemy state to original when the player finishes the game
    try:
        session['enemy_index'] = 0
        session['enemy_hp'] = BASE_ENEMY_HP
        session.pop('enemy_level', None)
    except Exception:
        pass
    return render_template('you_win.html')


@app.route('/you_lose')
def you_lose():
    # Simple lose page when player HP hits 0
    # Reset enemy state to original when the player loses
    try:
        session['enemy_index'] = 0
        session['enemy_hp'] = BASE_ENEMY_HP
        session.pop('enemy_level', None)
    except Exception:
        pass
    return render_template('you_lose.html')

# ------------------- TEST YOURSELF MODE -------------------
import random

@app.route('/test_yourself', methods=['GET', 'POST'])
def test_yourself():
    # Only reset test state for a true new start (GET with ?new=1)
    if request.method == 'GET' and request.args.get('new') == '1':
        session.pop('test_question_ids', None)
        session.pop('test_q_index', None)
        session.pop('test_correct', None)
        session.pop('test_start_time', None)
        session.pop('test_time_limit', None)
        session['test_user_answers'] = []
        print(f"[DEBUG] questions list length at test start: {len(questions)}")
        valid_questions = [q for q in questions if q.get('q') and str(q.get('q')).strip()]
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
        session['test_user_answers'].append({
            'question': question.get('q', ''),
            'user_answer': user_answer,
            'correct_answer': correct_answer,
            'correct': user_answer == correct_answer or user_answer in keywords,
            'feedback': question.get('feedback', 'No additional information available.')
        })
        if user_answer == correct_answer or user_answer in keywords:
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
    # Use the question IDs to determine total
    total = len(session.get('test_question_ids', []))
    correct = session.get('test_correct', 0)
    percent = int((correct / total) * 100) if total else 0
    passed = percent >= 75
    # Get user answers for review
    user_answers = session.get('test_user_answers', [])
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
    session['endless_current_question'] = random.choice(questions)
    session['endless_score_initialized'] = True
    
    return redirect(url_for('endless_game'))

@app.route('/endless/game', methods=['GET', 'POST'])
def endless_game():
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
        session['endless_question_start'] = time.time()
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
        correct = user_answer == correct_answer or user_answer in keywords
        
        # Store feedback for this question
        question_feedback = question.get('feedback', 'No additional information available.')
        if 'endless_feedback_list' not in session:
            session['endless_feedback_list'] = []
        
        feedback_entry = {
            'question': question.get('q', ''),
            'user_answer': user_answer,
            'correct_answer': correct_answer,
            'correct': correct,
            'feedback': question_feedback
        }
        session['endless_feedback_list'].append(feedback_entry)
        
        session['endless_total_answered'] = session.get('endless_total_answered', 0) + 1
        if correct:
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
        save_leaderboard(player_name, score, total_time, correct, wrong)
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
    return render_template('endless_result.html',
                          score=score,
                          highest_streak=highest_streak,
                          total_questions=total_answered,
                          correct=correct,
                          wrong=wrong,
                          total_time=round(total_time, 2),
                          player_name=player_name)


@app.route('/set_name', methods=['POST'])
def set_name():
    # Simple endpoint to set player's name in session
    name = request.form.get('player_name', '').strip()
    if not name:
        name = 'Anonymous'
    session['player_name'] = name
    # Return to the referring page (or index)
    return redirect(request.referrer or url_for('index'))

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
            
            # Get form data
            topic = request.form.get('topic')
            difficulty = request.form.get('difficulty')
            question_count = int(request.form.get('question_count', 10))
            context = request.form.get('context', '')
            
            # Generate questions with AI
            generated_questions = generate_questions_with_ai(content, topic, difficulty, question_count, context)
            
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
    try:
        questions_data = request.form.getlist('questions')
        selected_indices = request.form.getlist('selected_questions')
        
        # Load existing questions
        with open('data/questions.json', 'r', encoding='utf-8') as f:
            existing_questions = json.load(f)
        
        # Find the next available ID
        next_id = max([q.get('id', 0) for q in existing_questions]) + 1
        
        # Add selected questions
        for index_str in selected_indices:
            index = int(index_str)
            question_json = questions_data[index]
            question_data = json.loads(question_json)
            
            # Assign ID and mark as AI generated
            question_data['id'] = next_id
            question_data['ai_generated'] = True
            
            existing_questions.append(question_data)
            next_id += 1
        
        # Save updated questions
        with open('data/questions.json', 'w', encoding='utf-8') as f:
            json.dump(existing_questions, f, indent=2, ensure_ascii=False)
        
        # Recreate search index
        recreate_search_index()
        
        flash(f'Successfully added {len(selected_indices)} questions to the question bank!')
        return redirect(url_for('teacher_dashboard'))
        
    except Exception as e:
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
    api_key_configured = bool(OPENAI_API_KEY and OPENAI_API_KEY != 'your-openai-api-key-here')
    
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
    api_key_configured = bool(OPENAI_API_KEY and OPENAI_API_KEY != 'your-openai-api-key-here')
    
    return render_template('teacher_ai_grading.html', 
                         config=config, 
                         ai_grading_enabled=ai_grading_enabled,
                         api_key_configured=api_key_configured,
                         test_result=test_result)

# Placeholder routes for other teacher features
@app.route('/teacher/questions')
@teacher_required
def teacher_questions():
    return "<h1>Question Management - Under Development</h1><a href='/teacher/dashboard'>Back to Dashboard</a>"

@app.route('/teacher/analytics')
@teacher_required
def teacher_analytics():
    return "<h1>Student Analytics - Under Development</h1><a href='/teacher/dashboard'>Back to Dashboard</a>"

@app.route('/teacher/levels')
@teacher_required
def teacher_levels():
    return "<h1>Level Configuration - Under Development</h1><a href='/teacher/dashboard'>Back to Dashboard</a>"

@app.route('/teacher/settings')
@teacher_required
def teacher_settings():
    return "<h1>Game Settings - Under Development</h1><a href='/teacher/dashboard'>Back to Dashboard</a>"

# Helper functions for teacher portal
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

# Run the Flask app
if __name__ == "__main__":
    app.run(debug=True)
