from flask import Flask, request, jsonify, abort
from dotenv import load_dotenv
from google import genai
from google.genai import types
import os
from werkzeug.exceptions import HTTPException
from flask_cors import CORS

# loading the environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

users_chat_history = {}
chat_id = ""
prompt = ""

def update_chat_history(role, text):
    content = {
        "role": role,
        "parts": [{"text": text,}],
    }
    users_chat_history[chat_id].append(content)

def get_chat_history():
    if chat_id not in users_chat_history:
        users_chat_history[chat_id] = []

    return users_chat_history[chat_id]

def fetch_response():
    try:
        chat_history = get_chat_history()
        chat_session = client.chats.create(
            model=os.getenv("MODEL"),
            config=types.GenerateContentConfig(
                system_instruction="Your persona is that of an enthusiastic and jovial anime geek. All responses must be directly related to anime or manga, so please avoid topics outside of this domain. When answering, be brief and to the point, just like you're chatting with a friend who gets it. Feel free to add some quirky, friendly flair when appropriate. If you are ever uncertain about a user's request or require more information, you must ask a clarifying question to ensure a more accurate response.",
                # max_output_tokens=250,
                # thinking_config=
            ),
            history=chat_history,
        )
        response = chat_session.send_message(prompt)
        update_chat_history("user", prompt)
        update_chat_history("model", response.text)
        return response.text
    except Exception as error:
        print("error", error)
        raise

@app.route('/chat', methods=['POST'])
def chat():
    if not request.json or ('prompt' not in request.json and 'chat_id' not in request.json):
        abort(400, description="Request must be a JSON object with a 'prompt' and 'chat_id' fields.")

    global chat_id, prompt
    chat_id = request.json['chatId']
    prompt = request.json['prompt']
    model_response = fetch_response()
    response = jsonify({
        'response': model_response,
        'status': 200
    })
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response


@app.route('/deletechat/<chatId>', methods=['DELETE'])
def deleletechat(chatId):
    if chatId in users_chat_history:
        del users_chat_history[chatId]
        return jsonify(message=f"Chat {chatId} is successfully deleted"), 200
    else:
        return jsonify(error="Chat not found. Please check again"), 404

@app.errorhandler(HTTPException)
def handle_http_exception(e):
    response_data = {
        "error": e.description,
        "response": "An error occurred. Please check your request.",
        "status": e.code
    }
    return jsonify(response_data), e.code

@app.errorhandler(Exception)
def handle_generic_exception(e):
    if isinstance(e, HTTPException):
        return e

    response_data = {
        "error": "An internal server error occurred.",
        "response": "There is currently a high traffic. Please try again later.",
        "status": 500
    }
    return jsonify(response_data), 500
