import os
import json
import google.generativeai as genai
from dotenv import load_dotenv
import uuid

# Load environment variables
load_dotenv()

# Configure the Gemini API
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

class LLMService:
    def __init__(self, model_name="gemini-2.0-flash"):
        self.model_name = model_name
        self._model = None
        self.chat = None
        
        if not GEMINI_API_KEY:
            print("Warning: GEMINI_API_KEY not set in environment variables")
    
    @property
    def model(self):
        """Lazily initialize and return the model"""
        if not self._model and GEMINI_API_KEY:
            self._model = genai.GenerativeModel(model_name=self.model_name)
        return self._model
    
    def start_new_chat(self, history=None):
        """Start a new chat session with the model"""
        if not GEMINI_API_KEY:
            return "API key not configured. Please add GEMINI_API_KEY to your .env file."
        
        try:
            self.chat = self.model.start_chat(history=history)
            return "New chat session started successfully."
        except Exception as e:
            print(f"Error starting chat session: {e}")
            return f"Error starting chat session. Error details: {str(e)}"
    
    def chat_message(self, message):
        """Send a message to the active chat session and get a response"""
        if not GEMINI_API_KEY:
            return "API key not configured. Please add GEMINI_API_KEY to your .env file."
        
        if not self.chat:
            self.start_new_chat()
        
        try:
            response = self.chat.send_message(message)
            return response.text
        except Exception as e:
            print(f"Error in chat conversation: {e}")
            return f"Error in chat conversation. Please try again later. Error details: {str(e)}"
    
    def get_solution_feedback(self, challenge, code, language):
        """Generate feedback for a submitted solution"""
        if not GEMINI_API_KEY:
            return "API key not configured. Please add GEMINI_API_KEY to your .env file."
        
        try:
            prompt = self._create_feedback_prompt(challenge, code, language)
            response = self.model.generate_content(contents=prompt)
            return response.text
        except Exception as e:
            print(f"Error calling Gemini API: {e}")
            return f"Error generating feedback. Please try again later. Error details: {str(e)}"
    
    def get_hint(self, challenge, current_code=None, hint_index=0):
        """Generate a hint for the challenge, considering the current code if provided"""
        if not GEMINI_API_KEY:
            return "API key not configured. Please add GEMINI_API_KEY to your .env file."
       
        try:
            prompt = self._create_hint_prompt(challenge, current_code)
            response = self.model.generate_content(contents=prompt)
            return response.text
        except Exception as e:
            print(f"Error calling Gemini API: {e}")
            return f"Error generating hint. Please try again later. Error details: {str(e)}"
    
    def generate_challenge(self, difficulty=None):
        """Generate a coding challenge using LLM"""
        if not GEMINI_API_KEY:
            return None
        
        try:
            prompt = self._create_challenge_prompt(difficulty)
            response = self.model.generate_content(contents=prompt)
            
            # Parse the JSON response
            try:
                # Extract JSON from the response text
                response_text = response.text
                # Remove any markdown code block indicators if present
                if "```json" in response_text:
                    response_text = response_text.split("```json")[1].split("```")[0].strip()
                elif "```" in response_text:
                    response_text = response_text.split("```")[1].split("```")[0].strip()
                
                challenge_data = json.loads(response_text)
                
                # Ensure the challenge has a unique ID
                if "id" not in challenge_data:
                    challenge_data["id"] = str(uuid.uuid4())
                
                return challenge_data
            except json.JSONDecodeError as e:
                print(f"Error parsing challenge JSON: {e}")
                print(f"Raw response: {response.result}")
                return None
        except Exception as e:
            print(f"Error calling Gemini API: {e}")
            return None
            
    def generate_multiple_challenges(self, count=5, difficulties=None):
        """Generate multiple coding challenges"""
        challenges = []
        
        if difficulties is None:
            difficulties = ["easy", "medium", "hard"]
        
        # Distribute difficulties across the requested count
        assigned_difficulties = []
        for i in range(count):
            assigned_difficulties.append(difficulties[i % len(difficulties)])
        
        # Generate challenges with assigned difficulties
        for difficulty in assigned_difficulties:
            challenge = self.generate_challenge(difficulty)
            if challenge:
                challenges.append(challenge)
        
        return challenges
    
    def _create_feedback_prompt(self, challenge, code, language):
        """Create a prompt for generating solution feedback"""
        return f"""
        You are an expert coding interviewer reviewing a candidate's solution. 
        
        Challenge: {challenge['title']}
        Description: {challenge['description']}
        
        Examples:
        {json.dumps(challenge.get('examples', []))}
        
        The candidate submitted this {language} solution:
        ```{language}
        {code}
        ```
        
        Provide structured constructive feedback about the solution. Include:
        1. Whether the solution correctly solves the problem
        2. Time and space complexity analysis
        3. Code quality assessment
        4. Possible optimizations or alternative approaches
        5. Edge cases that might not be handled
        
        Format your response in clear sections with Markdown formatting. After the feedback, please include
        your solution to the problem in the same language for reference.
        """
    
    def _create_hint_prompt(self, challenge, current_code=None):
        """Create a prompt for generating hints"""
        code_context = ""
        if current_code:
            code_context = f"""
            The user has written the following code so far:
            ```
            {current_code}
            ```
            """
        
        return f"""
        You are a helpful coding interview assistant.
        
        Challenge: {challenge['title']}
        Description: {challenge['description']}
        
        Examples:
        {json.dumps(challenge.get('examples', []))}
        {code_context}
        
        Provide a useful hint that will help the user solve the problem without giving away the complete solution.
        The hint should be concise and point them in the right direction.
        """
    
    def _create_challenge_prompt(self, difficulty=None):
        """Create a prompt for generating a coding challenge"""
        difficulty_str = f"The difficulty level should be {difficulty}." if difficulty else "Choose a random difficulty level (easy, medium, or hard)."
        
        return f"""
        Generate a coding interview challenge. {difficulty_str}
        
        The response should be a valid JSON object with the following structure:
        {{
          "id": "unique_identifier",
          "title": "Challenge Title",
          "description": "Detailed description of the problem",
          "examples": [
            {{"input": "Example input", "output": "Example output", "explanation": "Optional explanation"}}
          ],
          "difficulty": "easy|medium|hard",
          "hints": [
            "First hint that guides without giving away the solution",
            "Second hint that provides more direction"
          ]
        }}
        
        Make sure the challenge:
        1. Is clearly defined with unambiguous requirements
        2. Has at least two examples with input and expected output
        3. Has appropriate difficulty level
        4. Includes 2-3 helpful hints that don't give away the solution
        5. Is formatted as valid JSON
        
        Return ONLY the JSON without any other text.
        """