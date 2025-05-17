from flask import Flask, render_template, request, jsonify
from flask_mysqldb import MySQL  
import requests

app = Flask(__name__)

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '2505'
app.config['MYSQL_DB'] = 'snake_game'  

mysql = MySQL(app)

SECRET_KEY = '6LdlVjcrAAAAAFqTrtJvuG3fg6KyjvDw6hR2kJ5V'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit_score', methods=['POST'])
def submit_score():
    data = request.json
    nickname = data.get('nickname')
    score = data.get('score')
    difficulty = data.get('difficulty')

    cursor = mysql.connection.cursor()
    cursor.execute("INSERT INTO scores (nickname, score, difficulty) VALUES (%s, %s, %s)",
                   (nickname, score, difficulty))
    mysql.connection.commit()
    cursor.close()
    return jsonify({"message": "Score saved!"})

@app.route('/top_scores')
def top_scores():
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT nickname, score, difficulty FROM scores ORDER BY score DESC LIMIT 10")
    results = cursor.fetchall()
    cursor.close()

    top_list = [{"nickname": row[0], "score": row[1], "difficulty": row[2]} for row in results]
    return jsonify(top_list)

@app.route('/validate_captcha', methods=['POST'])
def validate_captcha():
    data = request.get_json()
    recaptcha_response = data.get('response')

    verify_url = 'https://www.google.com/recaptcha/api/siteverify'
    payload = {
        'secret': SECRET_KEY,
        'response': recaptcha_response
    }

    r = requests.post(verify_url, data=payload)
    result = r.json()

    return jsonify({'success': result.get('success', False)})

@app.route('/get_high_score')
def get_high_score():
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT MAX(score) FROM scores")
    result = cursor.fetchone()
    cursor.close()
    return jsonify({"high_score": result[0] if result[0] else 0})


if __name__ == '__main__':
    app.run(debug=True)
