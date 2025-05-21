from flask import Flask, render_template, request, jsonify
from flask_mysqldb import MySQL  
import requests

app = Flask(__name__)

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '2505'
app.config['MYSQL_DB'] = 'snake_game1'  

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

    # Отримати role_id для 'user' (можна кешувати це, якщо хочеш)
    cursor.execute("SELECT id FROM roles WHERE role_name = 'user'")
    role_result = cursor.fetchone()
    if not role_result:
        return jsonify({"error": "Role 'user' not found"}), 500
    role_id = role_result[0]

    # Перевірити, чи користувач вже існує
    cursor.execute("SELECT id FROM users WHERE nickname = %s", (nickname,))
    user = cursor.fetchone()
    if user:
        user_id = user[0]
    else:
        cursor.execute(
            "INSERT INTO users (role_id, nickname) VALUES (%s, %s)",
            (role_id, nickname)
        )
        mysql.connection.commit()
        user_id = cursor.lastrowid

    # Додати результат гри
    cursor.execute(
        "INSERT INTO scores (user_id, score, difficulty) VALUES (%s, %s, %s)",
        (user_id, score, difficulty)
    )
    mysql.connection.commit()
    cursor.close()
    return jsonify({"message": "Score saved!"})


@app.route('/top_scores')
def top_scores():
    cursor = mysql.connection.cursor()
    cursor.execute("""
        SELECT u.nickname, s.score, s.difficulty
        FROM scores s
        JOIN users u ON s.user_id = u.id
        ORDER BY s.score DESC
        LIMIT 10
    """)
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

@app.route('/delete_scores', methods=['POST'])
def delete_scores():
    data = request.json
    password = data.get('password')
    nickname = data.get('nickname')

    if password != "2505":
        return jsonify({"message": "Wrong password!"}), 403

    cursor = mysql.connection.cursor()

    # Видалити всі результати
    cursor.execute("DELETE FROM scores")

    # Призначити роль 'admin' користувачу з переданим nickname
    cursor.execute("SELECT id FROM users WHERE nickname = %s", (nickname,))
    user = cursor.fetchone()

    if user:
        user_id = user[0]
        cursor.execute("SELECT id FROM roles WHERE role_name = 'admin'")
        role = cursor.fetchone()
        if role:
            admin_role_id = role[0]
            cursor.execute("UPDATE users SET role_id = %s WHERE id = %s", (admin_role_id, user_id))
            mysql.connection.commit()
            message = "Scores deleted. You are now admin."
        else:
            message = "Role 'admin' not found in DB."
    else:
        message = "User not found."

    cursor.close()
    return jsonify({"message": message})



if __name__ == '__main__':
    app.run(debug=True)
