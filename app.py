from flask import Flask, request, jsonify
import sqlite3
import random

app = Flask(__name__)

# Initialize the SQLite database
def init_db():
    conn = sqlite3.connect('DHT.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS peers 
                      (username TEXT PRIMARY KEY, password TEXT, url TEXT, status TEXT, token TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS files 
                      (username TEXT, filename TEXT, FOREIGN KEY(username) REFERENCES peers(username))''')
    conn.commit()
    conn.close()

# Function to get a database connection
def get_db_connection():
    conn = sqlite3.connect('DHT.db')
    return conn

# POST /login endpoint
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    url = data.get('url')
    
    # Generate a random token
    token = str(random.randint(100000, 999999))
    
    # Insert peer into DHT or update if already present
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT OR REPLACE INTO peers (username, password, url, status, token) VALUES (?, ?, ?, ?, ?)',
                   (username, password, url, 'online', token))
    conn.commit()
    conn.close()
    
    # Log the peer's IP on the server console
    print(f"Peer {username} is online with IP {url}")
    
    return jsonify({'status': 'ok', 'token': token})

# POST /indice endpoint
@app.route('/indice', methods=['POST'])
def indice():
    data = request.json
    username = data.get('username')
    files = data.get('archivos')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM files WHERE username = ?', (username,))
    
    for file in files:
        cursor.execute('INSERT INTO files (username, filename) VALUES (?, ?)', (username, file))
    
    conn.commit()
    conn.close()
    
    return jsonify({'status': 'ok'})

# POST /buscar endpoint
@app.route('/buscar', methods=['POST'])
def buscar():
    data = request.json
    file_name = data.get('archivo')
    
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

# POST /logout endpoint
@app.route('/logout', methods=['POST'])
def logout():
    data = request.json
    username = data.get('username')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE peers SET status = ? WHERE username = ?', ('offline', username))
    conn.commit()
    conn.close()
    
    print(f"Peer {username} is offline")
    
    return jsonify({'status': 'ok'})

# Initialize the database when the app starts
if __name__ == '__main__':
    init_db()
    app.run(port=4040, debug=True)
