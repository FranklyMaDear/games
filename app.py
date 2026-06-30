import os
import json
from flask import Flask, send_from_directory, request, jsonify
from flask_cors import CORS
import asgiref.wsgi

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)

# Σέρβιρε την κεντρική σελίδα
@app.route('/')
def serve_index():
    return send_from_directory('.', 'index.html')

# Σέρβιρε τα static αρχεία
@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('.', path)

# ==========================================
# DATABASE (Προσομοίωση - μπορείς να το συνδέσεις με SQLite αργότερα)
# ==========================================
user_data = {}

def get_user_data(user_id):
    if user_id not in user_data:
        user_data[user_id] = {'points': 0, 'wins_c4': 0, 'c4_claimed': False}
    return user_data[user_id]

@app.route('/board', methods=['GET'])
def get_board():
    user_id = request.args.get('userId')
    data = get_user_data(user_id)
    return jsonify({'points': data['points'], 'level': 1, 'free_spins': 0})

@app.route('/add-points', methods=['POST'])
def add_points():
    data = request.json
    user_id = data.get('userId')
    points = data.get('points', 0)
    user = get_user_data(user_id)
    user['points'] += points
    return jsonify({'added': points, 'total': user['points']})

# ΝΕΟ ENDPOINT: Το παιχνίδι Connect 4 στέλνει νίκη εδώ
@app.route('/record-win', methods=['POST'])
def record_win():
    data = request.json
    user_id = data.get('userId')
    game = data.get('game', 'connect4')
    if user_id:
        user = get_user_data(user_id)
        if game == 'connect4':
            user['wins_c4'] += 1
            return jsonify({'wins': user['wins_c4']})
    return jsonify({'error': 'Invalid data'}), 400

# Διαβάζει την πρόοδο για το Daily Reward
@app.route('/missions', methods=['GET'])
def get_missions():
    user_id = request.args.get('userId')
    user = get_user_data(user_id)
    return jsonify({'connect4': {'wins': user['wins_c4'], 'claimed': user['c4_claimed']}})

# Εξαργύρωση του Daily Reward
@app.route('/missions/claim', methods=['POST'])
def claim_mission():
    data = request.json
    user_id = data.get('userId')
    if user_id:
        user = get_user_data(user_id)
        if user['wins_c4'] >= 3 and not user['c4_claimed']:
            user['c4_claimed'] = True
            user['points'] += 150
            return jsonify({'status': 'claimed', 'points_added': 150})
    return jsonify({'status': 'failed'}), 400

# ==========================================
# ΣΗΜΑΝΤΙΚΟ: Διόρθωση για το Uvicorn του Hugging Face!
# ==========================================
app = asgiref.wsgi.WsgiToAsgi(app)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 7860)))
