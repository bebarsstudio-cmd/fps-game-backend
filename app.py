   import os
   import random
   import string
   from flask import Flask, request, jsonify
   from flask_cors import CORS
   import sqlite3

   app = Flask(__name__)
   CORS(app)

   DB_FILE = "game.db"

   def get_db():
       conn = sqlite3.connect(DB_FILE)
       conn.row_factory = sqlite3.Row
       return conn

   def init_db():
       with get_db() as conn:
           conn.execute('''CREATE TABLE IF NOT EXISTS users 
                           (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                            game_id TEXT UNIQUE, username TEXT UNIQUE, password TEXT)''')
           conn.execute('''CREATE TABLE IF NOT EXISTS servers 
                           (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                            game_id TEXT, host_ip TEXT, is_public INTEGER, 
                            last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
           conn.commit()

   init_db()

   @app.route('/api/signup', methods=['POST'])
   def signup():
       data = request.json
       username = data.get('username')
       password = data.get('password')
       if not username or not password:
           return jsonify({"success": False, "message": "Username and password required"}), 400
       
       game_id = ''.join(random.choices(string.digits, k=4))
       try:
           with get_db() as conn:
               conn.execute("INSERT INTO users (game_id, username, password) VALUES (?, ?, ?)", 
                            (game_id, username, password))
               conn.commit()
           return jsonify({"success": True, "game_id": game_id, "username": username})
       except Exception as e:
           return jsonify({"success": False, "message": "Username might be taken"}), 400

   @app.route('/api/login', methods=['POST'])
   def login():
       data = request.json
       username = data.get('username')
       password = data.get('password')
       with get_db() as conn:
           user = conn.execute("SELECT game_id, username FROM users WHERE username=? AND password=?", 
                               (username, password)).fetchone()
       if user:
           return jsonify({"success": True, "game_id": user['game_id'], "username": user['username']})
       return jsonify({"success": False, "message": "Invalid credentials"}), 401

   @app.route('/api/get_servers', methods=['GET'])
   def get_servers():
       with get_db() as conn:
           rows = conn.execute('''SELECT s.game_id, u.username, s.host_ip FROM servers s 
                                  JOIN users u ON s.game_id=u.game_id WHERE s.is_public=1''').fetchall()
       servers = [{"game_id": r['game_id'], "username": r['username'], "host_ip": r['host_ip']} for r in rows]
       return jsonify({"success": True, "servers": servers})

   @app.route('/api/register_server', methods=['POST'])
   def register_server():
       data = request.json
       with get_db() as conn:
           conn.execute("INSERT INTO servers (game_id, host_ip, is_public) VALUES (?,?,?)",
                        (data['game_id'], data.get('host_ip','127.0.0.1'), data.get('is_public',1)))
           conn.commit()
       return jsonify({"success": True})

   if __name__ == '__main__':
       port = int(os.environ.get('PORT', 10000))
       app.run(host='0.0.0.0', port=port)
