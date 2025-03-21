// Interview Helper App
document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const languageSelector = document.getElementById('language-selector');
    const difficultySelector = document.getElementById('difficulty-selector');
    const contextInput = document.getElementById('context-input');
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

    // Configure marked.js
    marked.setOptions({
        breaks: true,
        gfm: true,
        headerIds: false
    });

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
    difficultySelector.addEventListener('change', updateDifficultyDisplay);
    newChallengeBtn.addEventListener('click', loadNewChallenge);

    // LLM Selector and API Key Input
    const llmSelector = document.getElementById('llm-selector');
    const apiKeyInput = document.getElementById('api-key-input');
    const apiKeyLabel = document.getElementById('api-key-label');

    llmSelector.addEventListener('change', updateApiKeyLabel);

    function updateApiKeyLabel() {
        const selectedLLM = llmSelector.value;
        switch (selectedLLM) {
            case 'openai':
                apiKeyLabel.textContent = 'OpenAI API Key:';
                break;
            case 'anthropic':
                apiKeyLabel.textContent = 'Anthropic API Key:';
                break;
            case 'gemini':
                apiKeyLabel.textContent = 'Google Gemini API Key:';
                break;
            default:
                apiKeyLabel.textContent = 'API Key:';
        }
    }

    // Initialize the label on page load
    updateApiKeyLabel();
    hintBtn.addEventListener('click', requestHint);
    submitBtn.addEventListener('click', submitSolution);

    // Load initial challenge
    // loadNewChallenge();

    // Language Change Handler
    function handleLanguageChange() {
        const selectedLanguage = languageSelector.value;
        
        // Update CodeMirror mode
        codeEditor.setOption('mode', languageModes[selectedLanguage]);
    }
    
    // Update the display based on the selected difficulty
    function updateDifficultyDisplay() {
        const selectedDifficulty = difficultySelector.value;
        
        // Visual feedback that difficulty has been selected
        if (selectedDifficulty) {
            difficultySelector.classList.add('active');
        } else {
            difficultySelector.classList.remove('active');
        }
    }

    // Load a new coding challenge from the backend
    async function loadNewChallenge() {
        showLoading(challengeDescription);
        
        try {
            // Reset the hint index for the new challenge
            currentHintIndex = 0;
            
            // Get the selected difficulty and additional context
            const selectedDifficulty = difficultySelector.value;
            const additionalContext = contextInput.value.trim();
            const selectedLanguage = languageSelector.value;  // Get the selected language
            
            // Build the API URL with parameters
            let apiUrl = `${API_BASE_URL}/challenge`;
            const params = new URLSearchParams();
            
            if (selectedDifficulty) {
                params.append('difficulty', selectedDifficulty);
            }
            
            if (additionalContext) {
                params.append('context', additionalContext);
            }
            
            // Add the language parameter
            params.append('language', selectedLanguage);
            
            // Add parameters to URL if any exist
            if (params.toString()) {
                apiUrl += `?${params.toString()}`;
            }
            
            // Call the backend API to get a challenge with the specified parameters
            const response = await fetch(apiUrl);
            const data = await response.json();
            
            if (response.ok) {
                currentChallenge = data;
                displayChallenge(data);
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
                // Format hint with markdown parser
                const formattedHint = marked.parse(data.hint);
                resultsDisplay.innerHTML = `<div class="hint"><strong>Hint:</strong> ${formattedHint}</div>`;
                
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
                // Format the feedback with markdown parser
                const formattedFeedback = marked.parse(data.feedback);
                resultsDisplay.innerHTML = `<div class="feedback">${formattedFeedback}</div>`;
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
        
        // Show difficulty if available
        const difficultyText = challenge.difficulty ? 
            `<span class="difficulty ${challenge.difficulty.toLowerCase()}">${challenge.difficulty}</span>` : '';
        
        // Format challenge description with markdown
        const formattedDescription = marked.parse(challenge.description);
        
        let examplesHTML = '';
        if (challenge.examples && challenge.examples.length > 0) {
            const exampleItems = challenge.examples.map(ex => {
                const inputFormatted = `<p><strong>Input:</strong> <code>${ex.input}</code></p>`;
                const outputFormatted = `<p><strong>Output:</strong> <code>${ex.output}</code></p>`;
                const explanationFormatted = ex.explanation ? 
                    `<p><strong>Explanation:</strong> ${marked.parse(ex.explanation)}</p>` : '';
                
                return `<li>${inputFormatted}${outputFormatted}${explanationFormatted}</li>`;
            }).join('');
            
            examplesHTML = `
                <div class="examples">
                    <h4>Examples:</h4>
                    <ul class="example-list">
                        ${exampleItems}
                    </ul>
                </div>
            `;
        }

        let constraintsHTML = '';
        if (challenge.constraints && challenge.constraints.length > 0) {
            const constraintItems = challenge.constraints.map(constraint => 
                `<li>${marked.parse(constraint)}</li>`
            ).join('');
            
            constraintsHTML = `
                <div class="constraints">
                    <h4>Constraints:</h4>
                    <ul class="constraint-list">
                        ${constraintItems}
                    </ul>
                </div>
            `;
        }

        challengeDescription.innerHTML = `
            <div class="challenge-header">
                ${difficultyText}
            </div>
            <div class="challenge-content">
                ${formattedDescription}
                ${examplesHTML}
                ${constraintsHTML}
            </div>
        `;
    }
    
    // Show loading state in a container
    function showLoading(container) {
        container.innerHTML = '<p class="loading">Loading...</p>';
    }
});

// API Settings Modal Controls
const apiSettingsBtn = document.getElementById('api-settings-btn');
const apiSettingsModal = document.getElementById('api-settings-modal');
const modalCloseBtn = apiSettingsModal.querySelector('.close-button');

apiSettingsBtn.addEventListener('click', showApiSettingsModal);
modalCloseBtn.addEventListener('click', hideApiSettingsModal);

function showApiSettingsModal() {
    apiSettingsModal.style.display = 'block';
}

function hideApiSettingsModal() {
    apiSettingsModal.style.display = 'none';
}

// API Settings Submission
const saveApiSettingsBtn = document.getElementById('save-api-settings-btn');

saveApiSettingsBtn.addEventListener('click', submitApiSettings);

async function submitApiSettings() {
    const selectedLLM = llmSelector.value;
    const apiKey = apiKeyInput.value;

    // Create a dummy request to the backend (replace with actual API call later)
    const response = await fetch('/api/settings', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            llm: selectedLLM,
            apiKey: apiKey
        })
    });

    if (response.ok) {
        console.log('API settings submitted successfully!');
        hideApiSettingsModal();
        // Optional: Provide feedback to the user
        // resultsDisplay.innerHTML = '<p class="success">API settings saved successfully!</p>';
    } else {
        console.error('Failed to submit API settings.');
        // Optional: Display error message to the user
        // resultsDisplay.innerHTML = '<p class="error">Failed to save API settings.</p>';
    }
}