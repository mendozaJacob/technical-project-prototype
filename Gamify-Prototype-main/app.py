from flask import Flask, request, session, redirect, url_for, render_template

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
        selected = request.form.get('option')
        correct = question['answer']

        if selected == correct:
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

if __name__ == "__main__":
    app.run(debug=True)
