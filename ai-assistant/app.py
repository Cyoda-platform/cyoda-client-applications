import uuid

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import threading
import queue

from common.util.utils import read_json_file
from entity.app_gen_entity.workflow.workflow import question_queue, cyoda_token
from entity.state_machine import cyoda_state_machine
from entity.workflow import process_event

app = Flask(__name__, static_folder='static')
CORS(app)  # Enable CORS for all routes

def read_questions_from_file():
    return read_json_file("/home/kseniia/IdeaProjects/cyoda-client-applications/ai-assistant/entity/app_gen_entity/app_gen_entity.json")

data = read_questions_from_file()

# For demonstration, let's pre-populate the queue with some questions
def start_session():
    state = cyoda_state_machine.current_transition
    process_event(cyoda_token, data, state['name'])

# Start background threads
start_session()

@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/get_question', methods=['GET'])
def get_question():
    try:
        question = question_queue.get_nowait()
        return jsonify({"question": question}), 200
    except queue.Empty:
        return jsonify({"question": None}), 204  # No Content

@app.route('/submit_answer', methods=['POST'])
def submit_answer():
    req_data = request.get_json()
    answer = req_data.get('answer')
    question = req_data.get('question')
    if not question or not answer:
        return jsonify({"message": "Invalid data"}), 400
    # Here, handle the answer (e.g., store it, process it, etc.)
    print(f"Received answer for question '{question}': {answer}")
    thread = threading.Thread(target=process_answer, args=(answer,))
    thread.daemon = True  # Optional: Makes the thread exit when the main program exits
    thread.start()
    return jsonify({"message": "Answer received"}), 200

def process_answer(user_answer: str):
    transitions = data["transitions"]
    transitions[-1]["user_answer"] = user_answer
    transition = cyoda_state_machine.next_transition(data["next_transition"])
    process_event(cyoda_token, data, transition['name'])


if __name__ == '__main__':
    app.run(debug=True)
