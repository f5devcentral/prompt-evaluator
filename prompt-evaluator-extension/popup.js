import { CalypsoAgent } from './src/agents/CalypsoAgent.js';

document.addEventListener('DOMContentLoaded', () => {
    // Tab switching
    const tabs = document.querySelectorAll('.tab');
    const tabContents = document.querySelectorAll('.tab-content');
    
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const tabName = tab.getAttribute('data-tab');
            
            // Update active tab
            tabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            
            // Update active content
            tabContents.forEach(content => {
                content.classList.remove('active');
                if (content.id === `${tabName}-tab`) {
                    content.classList.add('active');
                }
            });
        });
    });
    
    // Load saved API key
    chrome.storage.sync.get(['calypsoApiKey'], (result) => {
        if (result.calypsoApiKey) {
            document.getElementById('apiKey').value = result.calypsoApiKey;
            document.getElementById('apiKeyStatus').textContent = 'API key saved';
            document.getElementById('apiKeyStatus').classList.add('success');
        }
    });
    
    // Save API key
    document.getElementById('saveSettingsButton').addEventListener('click', () => {
        const apiKey = document.getElementById('apiKey').value.trim();
        
        if (!apiKey) {
            document.getElementById('apiKeyStatus').textContent = 'Please enter an API key';
            document.getElementById('apiKeyStatus').classList.remove('success');
            document.getElementById('apiKeyStatus').classList.add('error');
            return;
        }
        
        chrome.storage.sync.set({ calypsoApiKey: apiKey }, () => {
            document.getElementById('apiKeyStatus').textContent = 'API key saved successfully';
            document.getElementById('apiKeyStatus').classList.remove('error');
            document.getElementById('apiKeyStatus').classList.add('success');
        });
    });
    
    // Evaluate prompt
    document.getElementById('evaluateButton').addEventListener('click', async () => {
        const prompt = document.getElementById('prompt').value.trim();
        
        if (!prompt) {
            alert('Please enter a prompt to evaluate');
            return;
        }
        
        // Get API key from storage
        chrome.storage.sync.get(['calypsoApiKey'], async (result) => {
            if (!result.calypsoApiKey) {
                alert('Please set your CalypsoAI API key in the Settings tab');
                return;
            }
            
            try {
                // Show loading state
                document.getElementById('evaluateButton').textContent = 'Evaluating...';
                document.getElementById('evaluateButton').disabled = true;
                
                const agent = new CalypsoAgent('popup-agent', result.calypsoApiKey);
                const shared = new Map();
                shared.set('prompts', [prompt]);
                
                const { result: scanResults } = await agent.run(shared);
                const stats = shared.get('scanStats');
                
                // Display results
                document.getElementById('results').style.display = 'block';
                
                // Update stats
                const statsHtml = `
                    <div class="stat-item">
                        <div>Total</div>
                        <div>${stats.total}</div>
                    </div>
                    <div class="stat-item">
                        <div>Safe</div>
                        <div>${stats.safe}</div>
                    </div>
                    <div class="stat-item">
                        <div>Vulnerable</div>
                        <div>${stats.vulnerabilities}</div>
                    </div>
                    <div class="stat-item">
                        <div>Errors</div>
                        <div>${stats.errors}</div>
                    </div>
                `;
                document.getElementById('stats').innerHTML = statsHtml;
                
                // Display result items
                const resultItemsHtml = scanResults.map(result => {
                    if (result.error) {
                        return `
                            <div class="result-item error">
                                <div>Error: ${result.error}</div>
                            </div>
                        `;
                    }
                    
                    const isSafe = result.is_safe;
                    const vulnerabilities = result.scan_result.vulnerabilities || [];
                    const verdict = result.scan_result.verdict || (isSafe ? 'Passed' : 'Flagged');
                    const outcome = result.scan_result.outcome || (isSafe ? 'passed' : 'flagged');
                    
                    // Get the overall outcome from the new API response structure
                    const overallOutcome = result.scan_result.result && result.scan_result.result.outcome 
                        ? result.scan_result.result.outcome 
                        : outcome;
                    
                    return `
                        <div class="result-item ${isSafe ? 'safe' : 'vulnerability'}">
                            <div>${isSafe ? 'Safe' : 'Vulnerable'} (${overallOutcome})</div>
                            ${vulnerabilities.length > 0 ? `
                                <div>Vulnerabilities found:</div>
                                <ul>
                                    ${vulnerabilities.map(v => `<li>${v.description}</li>`).join('')}
                                </ul>
                            ` : ''}
                            ${result.scan_result.risk_score !== undefined ? `
                                <div>Risk Score: ${(result.scan_result.risk_score * 100).toFixed(2)}%</div>
                            ` : ''}
                        </div>
                    `;
                }).join('');
                
                document.getElementById('resultItems').innerHTML = resultItemsHtml;
            } catch (error) {
                console.error(`Error processing prompt: ${error.message}`);
                document.getElementById('results').style.display = 'block';
                document.getElementById('stats').innerHTML = `
                    <div class="stat-item">
                        <div>Error</div>
                        <div>1</div>
                    </div>
                `;
                document.getElementById('resultItems').innerHTML = `
                    <div class="result-item error">
                        <div>Error: ${error.message}</div>
                    </div>
                `;
            } finally {
                // Reset button state
                document.getElementById('evaluateButton').textContent = 'Evaluate Prompt';
                document.getElementById('evaluateButton').disabled = false;
            }
        });
    });
}); 