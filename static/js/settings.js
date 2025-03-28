// Interview Helper - API Settings Management
document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const apiKeyForm = document.getElementById('api-key-form');
    const apiKeyList = document.getElementById('api-key-list');
    const apiKeyIdInput = document.getElementById('api-key-id');
    const llmProviderSelect = document.getElementById('llm-provider');
    const llmModelSelect = document.getElementById('llm-model');
    const apiKeyInput = document.getElementById('api-key');
    const toggleVisibilityBtn = document.getElementById('toggle-visibility');
    const saveKeyBtn = document.getElementById('save-key-btn');
    const cancelBtn = document.getElementById('cancel-btn');
    const messageContainer = document.getElementById('message-container');

    // Backend API endpoint
    const API_BASE_URL = '/api';
    
    // Model options for each provider
    const modelOptions = {
        'GEMINI': [
            { value: 'gemini-2.0-flash', label: 'Gemini 2.0 Flash' },
            { value: 'gemini-2.0-pro', label: 'Gemini 2.0 Pro' },
            { value: 'gemini-1.5-pro', label: 'Gemini 1.5 Pro' },
            { value: 'gemini-1.0-pro', label: 'Gemini 1.0 Pro' }
        ],
        'ANTHROPIC': [
            { value: 'claude-3-opus', label: 'Claude 3 Opus' },
            { value: 'claude-3-sonnet', label: 'Claude 3 Sonnet' },
            { value: 'claude-3-haiku', label: 'Claude 3 Haiku' },
            { value: 'claude-2.1', label: 'Claude 2.1' }
        ],
        'OPENAI': [
            { value: 'gpt-4o', label: 'GPT-4o' },
            { value: 'gpt-4-turbo', label: 'GPT-4 Turbo' },
            { value: 'gpt-4', label: 'GPT-4' },
            { value: 'gpt-3.5-turbo', label: 'GPT-3.5 Turbo' }
        ]
    };

    // Event Listeners
    llmProviderSelect.addEventListener('change', updateModelOptions);
    toggleVisibilityBtn.addEventListener('click', toggleApiKeyVisibility);
    apiKeyForm.addEventListener('submit', handleFormSubmit);
    cancelBtn.addEventListener('click', resetForm);

    // Current user and API keys
    let currentUser = null;
    let userApiKeys = [];

    // Check if user is logged in on page load
    checkAuthStatus().then(() => {
        if (currentUser) {
            loadUserApiKeys();
        } else {
            showLoginRequired();
        }
    });

    // Check authentication status
    async function checkAuthStatus() {
        try {
            const response = await fetch(`${API_BASE_URL}/user`);
            
            if (response.ok) {
                const data = await response.json();
                currentUser = data;
                return true;
            } else {
                return false;
            }
        } catch (error) {
            console.error('Error checking authentication status:', error);
            return false;
        }
    }

    // Show login required message
    function showLoginRequired() {
        apiKeyList.innerHTML = `
            <div class="login-required">
                <p>You must be logged in to manage API keys.</p>
                <a href="/" class="btn primary">Go to Login</a>
            </div>
        `;
        apiKeyForm.style.display = 'none';
    }

    // Load user's API keys
    async function loadUserApiKeys() {
        try {
            const response = await fetch(`${API_BASE_URL}/api-keys`);
            
            if (response.ok) {
                const data = await response.json();
                userApiKeys = data.apiKeys || [];
                renderApiKeyList();
            } else if (response.status === 401) {
                showLoginRequired();
            } else {
                showMessage('Failed to load API keys. Please try again.', 'error');
            }
        } catch (error) {
            console.error('Error loading API keys:', error);
            showMessage('Error loading API keys. Please try again.', 'error');
        }
    }

    // Render the list of API keys
    function renderApiKeyList() {
        if (userApiKeys.length === 0) {
            apiKeyList.innerHTML = `
                <div class="no-keys">
                    <p>You haven't added any API keys yet.</p>
                </div>
            `;
            return;
        }

        const keyItems = userApiKeys.map(key => `
            <div class="api-key-item">
                <div class="key-info">
                    <div class="provider-badge ${key.llm_provider.toLowerCase()}">${key.llm_provider}</div>
                    <div class="key-details">
                        <h4>${key.model || 'Default Model'}</h4>
                        <p class="masked-key">${key.api_key}</p>
                    </div>
                </div>
                <div class="key-actions">
                    <button class="btn small edit-key" data-id="${key.id}">Edit</button>
                    <button class="btn small delete-key" data-id="${key.id}">Delete</button>
                </div>
            </div>
        `).join('');

        apiKeyList.innerHTML = `
            <div class="api-keys-container">
                ${keyItems}
            </div>
        `;

        // Add event listeners to edit and delete buttons
        document.querySelectorAll('.edit-key').forEach(btn => {
            btn.addEventListener('click', () => editApiKey(btn.dataset.id));
        });

        document.querySelectorAll('.delete-key').forEach(btn => {
            btn.addEventListener('click', () => deleteApiKey(btn.dataset.id));
        });
    }

    // Edit an API key
    function editApiKey(keyId) {
        const apiKey = userApiKeys.find(key => key.id == keyId);
        
        if (apiKey) {
            apiKeyIdInput.value = apiKey.id;
            llmProviderSelect.value = apiKey.llm_provider;
            updateModelOptions();
            
            // Set the model if it exists
            if (apiKey.model) {
                llmModelSelect.value = apiKey.model;
            }
            
            // Don't display the actual API key for security,
            // but indicate that it will be updated
            apiKeyInput.value = '';
            apiKeyInput.placeholder = 'Enter new API key or leave blank to keep current';
            
            saveKeyBtn.textContent = 'Update API Key';
            scrollToForm();
        }
    }

    // Delete an API key
    async function deleteApiKey(keyId) {
        if (!confirm('Are you sure you want to delete this API key?')) {
            return;
        }

        try {
            const response = await fetch(`${API_BASE_URL}/api-keys/${keyId}`, {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            if (response.ok) {
                showMessage('API key deleted successfully!', 'success');
                loadUserApiKeys(); // Refresh the list
            } else {
                const data = await response.json();
                throw new Error(data.error || 'Failed to delete API key');
            }
        } catch (error) {
            console.error('Error deleting API key:', error);
            showMessage(`Error: ${error.message}`, 'error');
        }
    }

    // Handle form submission
    async function handleFormSubmit(event) {
        event.preventDefault();

        const keyId = apiKeyIdInput.value.trim();
        const provider = llmProviderSelect.value;
        const model = llmModelSelect.value;
        const apiKey = apiKeyInput.value;

        // Validation
        if (!provider) {
            showMessage('Please select an LLM provider', 'error');
            return;
        }

        if (!model) {
            showMessage('Please select a model', 'error');
            return;
        }

        // If editing and API key is empty, we need to check if we're keeping the existing key
        if (!apiKey && !keyId) {
            showMessage('Please enter an API key', 'error');
            return;
        }

        // Prepare payload
        const payload = {
            llm_provider: provider,
            model: model,
            api_key: apiKey
        };

        try {
            let response;
            let successMessage;
            
            if (keyId) {
                // Update existing key
                response = await fetch(`${API_BASE_URL}/api-keys/${keyId}`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(payload)
                });
                successMessage = 'API key updated successfully!';
            } else {
                // Create new key
                response = await fetch(`${API_BASE_URL}/api-keys`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(payload)
                });
                successMessage = 'API key added successfully!';
            }

            if (response.ok) {
                showMessage(successMessage, 'success');
                resetForm();
                loadUserApiKeys(); // Refresh the list
            } else {
                const data = await response.json();
                throw new Error(data.error || 'Failed to save API key');
            }
        } catch (error) {
            console.error('Error saving API key:', error);
            showMessage(`Error: ${error.message}`, 'error');
        }
    }

    // Update model options based on selected provider
    function updateModelOptions() {
        const provider = llmProviderSelect.value;
        llmModelSelect.innerHTML = '<option value="">-- Select Model --</option>';
        
        if (provider && modelOptions[provider]) {
            modelOptions[provider].forEach(model => {
                const option = document.createElement('option');
                option.value = model.value;
                option.textContent = model.label;
                llmModelSelect.appendChild(option);
            });
        }
    }

    // Toggle API key visibility
    function toggleApiKeyVisibility() {
        if (apiKeyInput.type === 'password') {
            apiKeyInput.type = 'text';
            toggleVisibilityBtn.textContent = 'Hide';
        } else {
            apiKeyInput.type = 'password';
            toggleVisibilityBtn.textContent = 'Show';
        }
    }

    // Reset the form to add new key state
    function resetForm() {
        apiKeyForm.reset();
        apiKeyIdInput.value = '';
        saveKeyBtn.textContent = 'Save API Key';
        apiKeyInput.placeholder = 'Enter your API key';
        updateModelOptions();
    }

    // Scroll to the form section
    function scrollToForm() {
        document.querySelector('.add-api-key-form').scrollIntoView({
            behavior: 'smooth',
            block: 'start'
        });
    }

    // Show a message to the user
    function showMessage(message, type) {
        messageContainer.innerHTML = `<div class="message ${type}">${message}</div>`;
        messageContainer.style.display = 'block';
        
        setTimeout(() => {
            messageContainer.style.opacity = '1';
        }, 10);
        
        setTimeout(() => {
            messageContainer.style.opacity = '0';
            setTimeout(() => {
                messageContainer.style.display = 'none';
                messageContainer.innerHTML = '';
            }, 300);
        }, 3000);
    }
});