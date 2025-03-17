# Interview Helper

An interactive application to help you practice coding interview challenges, get hints, and improve your skills.

## Features

- **Challenge Display**: Access a variety of coding challenges
- **Interactive Code Editor**: Write and test your solutions
- **Multiple Language Support**: JavaScript, Python, Java, and C++
- **Hints**: Get helpful hints when you're stuck
- **Solution Feedback**: Receive immediate feedback on your submissions
- **Sample Solutions**: View optimal solutions after solving challenges

## Project Structure

```
interview_helper/
│
├── index.html                 # Main application page
├── static/
│   ├── css/
│   │   └── styles.css         # Application styling
│   └── js/
│       └── app.js             # Frontend JavaScript logic
└── README.md                  # Project documentation
```

## Setup Instructions

The frontend part of this application is built with vanilla JavaScript and can be run directly in a modern web browser.

1. Open `index.html` in your browser to start using the application.
2. Select your preferred programming language from the dropdown.
3. Use the code editor to write your solution to the displayed challenge.
4. Click "Get Hint" if you need assistance.
5. Click "I'm Finished" to submit your solution for evaluation.
6. Use "New Challenge" to load another coding challenge.

## Future Backend Implementation

The frontend is designed to work with a Python Flask backend (to be implemented) that will:
- Provide a larger database of coding challenges
- Execute user code in a secure sandbox environment
- Use LLM technology (like Gemini API) to:
  - Generate custom hints
  - Analyze code submissions
  - Provide detailed feedback on solutions

## Technical Details

### Frontend Technologies
- HTML5
- CSS3
- Vanilla JavaScript
- CodeMirror for the code editor

### Future Backend Technologies (planned)
- Python 3.x
- Flask framework
- Sandbox environment for code execution
- Gemini API or other LLM integration for intelligent assistance
