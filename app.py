# ------------------- ENDLESS MODE -------------------
# (Moved below app initialization)
# This code ensures Flask and Whoosh are installed before importing them, preventing runtime errors
import subprocess
import sys
import os
import json
import time
from flask import Flask, render_template, request, redirect, url_for, session
from whoosh.fields import Schema, TEXT, ID
from whoosh import index

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
        session['enemy_hp'] = 100  # Set enemy HP to 100
        session['q_index'] = 0
        session['feedback'] = None
        session['correct_answers'] = 0
        session['wrong_answers'] = 0
        session["level_start_time"] = time.time()
        session["game_start_time"] = time.time()
        session['level_completed'] = False
        session['current_timer'] = 45  # Default timer is 45 seconds
        # Initialize enemy progression index (follow order in data/enemies.json)
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
    if session['q_index'] >= len(questions) or session['player_hp'] <= 0:
        return redirect(url_for('result'))


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
            if user_answer == correct_answer:
                session['score'] += score  # Add score
                session['enemy_hp'] -= (damage * 3)
                session['feedback'] = f"🔥 Exact answer! Triple damage: {damage*3} and {score} points in {time_taken:.2f} seconds."
                session["current_timer"] = min(60, session.get("current_timer", 45) + 5)  # Add 5s to timer for next question, max 60s
                session['correct_answers'] = session.get('correct_answers', 0) + 1  # Track correct answers
            elif user_answer in keywords:
                session['score'] += score  # Add score
                session['enemy_hp'] -= damage
                session['feedback'] = f"✅ Correct! You dealt {damage} damage and earned {score} points in {time_taken:.2f} seconds."
                session["current_timer"] = min(60, session.get("current_timer", 45) + 5)  # Add 5s to timer for next question, max 60s
                session['correct_answers'] = session.get('correct_answers', 0) + 1  # Track correct answers
            else:
                session['player_hp'] -= BASE_DAMAGE * current_level
                session['score'] -= 5  # Deduct points for wrong answer
                session['feedback'] = "❌ Incorrect!"
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
            'correct_answer': correct_answer
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
@app.route('/endless', methods=['GET', 'POST'])
def endless():
    # Initialize session state for new endless run
    if 'endless_score' not in session or request.method == 'GET':
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
    if session['endless_hp'] <= 0:
        return redirect(url_for('endless_result'))
    # Timer logic
    if 'endless_question_start' not in session or request.method == 'GET':
        session['endless_question_start'] = time.time()
    elapsed = time.time() - session['endless_question_start']
    time_left = max(0, 45 - int(elapsed))
    # Pick or keep the current question
    if 'endless_current_question' not in session or request.method == 'GET':
        session['endless_current_question'] = random.choice(questions)
    question = session['endless_current_question']
    streak = session['endless_streak']
    score = session['endless_score']
    player_hp = session['endless_hp']
    highest_streak = session['endless_highest_streak']
    total_answered = session['endless_total_answered']
    if time_left == 0:
        session['endless_hp'] -= 10
        session['endless_streak'] = 0
        session['endless_wrong'] += 1
        session['endless_total_answered'] += 1
        session['endless_question_start'] = time.time()
        session['endless_current_question'] = random.choice(questions)
        return redirect(url_for('endless'))
    if request.method == 'POST':
        user_answer = request.form.get('answer', '').strip().lower()
        correct_answer = question.get('answer', '').strip().lower()
        raw_keywords = question.get('keywords', [])
        if isinstance(raw_keywords, str):
            keywords = [k.strip().lower() for k in raw_keywords.split(',') if k.strip()]
        else:
            keywords = [str(k).strip().lower() for k in raw_keywords]
        correct = user_answer == correct_answer or user_answer in keywords
        session['endless_total_answered'] += 1
        if correct:
            session['endless_score'] += 10
            session['endless_streak'] += 1
            session['endless_correct'] += 1
            if session['endless_streak'] > session['endless_highest_streak']:
                session['endless_highest_streak'] = session['endless_streak']
            # HP regen after 5 correct in a row
            if session['endless_streak'] % 5 == 0:
                session['endless_hp'] = min(100, session['endless_hp'] + 20)
        else:
            session['endless_hp'] -= 10
            session['endless_streak'] = 0
            session['endless_wrong'] += 1
        session['endless_question_start'] = time.time()
        session['endless_current_question'] = random.choice(questions)
        return redirect(url_for('endless'))
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
        session.pop('player_name', None)
        return redirect(url_for('leaderboard'))
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

# Run the Flask app
if __name__ == "__main__":
    app.run(debug=True)
