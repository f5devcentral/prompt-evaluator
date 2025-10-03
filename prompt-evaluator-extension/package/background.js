import { CalypsoAgent } from './src/agents/CalypsoAgent.js';

// Listen for messages from content scripts or popup
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.action === 'contentScriptLoaded') {
        console.log('Content script loaded in tab:', sender.tab.id);
    } else if (message.action === 'evaluatePrompt') {
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
        
        // Create agent and run evaluation
        const agent = new CalypsoAgent('background-agent', result.calypsoApiKey);
        const shared = new Map();
        shared.set('prompts', [prompt]);
        
        const { result: scanResults } = await agent.run(shared);
        const stats = shared.get('scanStats');
        
        return {
            success: true,
            scanResults,
            stats
        };
    } catch (error) {
        console.error('Error evaluating prompt:', error);
        return {
            success: false,
            error: error.message
        };
    }
}

// Listen for tab updates to detect when a user is on a page with a prompt input
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
    if (changeInfo.status === 'complete' && tab.url) {
        // Check if the URL is likely to be a page with a prompt input
        if (isLikelyPromptPage(tab.url)) {
            // Inject the content script if it's not already injected
            chrome.scripting.executeScript({
                target: { tabId: tabId },
                files: ['content.js']
            }).catch(error => {
                console.error('Error injecting content script:', error);
            });
        }
    }
});

// Helper function to determine if a URL is likely to be a page with a prompt input
function isLikelyPromptPage(url) {
    const promptDomains = [
        'openai.com',
        'anthropic.com',
        'google.com',
        'perplexity.ai',
        'you.com',
        'poe.com',
        'character.ai',
        'huggingface.co',
        'replicate.com',
        'stability.ai',
        'midjourney.com',
        'github.com',
        'microsoft.com',
        'notion.so',
        'slack.com',
        'zoom.us'
    ];
    
    return promptDomains.some(domain => url.includes(domain));
}

// Initialize extension
console.log('Prompt Evaluator extension initialized'); 