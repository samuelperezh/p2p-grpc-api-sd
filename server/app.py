import os
from flask import Flask, request, jsonify
import sqlite3
import bcrypt
import secrets
import string
from functools import wraps

app = Flask(__name__)

def init_db():
    conn = sqlite3.connect('DHT.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS peers 
                      (username TEXT PRIMARY KEY, password TEXT, url TEXT, status TEXT, token TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS files 
                      (username TEXT, filename TEXT, FOREIGN KEY(username) REFERENCES peers(username))''')
    conn.commit()
    conn.close()

def get_db_connection():
    conn = sqlite3.connect('DHT.db')
    return conn

def validate_login(username, password):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT password FROM peers WHERE username = ?', (username,))
    result = cursor.fetchone()
    conn.close()
    
    if result:
        hashed_password = result[0]
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
    return False

def generate_token():
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(20))

def extract_token(auth_header):
    if auth_header and auth_header.startswith('Bearer '):
        return auth_header.split(" ")[1]
    return None

def check_token(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        token = extract_token(auth_header)
        
        if not token:
            return jsonify({'status': 'error', 'message': 'Token missing or malformed'}), 401
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT username FROM peers WHERE token = ?', (token,))
        user = cursor.fetchone()
        conn.close()
        
        if not user:
            return jsonify({'status': 'error', 'message': 'Invalid token'}), 401
        
        return func(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    url = data.get('url')

    if not username or not password or not url:
        return jsonify({'status': 'error', 'message': 'Missing fields'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT password FROM peers WHERE username = ?', (username,))
    result = cursor.fetchone()

    if result:
        if not bcrypt.checkpw(password.encode('utf-8'), result[0].encode('utf-8')):
            conn.close()
            return jsonify({'status': 'error', 'message': 'Incorrect password'}), 401
    else:
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        cursor.execute('INSERT INTO peers (username, password, url, status) VALUES (?, ?, ?, ?)',
                       (username, hashed_password.decode('utf-8'), url, 'online'))

    new_token = generate_token()
    cursor.execute('UPDATE peers SET token = ?, status = ?, url = ? WHERE username = ?',
                   (new_token, 'online', url, username))
    conn.commit()

    print(f"Peer {username} is online with IP {url}")
    
    conn.close()
    
    return jsonify({'status': 'ok', 'token': new_token})

@app.route('/indice', methods=['POST'])
@check_token
def indice():
    data = request.json
    username = data.get('username')
    files = data.get('archivos')

    if not username or not files:
        return jsonify({'status': 'error', 'message': 'Missing fields'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM files WHERE username = ?', (username,))

    for file in files:
        cursor.execute('INSERT INTO files (username, filename) VALUES (?, ?)', (username, file))

    conn.commit()
    conn.close()

    return jsonify({'status': 'ok'})

@app.route('/buscar', methods=['POST'])
def buscar():
    data = request.json
    file_name = data.get('archivo')

    if not file_name:
        return jsonify({'status': 'error', 'message': 'Missing file name'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''SELECT peers.url, peers.username 
                      FROM files JOIN peers 
                      ON files.username = peers.username 
                      WHERE files.filename = ? AND peers.status = 'online' ''', 
                   (file_name,))

    results = cursor.fetchall()
    conn.close()

    response = []
    for result in results:
        url, username = result
        response.append({'url': f"{url}/download/{file_name}", 'username': username})

    return jsonify({'results': response})

@app.route('/logout', methods=['POST'])
@check_token
def logout():
    data = request.json
    username = data.get('username')

    if not username:
        return jsonify({'status': 'error', 'message': 'Missing username'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE peers SET status = ? WHERE username = ?', ('offline', username))
    conn.commit()
    conn.close()

    print(f"Peer {username} is offline")

    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    init_db()
    app.run(host="0.0.0.0", port=int(os.getenv('PORT', 5000)), debug=True)
