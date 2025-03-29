from flask import Flask, request, jsonify, session
from flask_cors import CORS
import os
from dotenv import load_dotenv
from llm_service import LLMService

# Import database components
from database.database import get_db_session, init_db_schema, init_db_connection
from database.config import DatabaseConfig
from database.models import User, LlmApiKey, LlmProvider

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__, static_folder='static')
app.secret_key = os.environ.get('SECRET_KEY', os.urandom(24))
CORS(app)  # Enable CORS for all routes

# Create custom configuration
custom_config = DatabaseConfig(
    db_name=os.environ.get('DB_NAME', 'interview_helper'),
    db_type='postgresql',
    db_host=os.environ.get('DB_HOST', 'localhost'),
    db_user=os.environ.get('DB_USER', 'user'),
    db_password=os.environ.get('DB_PASSWORD', 'password'),
    db_port=os.environ.get('DB_PORT', 5432),
)

# Configure database with custom settings
init_db_connection(custom_config)

# Initialize the database
init_db_schema()

# Teardown database session after each request
@app.teardown_appcontext
def shutdown_session(exception=None):
    db = get_db_session()
    if db is not None:
        db.remove()

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
        db = get_db_session()
        db.add(user)
        db.commit()
        return jsonify({"message": "User registered successfully", "user": user.to_dict()}), 201
    except Exception as e:
        get_db_session().rollback()
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
    language = request.args.get('language', 'javascript')
    # Add model selection parameters
    provider = request.args.get('provider')
    model = request.args.get('model')  # Added model parameter
    
    if challenge_id:
        # If a specific ID is requested, look it up in the challenge_history
        # This would be needed if you want to revisit a specific challenge
        challenge = challenge_history.get(challenge_id)
        
        if not challenge:
            return jsonify({"error": "Challenge not found"}), 404
    else:
        # Fetch API key for the selected provider
        api_key = None
        if provider:
            user_id = session.get('user_id')
            if not user_id:
                return jsonify({"error": "Not logged in"}), 401
            
            try:
                # Convert provider to enum
                provider_enum = LlmProvider[provider.upper()]
                db = get_db_session()
                api_key_entry = db.query(LlmApiKey).filter_by(user_id=user_id, llm_provider=provider_enum).first()
                if api_key_entry:
                    api_key = api_key_entry.api_key
            except KeyError:
                return jsonify({"error": f"Invalid provider: {provider}"}), 400
        
        # Initialize the LLM service with the selected provider, model, and API key
        if provider and model and api_key:
            llm_service.initialize_model(model_name=model, api_key=api_key)
        
        # Generate a new random challenge using LLM
        challenge = llm_service.generate_challenge(difficulty, additional_context, language)
        
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

# API Key Management Routes
@app.route('/api/api-keys', methods=['GET'])
def get_api_keys():
    """Get all API keys for the current user"""
    user_id = session.get('user_id')
    
    if not user_id:
        return jsonify({"error": "Not logged in"}), 401
    
    try:
        db = get_db_session()
        api_keys = LlmApiKey.query.filter_by(user_id=user_id).all()
        
        return jsonify({
            "apiKeys": [key.to_dict() for key in api_keys]
        })
    except Exception as e:
        return jsonify({"error": f"Error retrieving API keys: {str(e)}"}), 500

@app.route('/api/api-keys', methods=['POST'])
def add_api_key():
    """Add a new API key for the current user"""
    user_id = session.get('user_id')
    
    if not user_id:
        return jsonify({"error": "Not logged in"}), 401
    
    data = request.json
    llm_provider = data.get('llm_provider')
    model = data.get('model')
    api_key = data.get('api_key')
    
    if not llm_provider or not api_key:
        return jsonify({"error": "Provider and API key are required"}), 400
    
    try:
        # Convert string to enum
        provider_enum = LlmProvider[llm_provider]
        
        # Create new API key entry
        new_api_key = LlmApiKey(user_id=user_id, llm_provider=provider_enum, api_key=api_key)
        
        # Add optional model field
        if model:
            new_api_key.model = model
        
        # Save to database
        db = get_db_session()
        db.add(new_api_key)
        db.commit()
        
        print(f"Added new API key: Provider={llm_provider}, Model={model}")
        
        return jsonify({
            "message": "API key added successfully",
            "api_key": new_api_key.to_dict()
        }), 201
    except KeyError:
        return jsonify({"error": f"Invalid provider: {llm_provider}"}), 400
    except Exception as e:
        db.rollback()
        return jsonify({"error": f"Error adding API key: {str(e)}"}), 500

@app.route('/api/api-keys/<int:key_id>', methods=['PUT'])
def update_api_key(key_id):
    """Update an existing API key"""
    user_id = session.get('user_id')
    
    if not user_id:
        return jsonify({"error": "Not logged in"}), 401
    
    data = request.json
    llm_provider = data.get('llm_provider')
    model = data.get('model')
    api_key = data.get('api_key')
    
    if not llm_provider:
        return jsonify({"error": "Provider is required"}), 400
    
    try:
        # Get the API key from the database
        db = get_db_session()
        api_key_entry = LlmApiKey.query.filter_by(id=key_id, user_id=user_id).first()
        
        if not api_key_entry:
            return jsonify({"error": "API key not found or not owned by current user"}), 404
        
        # Convert string to enum
        provider_enum = LlmProvider[llm_provider]
        
        # Update fields
        api_key_entry.llm_provider = provider_enum
        
        if model:
            api_key_entry.model = model
        
        # Only update the API key if provided (allows updating provider/model without changing key)
        if api_key:
            api_key_entry.api_key = api_key
        
        # Save changes
        db.commit()
        
        print(f"Updated API key {key_id}: Provider={llm_provider}, Model={model}")
        
        return jsonify({
            "message": "API key updated successfully",
            "api_key": api_key_entry.to_dict()
        })
    except KeyError:
        return jsonify({"error": f"Invalid provider: {llm_provider}"}), 400
    except Exception as e:
        db.rollback()
        return jsonify({"error": f"Error updating API key: {str(e)}"}), 500

@app.route('/api/api-keys/<int:key_id>', methods=['DELETE'])
def delete_api_key(key_id):
    """Delete an API key"""
    user_id = session.get('user_id')
    
    if not user_id:
        return jsonify({"error": "Not logged in"}), 401
    
    try:
        db = get_db_session()
        api_key_entry = LlmApiKey.query.filter_by(id=key_id, user_id=user_id).first()
        
        if not api_key_entry:
            return jsonify({"error": "API key not found or not owned by current user"}), 404
        
        # Delete the API key
        db.delete(api_key_entry)
        db.commit()
        
        print(f"Deleted API key {key_id}")
        
        return jsonify({
            "message": "API key deleted successfully"
        })
    except Exception as e:
        db.rollback()
        return jsonify({"error": f"Error deleting API key: {str(e)}"}), 500

@app.route('/api/llm-models/<provider>', methods=['GET'])
def get_llm_models(provider):
    """Get available models for a specific LLM provider"""
    try:
        # Convert string to enum (will raise KeyError if invalid)
        provider_enum = LlmProvider[provider.upper()]
        # Get models using the enum method
        models = provider_enum.get_models()
        return jsonify(models)
    except KeyError:
        return jsonify({"error": f"Invalid provider: {provider}"}), 400
    except Exception as e:
        return jsonify({"error": f"Error retrieving models: {str(e)}"}), 500

# Add a route to get the settings.html page
@app.route('/settings')
def settings_page():
    return app.send_static_file('settings.html')

if __name__ == '__main__':
    # Initialize challenge history dict
    challenge_history = {}
    
    # No need to pre-generate challenges anymore
    # The app will generate fresh challenges on demand
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
