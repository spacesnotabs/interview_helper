// Interview Helper App
document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const languageSelector = document.getElementById('language-selector');
    const modelSelector = document.getElementById('model-selector');
    const difficultySelector = document.getElementById('difficulty-selector');
    const contextInput = document.getElementById('context-input');
    const newChallengeBtn = document.getElementById('new-challenge-btn');
    const hintBtn = document.getElementById('hint-btn');
    const submitBtn = document.getElementById('submit-btn');
    const challengeTitle = document.getElementById('challenge-title');
    const challengeDescription = document.getElementById('challenge-description');
    const resultsDisplay = document.getElementById('results-display');
    const authBtn = document.getElementById('auth-btn');
    const apiSettingsBtn = document.getElementById('api-settings-btn');

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
    
    // User authentication state
    let currentUser = null;
    
    // Available models from API keys
    let availableModels = [];
    
    // Language mode mapping
    const languageModes = {
        'javascript': 'javascript',
        'python': 'python',
        'java': 'text/x-java',
        'cpp': 'text/x-c++src'
    };
    
    // Event Listeners
    languageSelector.addEventListener('change', handleLanguageChange);
    modelSelector.addEventListener('change', updateModelSelection);
    difficultySelector.addEventListener('change', updateDifficultyDisplay);
    newChallengeBtn.addEventListener('click', loadNewChallenge);
    apiSettingsBtn.addEventListener('click', navigateToSettings);

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
            currentHintIndex = 0;
            const selectedDifficulty = difficultySelector.value;
            const additionalContext = contextInput.value.trim();
            const selectedLanguage = languageSelector.value;

            let modelData = null;
            if (modelSelector.value) {
                modelData = JSON.parse(modelSelector.value);
            }

            const params = new URLSearchParams();
            if (selectedDifficulty) params.append('difficulty', selectedDifficulty);
            if (additionalContext) params.append('context', additionalContext);
            params.append('language', selectedLanguage);
            if (modelData) {
                params.append('provider', modelData.provider);
                params.append('model', modelData.model);
            }

            const apiUrl = `${API_BASE_URL}/challenge?${params.toString()}`;
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
            // Get the selected model
            let modelData = null;
            if (modelSelector.value) {
                try {
                    modelData = JSON.parse(modelSelector.value);
                } catch (e) {
                    console.error('Error parsing model data:', e);
                }
            }
            
            // Call the backend API to get a hint
            const payload = {
                challengeId: currentChallenge.id,
                hintIndex: currentHintIndex,
                code: codeEditor.getValue()  // Send the current code for context-aware hints
            };
            
            // Add model data if available
            if (modelData) {
                payload.provider = modelData.provider;
                payload.key_id = modelData.key_id;
            }
            
            const response = await fetch(`${API_BASE_URL}/hint`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(payload)
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
            // Get the selected model
            let modelData = null;
            if (modelSelector.value) {
                try {
                    modelData = JSON.parse(modelSelector.value);
                } catch (e) {
                    console.error('Error parsing model data:', e);
                }
            }
            
            // Prepare the payload
            const payload = {
                challengeId: currentChallenge.id,
                code: userCode,
                language: language
            };
            
            // Add model data if available
            if (modelData) {
                payload.provider = modelData.provider;
                payload.key_id = modelData.key_id;
            }
            
            // Call the backend API to submit the solution
            const response = await fetch(`${API_BASE_URL}/submit`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(payload)
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
    
    // Authentication functionality
    
    // Get references to authentication modal elements
    const authModal = document.getElementById('auth-modal');
    const loginTab = document.getElementById('login-tab');
    const registerTab = document.getElementById('register-tab');
    const loginForm = document.getElementById('login-form');
    const registerForm = document.getElementById('register-form');
    const loginUsername = document.getElementById('login-username');
    const loginPassword = document.getElementById('login-password');
    const registerUsername = document.getElementById('register-username');
    const registerPassword = document.getElementById('register-password');
    const registerPasswordConfirm = document.getElementById('register-password-confirm');
    const loginError = document.getElementById('login-error');
    const registerError = document.getElementById('register-error');
    const loginBtn = document.getElementById('login-btn');
    const registerBtn = document.getElementById('register-btn');
    const modalCloseBtns = document.querySelectorAll('.close-button');
    
    // Add event listeners for authentication
    authBtn.addEventListener('click', showAuthModal);
    loginTab.addEventListener('click', () => switchAuthTab('login'));
    registerTab.addEventListener('click', () => switchAuthTab('register'));
    loginBtn.addEventListener('click', handleLogin);
    registerBtn.addEventListener('click', handleRegister);
    
    modalCloseBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const modal = this.closest('.modal');
            if (modal) modal.style.display = 'none';
        });
    });
    
    // Check if user is already logged in on page load
    checkAuthStatus();
    
    // Show the authentication modal
    function showAuthModal() {
        // If user is already logged in, log them out
        if (currentUser) {
            handleLogout();
            return;
        }
        
        // Otherwise, show the auth modal
        authModal.style.display = 'block';
    }
    
    // Switch between login and register tabs
    function switchAuthTab(tab) {
        if (tab === 'login') {
            loginTab.classList.add('active');
            registerTab.classList.remove('active');
            loginForm.style.display = 'block';
            registerForm.style.display = 'none';
        } else {
            loginTab.classList.remove('active');
            registerTab.classList.add('active');
            loginForm.style.display = 'none';
            registerForm.style.display = 'block';
        }
        
        // Clear any error messages
        loginError.textContent = '';
        registerError.textContent = '';
    }
    
    // Handle login form submission
    async function handleLogin() {
        const username = loginUsername.value.trim();
        const password = loginPassword.value;
        
        // Simple validation
        if (!username || !password) {
            loginError.textContent = 'Username and password are required';
            return;
        }
        
        try {
            const response = await fetch(`${API_BASE_URL}/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ username, password })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                // Login successful
                currentUser = data.user;
                authModal.style.display = 'none';
                updateAuthUI();
                
                // New: Handle post-login actions
                await handleLoginSuccess();
                
                // Optionally, show a success message
                showUserMessage('Login successful!', 'success');
            } else {
                // Login failed
                loginError.textContent = data.error || 'Login failed';
            }
        } catch (error) {
            console.error('Error during login:', error);
            loginError.textContent = 'An error occurred during login. Please try again.';
        }
    }
    
    // Handle register form submission
    async function handleRegister() {
        const username = registerUsername.value.trim();
        const password = registerPassword.value;
        const confirmPassword = registerPasswordConfirm.value;
        
        // Validation
        if (!username || !password) {
            registerError.textContent = 'Username and password are required';
            return;
        }
        
        if (password !== confirmPassword) {
            registerError.textContent = 'Passwords do not match';
            return;
        }
        
        // Basic password strength check
        if (password.length < 6) {
            registerError.textContent = 'Password should be at least 6 characters long';
            return;
        }
        
        try {
            const response = await fetch(`${API_BASE_URL}/register`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ username, password })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                // Registration successful - auto-login the user
                currentUser = data.user;
                authModal.style.display = 'none';
                updateAuthUI();
                showUserMessage('Account created successfully!', 'success');
            } else {
                // Registration failed
                registerError.textContent = data.error || 'Registration failed';
            }
        } catch (error) {
            console.error('Error during registration:', error);
            registerError.textContent = 'An error occurred during registration. Please try again.';
        }
    }
    
    // Handle user logout
    async function handleLogout() {
        try {
            const response = await fetch(`${API_BASE_URL}/logout`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            if (response.ok) {
                // Logout successful
                currentUser = null;
                updateAuthUI();
                showUserMessage('Logged out successfully!', 'success');
            } else {
                console.error('Logout failed');
            }
        } catch (error) {
            console.error('Error during logout:', error);
        }
    }
    
    // Check if the user is already authenticated
    async function checkAuthStatus() {
        try {
            const response = await fetch(`${API_BASE_URL}/user`);
            
            if (response.ok) {
                const data = await response.json();
                currentUser = data;
                updateAuthUI();
                
                // Once user is authenticated, load their available models
                await loadAvailableModels();
            }
        } catch (error) {
            console.error('Error checking authentication status:', error);
        }
    }
    
    // Update the UI based on authentication status
    function updateAuthUI() {
        if (currentUser) {
            // User is logged in
            authBtn.textContent = `Logout (${currentUser.username})`;
            
            // Load available models when user is logged in
            loadAvailableModels();
        } else {
            // User is not logged in
            authBtn.textContent = 'Login / Register';
            
            // Reset model selector when user logs out
            modelSelector.innerHTML = '<option value="">Login to use models</option>';
            modelSelector.disabled = true;
        }
    }
    
    // Display a temporary message to the user
    function showUserMessage(message, type) {
        resultsDisplay.innerHTML = `<p class="${type}">${message}</p>`;
        
        // Clear the message after a few seconds
        setTimeout(() => {
            resultsDisplay.innerHTML = '<p>Submit your solution or request a hint to see feedback...</p>';
        }, 3000);
    }

    // Navigate to settings page
    function navigateToSettings() {
        window.location.href = '/settings';
    }
    
    // Function to update model dropdown based on available API keys
    async function loadAvailableModels() {
        try {
            if (!currentUser) {
                modelSelector.innerHTML = '<option value="">Login to use models</option>';
                modelSelector.disabled = true;
                return;
            }

            const response = await fetch(`${API_BASE_URL}/api-keys`);
            if (response.ok) {
                const data = await response.json();
                modelSelector.innerHTML = '<option value="">Choose a model</option>';

                if (!data.apiKeys || data.apiKeys.length === 0) {
                    modelSelector.innerHTML = '<option value="">No API keys configured</option>';
                    modelSelector.disabled = true;
                    return;
                }

                for (const key of data.apiKeys) {
                    const provider = key.llm_provider.toLowerCase();
                    const modelsResponse = await fetch(`${API_BASE_URL}/llm-models/${provider}`);
                    if (modelsResponse.ok) {
                        const models = await modelsResponse.json();
                        models.forEach(model => {
                            const option = document.createElement('option');
                            option.value = JSON.stringify({ provider: key.llm_provider, model: model.value });
                            option.textContent = `${key.llm_provider} - ${model.label}`;
                            modelSelector.appendChild(option);
                        });
                    }
                }

                modelSelector.disabled = false;
            } else {
                modelSelector.innerHTML = '<option value="">Error loading models</option>';
                modelSelector.disabled = true;
            }
        } catch (error) {
            console.error('Error loading available models:', error);
            modelSelector.innerHTML = '<option value="">Error loading models</option>';
            modelSelector.disabled = true;
        }
    }
    
    // Function to handle model selection change
    function updateModelSelection() {
        // This function can be expanded later if needed
        console.log('Model selection changed:', modelSelector.value);
    }
    
    // Add this function to handle post-login actions
    async function handleLoginSuccess() {
        // Other login logic...
        
        // Load available models after successful login
        await loadAvailableModels();
    }
});