import { BatchAgent } from './BatchAgent.js';

/**
 * CalypsoAgent class for interacting with CalypsoAI API
 * Handles scanning prompts for potential injection attacks
 */
export class CalypsoAgent extends BatchAgent {
    constructor(name, apiKey, batchSize = 10) {
        super(name, batchSize);
        this.apiKey = apiKey;
        this.apiEndpoint = 'https://calypsoai.app/backend/v1/scans';
    }

    /**
     * Process a single prompt through CalypsoAI API
     * @param {string} prompt - Prompt to scan
     * @returns {Promise<Object>} - Scan results
     */
    async processItem(prompt) {
        try {
            console.log(`Sending request to ${this.apiEndpoint} with API key: ${this.apiKey.substring(0, 5)}...`);
            
            const response = await fetch(this.apiEndpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.apiKey}`
                },
                body: JSON.stringify({
                    input: prompt,
                    options: {
                        detailed: true,
                        include_metadata: true
                    }
                })
            });

            console.log(`Response status: ${response.status} ${response.statusText}`);
            
            if (!response.ok) {
                let errorMessage = `API request failed with status ${response.status}`;
                
                try {
                    const errorData = await response.json();
                    console.error('Error response data:', JSON.stringify(errorData, null, 2));
                    
                    if (errorData.message) {
                        errorMessage += `: ${errorData.message}`;
                    } else if (errorData.error) {
                        errorMessage += `: ${errorData.error}`;
                    } else if (errorData.detail) {
                        errorMessage += `: ${errorData.detail}`;
                    } else if (typeof errorData === 'object') {
                        // If it's an object but doesn't have standard error fields, stringify it
                        errorMessage += `: ${JSON.stringify(errorData)}`;
                    }
                } catch (parseError) {
                    console.error('Failed to parse error response:', parseError);
                    // If we can't parse the JSON, try to get the text
                    try {
                        const errorText = await response.text();
                        if (errorText) {
                            errorMessage += `: ${errorText}`;
                        }
                    } catch (textError) {
                        console.error('Failed to get error text:', textError);
                    }
                }
                
                throw new Error(errorMessage);
            }

            const result = await response.json();
            console.log('API response:', JSON.stringify(result, null, 2));
            
            // Debug the result structure
            console.log('Result keys:', Object.keys(result));
            
            // Check for the new response structure
            if (result.result) {
                console.log('Result outcome:', result.result.outcome);
                console.log('Scanner results:', result.result.scannerResults);
                
                // Count passed and failed scanners
                const scannerResults = result.result.scannerResults || [];
                const passedScanners = scannerResults.filter(s => s.outcome === 'passed').length;
                const failedScanners = scannerResults.filter(s => s.outcome === 'failed').length;
                
                console.log(`Passed scanners: ${passedScanners}, Failed scanners: ${failedScanners}`);
            } else {
                console.log('Result outcome:', result.outcome);
                console.log('Result verdict:', result.verdict);
                console.log('Result vulnerabilities:', result.vulnerabilities);
                console.log('Result risk_score:', result.risk_score);
                console.log('Result is_safe:', result.is_safe);
            }
            
            // Check if the prompt is safe based on the API response
            const isSafe = this.isPromptSafe(result);
            console.log('Is prompt safe?', isSafe);
            
            return {
                prompt: prompt,
                scan_result: result,
                is_safe: isSafe,
                timestamp: new Date().toISOString()
            };
        } catch (error) {
            console.error(`Error processing prompt: ${error.message}`);
            return {
                prompt: prompt,
                error: error.message,
                is_safe: false, // Assume unsafe on error
                timestamp: new Date().toISOString()
            };
        }
    }

    /**
     * Determine if a prompt is safe based on the API response
     * @param {Object} result - API response
     * @returns {boolean} - Whether the prompt is safe
     */
    isPromptSafe(result) {
        console.log('Checking if prompt is safe...');
        
        // Check for the overall outcome in the result
        if (result.result && result.result.outcome) {
            console.log(`Found overall outcome: ${result.result.outcome}`);
            return result.result.outcome === 'cleared';
        }
        
        // Check for verdict field (Passed or Flagged)
        if (result.verdict) {
            console.log(`Found verdict: ${result.verdict}`);
            return result.verdict === 'Passed';
        }
        
        // Check for outcome field (passed or flagged)
        if (result.outcome) {
            console.log(`Found outcome: ${result.outcome}`);
            return result.outcome === 'passed';
        }
        
        // Check for vulnerabilities in the response
        if (result.vulnerabilities && result.vulnerabilities.length > 0) {
            console.log(`Found vulnerabilities: ${result.vulnerabilities.length}`);
            return false;
        }
        
        // Check for risk score if available
        if (result.risk_score !== undefined) {
            console.log(`Found risk score: ${result.risk_score}`);
            // Consider high risk scores as unsafe
            return result.risk_score < 0.5;
        }
        
        // Check for safety flag if available
        if (result.is_safe !== undefined) {
            console.log(`Found is_safe flag: ${result.is_safe}`);
            return result.is_safe;
        }
        
        // If we can't determine safety, assume unsafe
        console.log('Could not determine safety, assuming unsafe');
        return false;
    }

    /**
     * Preparation phase - validates API key and input
     * @param {Map} shared - Shared state
     * @returns {Array} - Prompts to process
     */
    async prep(shared) {
        if (!this.apiKey) {
            throw new Error('CalypsoAI API key is required');
        }

        const prompts = shared.get('prompts') || [];
        if (!Array.isArray(prompts)) {
            throw new Error('Input must be an array of prompts');
        }

        return prompts;
    }

    /**
     * Post-processing phase - stores results and calculates statistics
     * @param {Map} shared - Shared state
     * @param {Array} prepResult - Prompts that were processed
     * @param {Array} execResult - Scan results
     * @returns {string} - Next agent name
     */
    async post(shared, prepResult, execResult) {
        const stats = this.calculateStats(execResult);
        shared.set('scanResults', execResult);
        shared.set('scanStats', stats);
        return 'default';
    }

    /**
     * Calculate statistics from scan results
     * @param {Array} results - Scan results
     * @returns {Object} - Statistics
     */
    calculateStats(results) {
        const stats = {
            total: results.length,
            errors: 0,
            vulnerabilities: 0,
            safe: 0
        };

        results.forEach(result => {
            if (result.error) {
                stats.errors++;
            } else if (!result.is_safe) {
                stats.vulnerabilities++;
            } else {
                stats.safe++;
            }
        });

        return stats;
    }
} 