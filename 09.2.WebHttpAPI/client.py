import requests

WORDS = ["арбуз", "земля", "ананас", "слива", "апельсин", "груша", "яблоко", "абрикос", "вишня", "черешня"]
BASE_URL = "http://localhost:5000"

def play_game():
    response = requests.get(f"{BASE_URL}/start")
    current_word = response.json()['word']
    print(f"Server starts with: {current_word}")
     
    while True:
        valid_words = [w for w in WORDS if w[0].lower() == current_word[-1].lower()]
        if not valid_words:
            print("No valid words, I lose!")
            break
             
        my_word = valid_words[0]
        print(f"My move: {my_word}")
         
        response = requests.post(f"{BASE_URL}/move", json={"word": my_word})
        result = response.json()
         
        if result['status'] == 'win':
            print("Server has no words, I win!")
            break
        elif result['status'] == 'error':
            print("Server rejected my word!")
            break
             
        current_word = result['word']
        print(f"Server moves: {current_word}")

if __name__ == '__main__':
    play_game()