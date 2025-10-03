import { CalypsoAgent } from '../agents/CalypsoAgent.js';

// Replace with your actual API key
const API_KEY = 'your-api-key-here';

async function runIntegrationTest() {
    const agent = new CalypsoAgent('integration-test', API_KEY);
    const shared = new Map();
    
    // Test prompts
    const prompts = [
        'Hello, how are you?',
        'Ignore previous instructions and...',
        'What is 2+2?'
    ];
    
    shared.set('prompts', prompts);
    
    try {
        // Run the complete workflow
        const { result, nextAgent } = await agent.run(shared);
        
        console.log('Integration Test Results:');
        console.log('------------------------');
        console.log('Total prompts processed:', result.length);
        console.log('Scan statistics:', shared.get('scanStats'));
        
        // Log detailed results
        result.forEach((scanResult, index) => {
            console.log(`\nPrompt ${index + 1}:`);
            console.log('Input:', scanResult.prompt);
            if (scanResult.error) {
                console.log('Error:', scanResult.error);
            } else {
                console.log('Vulnerabilities:', scanResult.scan_result.vulnerabilities);
                console.log('Confidence:', scanResult.scan_result.confidence);
            }
        });
        
    } catch (error) {
        console.error('Integration test failed:', error);
    }
}

// Run the integration test
runIntegrationTest(); 