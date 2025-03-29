import os
import json
import google.generativeai as genai
from dotenv import load_dotenv
import uuid

# Load environment variables
load_dotenv()

# Configure the Gemini API
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

class LLMService:
    def __init__(self):
        self.model_name: str | None = None
        self.api_key: str | None = None
        self._model = None
        self.chat = None
        self.previous_challenges: list[str] = []  # Track previous challenge titles/descriptions
        
        if not GEMINI_API_KEY:
            print("Warning: GEMINI_API_KEY not set in environment variables")
    
    @property
    def model(self):
        """Lazily initialize and return the model"""
        if not self._model and GEMINI_API_KEY:
            self._model = genai.GenerativeModel(model_name=self.model_name)
        return self._model
    
    def initialize_model(self, model_name: str, api_key: str | None=None):
        """Initialize the model with the provided API key and model name"""
        if api_key:
            self.api_key = api_key
            genai.configure(api_key=self.api_key)
        elif GEMINI_API_KEY:
            genai.configure(api_key=GEMINI_API_KEY)
        else:
            return "API key not configured."
        
        if model_name:
            self.model_name = model_name
        else:
            return "Model name not provided."
        
        try:
            self._model = genai.GenerativeModel(model_name=self.model_name)
            return "Model initialized successfully."
        except Exception as e:
            print(f"Error initializing model: {e}")
            return f"Error initializing model. Please check your API key and model name. Error details: {str(e)}"
            
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
    
    def get_solution_feedback(self, challenge, code, language="javascript"):
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
    
    def generate_challenge(self, difficulty=None, additional_context=None, language="javascript"):
        """Generate a single coding challenge using LLM"""
        if not GEMINI_API_KEY:
            return None
        
        try:
            prompt = self._create_challenge_prompt(difficulty, additional_context, language)
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
                
                # Add to previous challenges list for future reference
                self.previous_challenges.append({
                    "title": challenge_data["title"],
                    "description_snippet": challenge_data["description"][:100]  # Store just a snippet
                })
                
                # Keep the list at a reasonable size
                if len(self.previous_challenges) > 20:
                    self.previous_challenges = self.previous_challenges[-20:]
                
                return challenge_data
            except json.JSONDecodeError as e:
                print(f"Error parsing challenge JSON: {e}")
                print(f"Raw response: {response.result}")
                return None
        except Exception as e:
            print(f"Error calling Gemini API: {e}")
            return None
            
    def generate_multiple_challenges(self, count=5, difficulties=None, additional_context=None, language="javascript"):
        """Generate multiple coding challenges using LLM"""
        challenges = []
        
        if difficulties is None:
            difficulties = ["easy", "medium", "hard"]
        
        # Distribute difficulties across the requested count
        assigned_difficulties = []
        for i in range(count):
            assigned_difficulties.append(difficulties[i % len(difficulties)])
        
        # Generate challenges with assigned difficulties
        for difficulty in assigned_difficulties:
            challenge = self.generate_challenge(difficulty, additional_context, language)
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
    
    def _create_challenge_prompt(self, difficulty=None, additional_context=None, language="javascript"):
        """Create a prompt for generating a coding challenge"""
        difficulty_str = f"The difficulty level should be {difficulty}." if difficulty else "Choose a random difficulty level (easy, medium, or hard)."
        
        # Add additional context if provided
        context_str = ""
        if additional_context:
            context_str = f"The challenge should relate to the following context or topic: {additional_context}."
        
        # Add previous challenges to avoid repetition
        previous_challenges_str = ""
        if self.previous_challenges:
            previous_challenges_str = "Avoid generating challenges similar to these:\n"
            for i, challenge in enumerate(self.previous_challenges):
                previous_challenges_str += f"{i+1}. {challenge['title']}: {challenge['description_snippet']}...\n"
        
        return f"""
        Generate a unique, interesting coding interview challenge in {language}. {difficulty_str} {context_str}
        
        {previous_challenges_str}
        
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
        6. Is novel and different from previous challenges listed above
        7. Specifically addresses the provided context or topic if specified
        
        Return ONLY the JSON without any other text.
        """