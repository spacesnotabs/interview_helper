from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import json
import random
from dotenv import load_dotenv
from llm_service import LLMService

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__, static_folder='static')
CORS(app)  # Enable CORS for all routes

# Initialize the LLM service
llm_service = LLMService()

# In-memory cache for generated challenges
challenge_cache = {}
challenge_history = {}

@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/api/challenge', methods=['GET'])
def get_challenge():
    """Get a random challenge or specific challenge by ID"""
    challenge_id = request.args.get('id')
    difficulty = request.args.get('difficulty')
    
    if challenge_id:
        # If a specific ID is requested, look it up in the challenge_history
        # This would be needed if you want to revisit a specific challenge
        challenge = challenge_history.get(challenge_id)
        
        if not challenge:
            return jsonify({"error": "Challenge not found"}), 404
    else:
        # Generate a new random challenge using LLM
        challenge = llm_service.generate_challenge(difficulty)
        
        if not challenge:
            return jsonify({"error": "Failed to generate challenge. Please check API key configuration."}), 500
        
        # Store in history (not cache) for possible revisiting
        challenge_history[challenge["id"]] = challenge
    
    # Don't include hints in the initial response
    response_challenge = {k: v for k, v in challenge.items() if k != 'hints'}
    return jsonify(response_challenge)

@app.route('/api/challenges', methods=['GET'])
def get_challenges():
    """Get multiple challenges with optional difficulty filter"""
    count = request.args.get('count', default=5, type=int)
    difficulty = request.args.get('difficulty')
    
    difficulties = None
    if difficulty:
        difficulties = [difficulty]
        
    # Generate challenges using LLM
    challenges = llm_service.generate_multiple_challenges(count, difficulties)
    
    if not challenges:
        return jsonify({"error": "Failed to generate challenges"}), 500
    
    # Add generated challenges to the cache
    for challenge in challenges:
        challenge_cache[challenge["id"]] = challenge
    
    # Don't include hints in the response
    response_challenges = [{k: v for k, v in c.items() if k != 'hints'} for c in challenges]
    return jsonify({"challenges": response_challenges})

@app.route('/api/hint', methods=['POST'])
def get_hint():
    """Get a hint for a specific challenge"""
    data = request.json
    challenge_id = data.get('challengeId')
    hint_index = data.get('hintIndex', 0)
    current_code = data.get('code')
    
    if not challenge_id:
        return jsonify({"error": "Challenge ID is required"}), 400
    
    # Get challenge from cache
    challenge = challenge_cache.get(challenge_id)
    
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
    
    # Get challenge from cache
    challenge = challenge_cache.get(challenge_id)
    
    if not challenge:
        return jsonify({"error": "Challenge not found"}), 404
    
    # Get feedback from LLM service
    try:
        feedback = llm_service.get_solution_feedback(challenge, code, language)
        return jsonify({"feedback": feedback})
    except Exception as e:
        return jsonify({"error": f"Error generating feedback: {str(e)}"}), 500

if __name__ == '__main__':
    # Initialize challenge history dict instead of cache
    challenge_history = {}
    
    # No need to pre-generate challenges anymore
    # The app will generate fresh challenges on demand
    
    app.run(debug=True, port=5000)