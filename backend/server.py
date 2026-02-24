# Jednoduchý backend pro správu kryptoměn uživatele
from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3

app = Flask(__name__)
CORS(app)

DB_PATH = 'backend/crypto.db'

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS holdings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        crypto TEXT,
        amount REAL,
        price REAL,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )''')
    conn.commit()
    conn.close()

@app.route('/api/user', methods=['POST'])
def create_user():
    data = request.json
    username = data.get('username')
    if not username:
        return jsonify({'error': 'Username required'}), 400
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute('INSERT INTO users (username) VALUES (?)', (username,))
        conn.commit()
        user_id = c.lastrowid
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({'error': 'User exists'}), 409
    conn.close()
    return jsonify({'id': user_id, 'username': username})

@app.route('/api/holdings/<username>', methods=['GET'])
def get_holdings(username):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT id FROM users WHERE username=?', (username,))
    user = c.fetchone()
    if not user:
        conn.close()
        return jsonify({'error': 'User not found'}), 404
    user_id = user[0]
    c.execute('SELECT crypto, amount, price FROM holdings WHERE user_id=?', (user_id,))
    holdings = [{'crypto': row[0], 'amount': row[1], 'price': row[2]} for row in c.fetchall()]
    conn.close()
    return jsonify({'username': username, 'holdings': holdings})

@app.route('/api/holdings/<username>', methods=['POST'])
def add_holding(username):
    data = request.json
    crypto = data.get('crypto')
    amount = data.get('amount')
    price = data.get('price')
    if not all([crypto, amount, price]):
        return jsonify({'error': 'Missing data'}), 400
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT id FROM users WHERE username=?', (username,))
    user = c.fetchone()
    if not user:
        conn.close()
        return jsonify({'error': 'User not found'}), 404
    user_id = user[0]
    c.execute('INSERT INTO holdings (user_id, crypto, amount, price) VALUES (?, ?, ?, ?)', (user_id, crypto, amount, price))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Holding added'})

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)
