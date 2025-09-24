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

questions = [
    {"q": "What does the command 'pwd' do?",
     "options": ["A) Prints working directory",
                 "B) Prints word document",
                 "C) Password reset",
                 "D) Print write data"],
     "answer": "A",
     "dialogue_correct": "✅ Correct! 'pwd' shows your current location in the filesystem. It's like asking: 'Where am I right now?'",
     "dialogue_wrong": "❌ Not quite. 'pwd' stands for 'print working directory' — it tells you your current folder path."},

    {"q": "Which command lists the files in your current directory?",
     "options": ["A) ls", "B) cd", "C) cat", "D) echo"],
     "answer": "A",
     "dialogue_correct": "✅ Nice! 'ls' lists all files and directories in your current folder — like opening a treasure chest of files!",
     "dialogue_wrong": "❌ Wrong. The 'ls' command shows all files and directories where you are. Think of it as 'Look Show'."},

    {"q": "What command is used to change directories?",
     "options": ["A) mv", "B) cd", "C) rm", "D) dir"],
     "answer": "B",
     "dialogue_correct": "✅ Correct! 'cd' means 'change directory' — it’s how you walk into a new folder.",
     "dialogue_wrong": "❌ Nope. The right answer is 'cd'. It moves you from one folder to another, like stepping through a door."},

    {"q": "Which command creates a new empty file?",
     "options": ["A) touch", "B) mkdir", "C) rm", "D) nano"],
     "answer": "A",
     "dialogue_correct": "✅ Correct! 'touch filename' creates an empty file. It's like magically summoning a blank scroll.",
     "dialogue_wrong": "❌ Wrong. The right answer is 'touch'. It’s used to create an empty file instantly."},

    {"q": "Which command deletes a file?",
     "options": ["A) cat", "B) rm", "C) delete", "D) erase"],
     "answer": "B",
     "dialogue_correct": "✅ Well done! 'rm' removes files permanently — be careful, there’s no recycle bin!",
     "dialogue_wrong": "❌ Wrong. 'rm' is the delete command. Always double-check before using it!"}
]

enemies = [
    {"name": "Gremlin of pwd", "avatar": "👹", "taunt": "The Gremlin snarls: 'You'll never escape directories!'"},
    {"name": "Orc of cd", "avatar": "🧟", "taunt": "The Orc grunts: 'You cannot move between my folders!'"},
    {"name": "Troll of ls", "avatar": "👺", "taunt": "The Troll laughs: 'You can't even see my files!'"},
    {"name": "Dragon of rm", "avatar": "🐉", "taunt": "The Dragon roars: 'I will delete you like a file!'"},
]

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
            session['feedback'] = question['dialogue_correct']
        else:
            session['player_hp'] -= BASE_DAMAGE * session['enemy_level']
            session['feedback'] = question['dialogue_wrong']

        if session['enemy_hp'] <= 0 and session['q_index'] < len(questions) - 1:
            session['enemy_level'] += 1
            session['enemy_hp'] = BASE_ENEMY_HP * session['enemy_level']

        session['q_index'] += 1
        return redirect(url_for('feedback'))

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

if __name__ == "__main__":
    app.run(debug=True)
