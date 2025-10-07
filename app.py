# This code ensures Flask and Whoosh are installed before importing them, preventing runtime errors
import subprocess
import sys
import os  # fixes line 40 error
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
    id=ID(stored=True, unique=True),  # Unique ID for each document
    question=TEXT(stored=True),       # The question text
    answer=TEXT(stored=True),         # The answer text
    keywords=TEXT(stored=True)        # Keywords for searching
)

# Create or open the Whoosh index directory
if not os.path.exists("indexdir"):
    os.mkdir("indexdir")  # Create the directory if it doesn't exist
    ix = index.create_in("indexdir", schema)  # Create a new index
else:
    ix = index.open_dir("indexdir")  # Open the existing index


# Initialize the Flask app
app = Flask(__name__)
app.secret_key = "unix_rpg_secret"  # Secret key for session management

# Helper function to save leaderboard data
def save_leaderboard(player_name, score, time_taken, question_text):
    record = {
        "player": player_name,
        "score": score,
        "time": round(time_taken, 2),
        "question": question_text
    }
    try:
        with open(LEADERBOARD_FILE, "r", encoding="utf-8") as f:
            leaderboard = json.load(f)
        print(f"Loaded leaderboard: {leaderboard}")  # Debugging
    except (FileNotFoundError, json.JSONDecodeError):
        print("Leaderboard file not found or invalid. Initializing a new leaderboard.")  # Debugging
        leaderboard = []

    leaderboard.append(record)
    print(f"Updated leaderboard: {leaderboard}")  # Debugging

    with open(LEADERBOARD_FILE, "w", encoding="utf-8") as f:
        json.dump(leaderboard, f, indent=4)
        print("Leaderboard saved successfully.")  # Debugging

# Route for the home page
@app.route('/')
def index():
    # Initialize session variables for the game
    session['score'] = 0
    session['player_hp'] = 50
    session['enemy_level'] = 1
    session['enemy_hp'] = BASE_ENEMY_HP * session['enemy_level']
    session['q_index'] = 0
    session['feedback'] = None
    return render_template('index.html')  # Render the home page

# Route for the game page
@app.route('/game', methods=['GET', 'POST'])
def game():
    # Check if the game is over
    if session['q_index'] >= len(questions) or session['player_hp'] <= 0:
        return redirect(url_for('result'))

    # Handle empty questions list
    if len(questions) == 0:
        return "No questions available. Please check the questions.json file."

    question = questions[session['q_index']]

    # Initialize timer when new question starts
    if "level_start_time" not in session:
        session["level_start_time"] = time.time()

    # Calculate remaining time
    elapsed = time.time() - session["level_start_time"]
    if elapsed > LEVEL_TIME_LIMIT:
        # Time expired → apply penalty & move on
        session['player_hp'] -= BASE_DAMAGE * session['enemy_level']
        session['feedback'] = f"⏳ Time's up! You took too long."
        session['q_index'] += 1
        session["level_start_time"] = time.time()  # reset timer
        return redirect(url_for('feedback'))

    if request.method == 'POST':
        user_answer = request.form.get('answer').strip().lower()
        correct_answer = question['answer'].strip().lower()
        keywords = question['keywords'].strip().lower()

        if user_answer == correct_answer or keywords:
            session['score'] += 10
            session['enemy_hp'] -= 10
            session['feedback'] = "✅ Correct!"
        else:
            session['player_hp'] -= BASE_DAMAGE * session['enemy_level']
            session['feedback'] = "❌ Incorrect!"

        # Enemy defeated? → reset HP + timer
        if session['enemy_hp'] <= 0 and session['q_index'] < len(questions) - 1:
            session['enemy_level'] += 1
            session['enemy_hp'] = BASE_ENEMY_HP * session['enemy_level']
            session["level_start_time"] = time.time()

        session['q_index'] += 1
        return redirect(url_for('feedback'))

    # Handle empty enemies list
    if len(enemies) == 0:
        enemy = {"name": "Unknown Enemy", "avatar": "❓", "taunt": "No enemies found!"}
    else:
        enemy_index = (session['enemy_level'] - 1) % len(enemies)
        enemy = enemies[enemy_index]

    # Calculate remaining time
    time_left = max(0, LEVEL_TIME_LIMIT - int(elapsed))

    return render_template('game.html',
                           question=question,
                           score=session['score'],
                           player_hp=session['player_hp'],
                           enemy_hp=session['enemy_hp'],
                           q_number=session['q_index'] + 1,
                           total=len(questions),
                           level=session['enemy_level'],
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
    bonus = 20 if session['q_index'] == len(questions) and session['player_hp'] > 0 else 0
    final_score = session['score'] + bonus

    # Determine the outcome of the game
    if session['player_hp'] <= 0:
        outcome = "💀 You were defeated!"
    elif session['q_index'] >= len(questions):
        outcome = "🏆 You defeated all enemies!"
    else:
        outcome = "✅ Quiz completed!"

    # Handle empty enemies list
    if len(enemies) == 0:
        enemy = {"name": "Unknown Enemy", "avatar": "❓", "taunt": "No enemies found!"}
    else:
        enemy_index = (session['enemy_level'] - 1) % len(enemies)
        enemy = enemies[enemy_index]

    # Render the result page
    return render_template('result.html', score=final_score,
                           player_hp=session['player_hp'],
                           enemy_hp=session['enemy_hp'],
                           outcome=outcome,
                           level=session['enemy_level'],
                           enemy=enemy)

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

    # Sort fastest answers first
    leaderboard = sorted(leaderboard, key=lambda x: x["time"])

    return render_template("leaderboard.html", leaderboard=leaderboard)

# Load enemies from the JSON file
try:
    with open('data/enemies.json', encoding='utf-8') as f:
        enemies = json.load(f)
    print(f"Enemies loaded successfully! Total enemies: {len(enemies)}")
except FileNotFoundError:
    print("Error: enemies.json file not found in the data folder.")
    enemies = []  # Fallback to an empty list if the file is missing
except json.JSONDecodeError as e:
    print(f"Error: Failed to decode enemies.json - {e}")
    enemies = []  # Fallback to an empty list if the file is invalid

# Load questions from the JSON file
try:
    with open('data/questions.json', encoding='utf-8') as f:
        questions = json.load(f)
    print("Questions loaded successfully!")
except FileNotFoundError:
    print("Error: questions.json file not found in the data folder.")
    questions = []  # Fallback to an empty list if the file is missing
except json.JSONDecodeError as e:
    print(f"Error: Failed to decode questions.json - {e}")
    questions = []  # Fallback to an empty list if the file is invalid

# Add questions from the JSON file to the Whoosh index
from whoosh.writing import AsyncWriter
writer = AsyncWriter(ix)
for question in questions:
    writer.add_document(
        id=str(question.get("id", "")),
        question=question.get("q", ""),
        answer=question.get("answer", ""),
        keywords=", ".join(question.get("keywords", []))
    )
writer.commit()  # Commit the changes to the index

# Run the Flask app
if __name__ == "__main__":
    app.run(debug=True)