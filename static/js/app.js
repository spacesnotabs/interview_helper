// Interview Helper App
document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const languageSelector = document.getElementById('language-selector');
    const newChallengeBtn = document.getElementById('new-challenge-btn');
    const hintBtn = document.getElementById('hint-btn');
    const submitBtn = document.getElementById('submit-btn');
    const challengeTitle = document.getElementById('challenge-title');
    const challengeDescription = document.getElementById('challenge-description');
    const resultsDisplay = document.getElementById('results-display');

    // Backend API endpoint
    const API_BASE_URL = '/api';
    
    // Initialize CodeMirror
    const codeEditor = CodeMirror(document.getElementById('code-editor'), {
        mode: 'javascript', // default language
        theme: 'default',
        lineNumbers: true,
        autofocus: true,
        tabSize: 2,
        indentWithTabs: false,
        lineWrapping: true,
        extraKeys: {
            "Tab": function(cm) {
                cm.replaceSelection("  ", "end");
            }
        }
    });

    // Set default code
    setDefaultCode('javascript');

    // Current challenge data
    let currentChallenge = null;
    let currentHintIndex = 0;
    
    // Language mode mapping
    const languageModes = {
        'javascript': 'javascript',
        'python': 'python',
        'java': 'text/x-java',
        'cpp': 'text/x-c++src'
    };
    
    // Event Listeners
    languageSelector.addEventListener('change', handleLanguageChange);
    newChallengeBtn.addEventListener('click', loadNewChallenge);
    hintBtn.addEventListener('click', requestHint);
    submitBtn.addEventListener('click', submitSolution);

    // Load initial challenge
    loadNewChallenge();

    // Language Change Handler
    function handleLanguageChange() {
        const selectedLanguage = languageSelector.value;
        
        // Update CodeMirror mode
        codeEditor.setOption('mode', languageModes[selectedLanguage]);
        
        // Set default code for the selected language
        setDefaultCode(selectedLanguage);
        
        // If we have a current challenge, update the code template
        if (currentChallenge) {
            setCodeTemplate(currentChallenge, selectedLanguage);
        }
    }
    
    // Set default starter code based on language
    function setDefaultCode(language) {
        let defaultCode = '';
        
        switch (language) {
            case 'javascript':
                defaultCode = '// Your JavaScript solution here\nfunction solution(input) {\n  // Write your code here\n  return null;\n}\n';
                break;
            case 'python':
                defaultCode = '# Your Python solution here\ndef solution(input):\n  # Write your code here\n  pass\n';
                break;
            case 'java':
                defaultCode = 'class Solution {\n  // Your Java solution here\n  public static Object solution(Object input) {\n    // Write your code here\n    return null;\n  }\n}\n';
                break;
            case 'cpp':
                defaultCode = '// Your C++ solution here\n#include <iostream>\n#include <vector>\n\nusing namespace std;\n\n// Write your code here\nauto solution(auto input) {\n  // Implementation\n  return {};\n}\n';
                break;
        }
        
        codeEditor.setValue(defaultCode);
    }
    
    // Set code template based on challenge and language
    function setCodeTemplate(challenge, language) {
        // This would normally use challenge-specific templates
        // For now, we'll just use the default code
        setDefaultCode(language);
    }

    // Load a new coding challenge from the backend
    async function loadNewChallenge() {
        showLoading(challengeDescription);
        
        try {
            // Reset the hint index for the new challenge
            currentHintIndex = 0;
            
            // Call the backend API to get a random challenge
            const response = await fetch(`${API_BASE_URL}/challenge`);
            const data = await response.json();
            
            if (response.ok) {
                currentChallenge = data;
                displayChallenge(data);
                
                // Set code template based on current language
                setCodeTemplate(data, languageSelector.value);
            } else {
                throw new Error(data.error || 'Failed to load challenge');
            }
        } catch (error) {
            console.error('Error loading challenge:', error);
            challengeDescription.innerHTML = `<p class="error">Failed to load challenge: ${error.message}</p>`;
        }
    }
    
    // Request a hint for the current challenge from the backend
    async function requestHint() {
        if (!currentChallenge) return;
        
        showLoading(resultsDisplay);
        
        try {
            // Call the backend API to get a hint
            const response = await fetch(`${API_BASE_URL}/hint`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    challengeId: currentChallenge.id,
                    hintIndex: currentHintIndex,
                    code: codeEditor.getValue()  // Send the current code for context-aware hints
                })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                resultsDisplay.innerHTML = `<p class="hint"><strong>Hint:</strong> ${data.hint}</p>`;
                
                // Increment the hint index if it's not the last hint
                if (!data.isLastHint) {
                    currentHintIndex++;
                }
            } else {
                throw new Error(data.error || 'Failed to get hint');
            }
        } catch (error) {
            console.error('Error getting hint:', error);
            resultsDisplay.innerHTML = `<p class="error">Failed to get hint: ${error.message}</p>`;
        }
    }
    
    // Submit the user's solution to the backend
    async function submitSolution() {
        if (!currentChallenge) return;
        
        const userCode = codeEditor.getValue();
        const language = languageSelector.value;
        
        showLoading(resultsDisplay);
        
        try {
            // Call the backend API to submit the solution
            const response = await fetch(`${API_BASE_URL}/submit`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    challengeId: currentChallenge.id,
                    code: userCode,
                    language: language
                })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                // Display the feedback from the LLM
                resultsDisplay.innerHTML = `<div class="feedback">${data.feedback}</div>`;
            } else {
                throw new Error(data.error || 'Failed to submit solution');
            }
        } catch (error) {
            console.error('Error submitting solution:', error);
            resultsDisplay.innerHTML = `<p class="error">Failed to submit solution: ${error.message}</p>`;
        }
    }
    
    // Display challenge in the UI
    function displayChallenge(challenge) {
        challengeTitle.textContent = challenge.title;
        
        let examplesHTML = '';
        if (challenge.examples && challenge.examples.length > 0) {
            examplesHTML = `
                <div class="examples">
                    <h4>Examples:</h4>
                    <ul>
                        ${challenge.examples.map(ex => `
                            <li>
                                <p><strong>Input:</strong> ${ex.input}</p>
                                <p><strong>Output:</strong> ${ex.output}</p>
                                ${ex.explanation ? `<p><strong>Explanation:</strong> ${ex.explanation}</p>` : ''}
                            </li>
                        `).join('')}
                    </ul>
                </div>
            `;
        }

        let constraintsHTML = '';
        if (challenge.constraints && challenge.constraints.length > 0) {
            constraintsHTML = `
                <div class="constraints">
                    <h4>Constraints:</h4>
                    <ul>
                        ${challenge.constraints.map(constraint => `<li>${constraint}</li>`).join('')}
                    </ul>
                </div>
            `;
        }

        challengeDescription.innerHTML = `
            <p>${challenge.description}</p>
            ${examplesHTML}
            ${constraintsHTML}
        `;
    }
    
    // Show loading state in a container
    function showLoading(container) {
        container.innerHTML = '<p class="loading">Loading...</p>';
    }
});