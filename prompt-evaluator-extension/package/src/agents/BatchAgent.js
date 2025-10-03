import { BaseAgent } from './BaseAgent.js';

/**
 * BatchAgent class for processing multiple items in sequence
 * Similar to BatchNode in Pocketflow, but adapted for browser extension context
 */
export class BatchAgent extends BaseAgent {
    constructor(name, batchSize = 10) {
        super(name);
        this.batchSize = batchSize;
        this.processedCount = 0;
        this.totalItems = 0;
    }

    /**
     * Process a single item in the batch
     * @param {any} item - Item to process
     * @returns {Promise<any>} - Processing result
     */
    async processItem(item) {
        throw new Error('processItem() must be implemented by subclass');
    }

    /**
     * Preparation phase - sets up batch processing
     * @param {Map} shared - Shared state
     * @returns {Array} - Items to process
     */
    async prep(shared) {
        const items = shared.get('items') || [];
        this.totalItems = items.length;
        
        if (this.totalItems === 0) {
            console.log('No items to process');
            return [];
        }

        console.log(`Starting batch processing of ${this.totalItems} items...`);
        return items;
    }

    /**
     * Execution phase - processes items in batches
     * @param {Array} items - Items to process
     * @returns {Promise<Array>} - Processing results
     */
    async exec(items) {
        const results = [];
        
        for (let i = 0; i < items.length; i += this.batchSize) {
            const batch = items.slice(i, i + this.batchSize);
            const batchResults = await Promise.all(
                batch.map(item => this.processItem(item))
            );
            results.push(...batchResults);
            
            this.processedCount += batch.length;
            const progress = (this.processedCount / this.totalItems) * 100;
            console.log(`Progress: ${this.processedCount}/${this.totalItems} items processed (${progress.toFixed(1)}%)`);
        }

        return results;
    }

    /**
     * Post-processing phase - handles batch completion
     * @param {Map} shared - Shared state
     * @param {Array} prepResult - Items that were processed
     * @param {Array} execResult - Processing results
     * @returns {string} - Next agent name
     */
    async post(shared, prepResult, execResult) {
        shared.set('batchResults', execResult);
        return 'default';
    }
} 