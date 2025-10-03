// Listen for messages from the popup or background script
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.action === 'evaluatePrompt') {
        evaluatePrompt(message.prompt)
            .then(result => sendResponse(result))
            .catch(error => sendResponse({ error: error.message }));
        return true; // Indicates we'll respond asynchronously
    }
});

// Function to evaluate a prompt using the CalypsoAgent
async function evaluatePrompt(prompt) {
    try {
        // Get API key from storage
        const result = await chrome.storage.sync.get(['calypsoApiKey']);
        
        if (!result.calypsoApiKey) {
            throw new Error('CalypsoAI API key not found. Please set it in the extension settings.');
        }
        
        // Instead of importing the module directly, send a message to the background script
        // which will handle the evaluation
        return new Promise((resolve, reject) => {
            chrome.runtime.sendMessage(
                { 
                    action: 'evaluatePrompt', 
                    prompt: prompt 
                },
                response => {
                    if (response.error) {
                        reject(new Error(response.error));
                    } else {
                        resolve(response);
                    }
                }
            );
        });
    } catch (error) {
        console.error('Error evaluating prompt:', error);
        return {
            success: false,
            error: error.message
        };
    }
}

// Function to find text input elements on the page
function findPromptInputs() {
    const inputs = [];
    
    // Look for common input elements
    const textInputs = document.querySelectorAll('input[type="text"], textarea');
    textInputs.forEach(input => {
        // Check if the input is visible and likely to be a prompt input
        if (isElementVisible(input) && isLikelyPromptInput(input)) {
            inputs.push({
                element: input,
                placeholder: input.placeholder || '',
                value: input.value || ''
            });
        }
    });
    
    return inputs;
}

// Helper function to check if an element is visible
function isElementVisible(element) {
    const style = window.getComputedStyle(element);
    return style.display !== 'none' && 
           style.visibility !== 'hidden' && 
           element.offsetWidth > 0 && 
           element.offsetHeight > 0;
}

// Helper function to determine if an input is likely to be a prompt input
function isLikelyPromptInput(element) {
    const placeholder = (element.placeholder || '').toLowerCase();
    const name = (element.name || '').toLowerCase();
    const id = (element.id || '').toLowerCase();
    const className = (element.className || '').toLowerCase();
    
    // Keywords that might indicate a prompt input
    const promptKeywords = [
        'prompt', 'message', 'question', 'ask', 'input', 'query', 
        'chat', 'conversation', 'instruction', 'command', 'request'
    ];
    
    // Check if any of the keywords are in the element's attributes
    return promptKeywords.some(keyword => 
        placeholder.includes(keyword) || 
        name.includes(keyword) || 
        id.includes(keyword) || 
        className.includes(keyword)
    );
}

// Notify the background script that the content script is loaded
chrome.runtime.sendMessage({ action: 'contentScriptLoaded' }); 