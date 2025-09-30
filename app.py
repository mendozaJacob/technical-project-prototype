# this code makes sure Flask and Whoosh are installed
# before trying to import them, preventing runtime errors
import subprocess
import sys

# Helper function to auto-install missing packages
def install_and_import(package):
    try:
        __import__(package)
    except ImportError:
        print(f"📦 Installing {package} ...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        globals()[package] = __import__(package)

# Ensure Flask and Whoosh are available
install_and_import("flask")
install_and_import("whoosh")

# Now safe to import normally
from flask import Flask, render_template, request, redirect, url_for, session
from whoosh.fields import Schema, TEXT, ID
from whoosh import index
import os, json


# Define the schema for the Whoosh index
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
    ix = index.open_dir("indexdir")

# Add data to the index
from whoosh.writing import AsyncWriter
writer = AsyncWriter(ix)
writer.add_document(id="1", question="What does 'pwd' do?", answer="Prints working directory", keywords="pwd, command")
writer.add_document(id="2", question="Which command lists files?", answer="ls", keywords="ls, list files")
writer.add_document(id="3", question="What command changes directories?", answer="cd", keywords="cd, change directory")
writer.add_document(id="4", question="Which command creates a file?", answer="touch", keywords="touch, create file")
writer.add_document(id="5", question="Which command deletes a file?", answer="rm", keywords="rm, delete file")
writer.commit()

app = Flask(__name__)  # Fix: Initialize Flask app with __name__
app.secret_key = "unix_rpg_secret"


BASE_ENEMY_HP = 50
BASE_DAMAGE = 10

@app.route('/')
def index():
    session['score'] = 0
    session['player_hp'] = 50
    session['enemy_level'] = 1
    session['enemy_hp'] = BASE_ENEMY_HP * session['enemy_level']
    session['q_index'] = 0
    session['feedback'] = None
    return render_template('index.html')

@app.route('/game', methods=['GET', 'POST'])
def game():
    if session['q_index'] >= len(questions) or session['player_hp'] <= 0:
        return redirect(url_for('result'))

    question = questions[session['q_index']]

    if request.method == 'POST':
        user_answer = request.form.get('answer').strip().lower()
        correct_answer = question['answer'].strip().lower()

        if user_answer == correct_answer:
            session['score'] += 10
            session['enemy_hp'] -= 10
            session['feedback'] = "✅ Correct!"
        else:
            session['player_hp'] -= BASE_DAMAGE * session['enemy_level']
            session['feedback'] = "❌ Incorrect!"

        if session['enemy_hp'] <= 0 and session['q_index'] < len(questions) - 1:
            session['enemy_level'] += 1
            session['enemy_hp'] = BASE_ENEMY_HP * session['enemy_level']

        session['q_index'] += 1
        return redirect(url_for('feedback'))

    # Fallback if enemies list is empty
    if len(enemies) == 0:
        enemy = {"name": "Unknown Enemy", "avatar": "❓", "taunt": "No enemies found!"}
    else:
        enemy_index = (session['enemy_level'] - 1) % len(enemies)
        enemy = enemies[enemy_index]

    return render_template('game.html', question=question,
                           score=session['score'],
                           player_hp=session['player_hp'],
                           enemy_hp=session['enemy_hp'],
                           q_number=session['q_index'] + 1,
                           total=len(questions),
                           level=session['enemy_level'],
                           enemy=enemy)

@app.route('/feedback')
def feedback():
    if not session.get('feedback'):
        return redirect(url_for('game'))
    feedback = session['feedback']
    session['feedback'] = None  # Clear feedback after rendering
    return render_template('feedback.html',
                           feedback=feedback,
                           player_hp=session['player_hp'],
                           enemy_hp=session['enemy_hp'],
                           score=session['score'],
                           level=session['enemy_level'])

@app.route('/result')
def result():
    bonus = 20 if session['q_index'] == len(questions) and session['player_hp'] > 0 else 0
    final_score = session['score'] + bonus

    if session['player_hp'] <= 0:
        outcome = "💀 You were defeated!"
    elif session['q_index'] >= len(questions):
        outcome = "🏆 You defeated all enemies!"
    else:
        outcome = "✅ Quiz completed!"

    enemy_index = (session['enemy_level'] - 1) % len(enemies)
    enemy = enemies[enemy_index]

    return render_template('result.html', score=final_score,
                           player_hp=session['player_hp'],
                           enemy_hp=session['enemy_hp'],
                           outcome=outcome,
                           level=session['enemy_level'],
                           enemy=enemy)

# Query route
from whoosh.qparser import QueryParser

@app.route('/search', methods=['GET'])
def search():
    query_text = request.args.get('q', '').strip().lower()  # Get query from URL parameter
    results = []
    with ix.searcher() as searcher:
        query = QueryParser("keywords", ix.schema).parse(query_text)
        results = searcher.search(query)
    return render_template('search.html', results=results)

# Load and test the JSON file
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
    with open('data/questions.json', encoding='utf-8') as f:  # Specify UTF-8 encoding
        questions = json.load(f)
    print("Questions loaded successfully!")
except FileNotFoundError:
    print("Error: questions.json file not found in the data folder.")
    questions = []  # Fallback to an empty list if the file is missing
except json.JSONDecodeError as e:
    print(f"Error: Failed to decode questions.json - {e}")
    questions = []  # Fallback to an empty list if the file is invalid

if __name__ == "__main__":
    app.run(debug=True)
