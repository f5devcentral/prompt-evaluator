/**
 * Base Agent class that provides the foundation for all agents in the system.
 * Similar to the Node class in Pocketflow, but adapted for browser extension context.
 */
export class BaseAgent {
    constructor(name) {
        this.name = name;
        this.shared = new Map();
    }

    /**
     * Preparation phase - called before execution
     * @param {Map} shared - Shared state between agents
     * @returns {any} - Preparation result
     */
    async prep(shared) {
        throw new Error('prep() must be implemented by subclass');
    }

    /**
     * Execution phase - main logic
     * @param {any} inputs - Input from prep phase
     * @returns {any} - Execution result
     */
    async exec(inputs) {
        throw new Error('exec() must be implemented by subclass');
    }

    /**
     * Post-processing phase - called after execution
     * @param {Map} shared - Shared state between agents
     * @param {any} prepResult - Result from prep phase
     * @param {any} execResult - Result from exec phase
     * @returns {string} - Next agent name or 'default'
     */
    async post(shared, prepResult, execResult) {
        return 'default';
    }

    /**
     * Run the complete agent workflow
     * @param {Map} shared - Shared state
     * @returns {Promise<any>} - Final result
     */
    async run(shared) {
        const prepResult = await this.prep(shared);
        const execResult = await this.exec(prepResult);
        const nextAgent = await this.post(shared, prepResult, execResult);
        return { result: execResult, nextAgent };
    }
} 