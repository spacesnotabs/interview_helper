from flask import Flask, request, jsonify, session
from flask_cors import CORS
import os
import json
import random
from dotenv import load_dotenv
from llm_service import LLMService
# Import database components
from database import db_session, init_db, User

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__, static_folder='static')
app.secret_key = os.environ.get('SECRET_KEY', os.urandom(24))
CORS(app)  # Enable CORS for all routes

# Initialize the database
init_db()

# Teardown database session after each request
@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()

# Initialize the LLM service
llm_service = LLMService()

# In-memory history for generated challenges
challenge_history = {}

@app.route('/')
def index():
    return app.send_static_file('index.html')

# User Authentication Routes
@app.route('/api/register', methods=['POST'])
def register():
    """Register a new user"""
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400
    
    # Check if user already exists
    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        return jsonify({"error": "Username already exists"}), 409
    
    # Create new user
    try:
        user = User(username=username, password=password)
        db_session.add(user)
        db_session.commit()
        return jsonify({"message": "User registered successfully", "user": user.to_dict()}), 201
    except Exception as e:
        db_session.rollback()
        return jsonify({"error": f"Registration failed: {str(e)}"}), 500

@app.route('/api/login', methods=['POST'])
def login():
    """Login a user"""
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400
    
    # Find the user
    user = User.query.filter_by(username=username).first()
    
    if not user or not user.check_password(password):
        return jsonify({"error": "Invalid username or password"}), 401
    
    # Set session variable
    session['user_id'] = user.id
    
    return jsonify({"message": "Login successful", "user": user.to_dict()})

@app.route('/api/logout', methods=['POST'])
def logout():
    """Logout current user"""
    session.pop('user_id', None)
    return jsonify({"message": "Logged out successfully"})

@app.route('/api/user', methods=['GET'])
def get_current_user():
    """Get current logged in user"""
    user_id = session.get('user_id')
    
    if not user_id:
        return jsonify({"error": "Not logged in"}), 401
    
    user = User.query.get(user_id)
    
    if not user:
        session.pop('user_id', None)
        return jsonify({"error": "User not found"}), 404
    
    return jsonify(user.to_dict())

# Existing routes
@app.route('/api/challenge', methods=['GET'])
def get_challenge():
    """Get a random challenge or specific challenge by ID"""
    challenge_id = request.args.get('id')
    difficulty = request.args.get('difficulty')
    additional_context = request.args.get('context')
    language = request.args.get('language', 'javascript')  # Add language parameter
    
    if challenge_id:
        # If a specific ID is requested, look it up in the challenge_history
        # This would be needed if you want to revisit a specific challenge
        challenge = challenge_history.get(challenge_id)
        
        if not challenge:
            return jsonify({"error": "Challenge not found"}), 404
    else:
        # Generate a new random challenge using LLM
        challenge = llm_service.generate_challenge(difficulty, additional_context, language)  # Pass language
        
        if not challenge:
            return jsonify({"error": "Failed to generate challenge. Please check API key configuration."}), 500
        
        # Store in history for possible revisiting and to prevent repetition
        challenge_history[challenge["id"]] = challenge
    
    # Don't include hints in the initial response
    response_challenge = {k: v for k, v in challenge.items() if k != 'hints'}
    return jsonify(response_challenge)

@app.route('/api/hint', methods=['POST'])
def get_hint():
    """Get a hint for a specific challenge"""
    data = request.json
    challenge_id = data.get('challengeId')
    hint_index = data.get('hintIndex', 0)
    current_code = data.get('code')
    
    if not challenge_id:
        return jsonify({"error": "Challenge ID is required"}), 400
    
    # Get challenge from history
    challenge = challenge_history.get(challenge_id)
    
    if not challenge:
        return jsonify({"error": "Challenge not found"}), 404
    
    # Get hint from LLM service
    hint = llm_service.get_hint(challenge, current_code, hint_index)
    
    # Check if this is the last predefined hint
    hints = challenge.get("hints", [])
    is_last_predefined_hint = hint_index >= len(hints) - 1
    
    return jsonify({
        "hint": hint,
        "isLastHint": is_last_predefined_hint
    })

@app.route('/api/submit', methods=['POST'])
def submit_solution():
    """Handle solution submission and provide feedback using LLM"""
    data = request.json
    challenge_id = data.get('challengeId')
    code = data.get('code')
    language = data.get('language', 'javascript')
    
    if not challenge_id or not code:
        return jsonify({"error": "Challenge ID and code are required"}), 400
    
    # Get challenge from history
    challenge = challenge_history.get(challenge_id)
    
    if not challenge:
        return jsonify({"error": "Challenge not found"}), 404
    
    # Get feedback from LLM service
    try:
        feedback = llm_service.get_solution_feedback(challenge, code, language)
        return jsonify({"feedback": feedback})
    except Exception as e:
        return jsonify({"error": f"Error generating feedback: {str(e)}"}), 500

@app.route('/api/settings', methods=['POST'])
def update_api_settings():
    """Handle API settings submission (LLM and API key)"""
    data = request.json
    llm = data.get('llm')
    api_key = data.get('apiKey')

    # For now, just print the received data
    print(f"Received API settings: LLM - {llm}, API Key - {api_key}")

    # In the future, you would update the LLM service with the new settings here
    # llm_service.update_settings(llm, api_key)

    return jsonify({"message": "API settings updated successfully"}), 200

if __name__ == '__main__':
    # Initialize challenge history dict
    challenge_history = {}
    
    # No need to pre-generate challenges anymore
    # The app will generate fresh challenges on demand
    
    app.run(debug=True, port=5000)