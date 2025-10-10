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
if not os.path.exists("indexdir"):
    os.mkdir("indexdir")
    ix = index.create_in("indexdir", schema)
else:
    try:
        ix = index.open_dir("indexdir")
    except Exception as e:
        print(f"Error opening Whoosh index: {e}")
        os.mkdir("indexdir")
        ix = index.create_in("indexdir", schema)

# Initialize the Flask app
app = Flask(__name__)
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
        return redirect(url_for('game'))

    # Pass unlocked info to template
    return render_template('select_level.html', levels=levels, highest_unlocked=highest_unlocked)

# Route for the home page
@app.route('/')
def index():
    # Always redirect to level selection if no level is selected
    if 'selected_level' not in session:
        return redirect(url_for('select_level'))
    return render_template('index.html')

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
    enemy = next((e for e in enemies if e.get("level") == current_level), None)
    if not enemy:
        enemy = {"name": "Unknown Enemy", "avatar": "❓", "taunt": "No enemies found for this level."}
    print(f"DEBUG: Selected enemy for level {current_level}: {enemy}")  # Debugging

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

        # Check if the answer is correct
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
    can_advance = session.get('level_completed', False) and next_level <= max_level

    # Unlock the next level if completed
    if session.get('level_completed', False):
        prev_highest = session.get('highest_unlocked', 1)
        if next_level > prev_highest:
            session['highest_unlocked'] = next_level

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
    with open('data/questions.json', encoding='utf-8') as f:
        questions = json.load(f)
    print("Questions loaded successfully!")
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
writer.commit()

# Run the Flask app
if __name__ == "__main__":
    app.run(debug=True)
