from flask import Flask, request, jsonify
import random

app = Flask(__name__)
WORDS = ["арбуз", "земля", "ананас", "слива", "апельсин", "груша", "яблоко", "абрикос", "вишня", "черешня"]
last_word = ""

@app.route('/start', methods=['GET'])
def start_game():
    global last_word
    last_word = random.choice(WORDS)
    return jsonify({"word": last_word})

@app.route('/move', methods=['POST'])
def make_move():
    global last_word
    data = request.json
    user_word = data.get('word', '')
     
    if not user_word or user_word[0].lower() != last_word[-1].lower():
        return jsonify({"status": "error", "message": "Invalid word"}), 400
         
    last_word = user_word
     
    valid_words = [w for w in WORDS if w[0].lower() == last_word[-1].lower()]
    if not valid_words:
        return jsonify({"status": "win", "word": None})
         
    server_word = random.choice(valid_words)
    last_word = server_word
    return jsonify({"status": "ok", "word": server_word})

if __name__ == '__main__':
    app.run(port=5000)