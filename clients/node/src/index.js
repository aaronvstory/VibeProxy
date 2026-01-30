/**
 * VibeProxy Node.js Client
 *
 * A lightweight OpenAI SDK wrapper for communicating with VibeProxy,
 * which provides a unified OpenAI-compatible API for Claude, GPT, Gemini, and other models.
 *
 * @example
 * import { VibeProxyClient } from 'vibeproxy-client';
 *
 * const client = new VibeProxyClient();
 * const response = await client.chat([
 *   { role: 'user', content: 'Hello!' }
 * ]);
 * console.log(response.content);
 */

import OpenAI from 'openai';

/**
 * VibeProxy Client
 *
 * Provides a simple interface for making chat completion requests to VibeProxy
 * using the OpenAI SDK. Supports both streaming and non-streaming responses.
 */
export class VibeProxyClient {
  /**
   * Create a new VibeProxy client
   *
   * @param {Object} options - Configuration options
   * @param {string} [options.baseUrl='http://localhost:8317/v1'] - VibeProxy base URL
   * @param {string} [options.model='claude-sonnet-4-5-20250929'] - Default model to use
   * @param {string} [options.apiKey='x'] - API key (any non-empty string works)
   * @param {number} [options.maxTokens=4096] - Default max tokens for responses
   * @param {number} [options.timeout=60000] - Request timeout in milliseconds
   */
  constructor(options = {}) {
    this.baseUrl = options.baseUrl || process.env.VIBEPROXY_URL || 'http://localhost:8317/v1';
    this.defaultModel = options.model || process.env.VIBEPROXY_MODEL || 'claude-sonnet-4-5-20250929';
    this.apiKey = options.apiKey || 'x'; // VibeProxy accepts any non-empty key
    this.defaultMaxTokens = options.maxTokens || 4096;
    this.timeout = options.timeout || 60000;

    // Initialize OpenAI client pointing to VibeProxy
    this.openai = new OpenAI({
      baseURL: this.baseUrl,
      apiKey: this.apiKey,
      timeout: this.timeout
    });

    // Track conversation history per session for multi-turn
    this.conversationHistory = new Map();
    // Track active abort controllers
    this.abortControllers = new Map();
  }

  /**
   * Get appropriate temperature for a model
   * GPT-5 requires temperature=1, Claude/others work with 0-1
   *
   * @param {string} model - Model ID
   * @param {number|null} [requestedTemp=null] - User-requested temperature
   * @returns {number} Appropriate temperature for the model
   */
  getTemperature(model, requestedTemp = null) {
    if (model.toLowerCase().includes('gpt-5')) {
      return 1.0; // Required for GPT-5
    }
    return requestedTemp ?? 0; // Deterministic by default for Claude/others
  }

  /**
   * Check if VibeProxy is healthy and responding
   *
   * @returns {Promise<{healthy: boolean, message: string, modelCount?: number}>}
   */
  async healthCheck() {
    try {
      const models = await this.listModels();
      return {
        healthy: true,
        message: `Healthy (${models.length} models available)`,
        modelCount: models.length
      };
    } catch (error) {
      if (error.code === 'ECONNREFUSED') {
        return {
          healthy: false,
          message: 'Connection refused - VibeProxy not running or tunnel down'
        };
      }
      if (error.name === 'AbortError') {
        return {
          healthy: false,
          message: 'Connection timeout'
        };
      }
      return {
        healthy: false,
        message: error.message
      };
    }
  }

  /**
   * List available models from VibeProxy
   *
   * @returns {Promise<Array<{id: string, object: string, created: number, owned_by: string}>>}
   */
  async listModels() {
    const response = await this.openai.models.list();
    return response.data;
  }

  /**
   * Send a chat completion request (non-streaming)
   *
   * @param {Array<{role: string, content: string|Array}>} messages - Conversation messages
   * @param {Object} [options] - Request options
   * @param {string} [options.model] - Model to use (defaults to client's default)
   * @param {number} [options.maxTokens] - Maximum tokens to generate
   * @param {number} [options.temperature] - Sampling temperature (auto-set for GPT-5)
   * @param {AbortSignal} [options.signal] - AbortSignal for cancellation
   * @returns {Promise<{content: string, finishReason: string, usage: Object, model: string}>}
   */
  async chat(messages, options = {}) {
    const model = options.model || this.defaultModel;
    const maxTokens = options.maxTokens || this.defaultMaxTokens;
    const temperature = this.getTemperature(model, options.temperature);

    const response = await this.openai.chat.completions.create({
      model,
      messages,
      max_tokens: maxTokens,
      temperature
    }, {
      signal: options.signal
    });

    const choice = response.choices?.[0];
    return {
      content: choice?.message?.content || '',
      finishReason: choice?.finish_reason || 'stop',
      usage: response.usage || {},
      model: response.model
    };
  }

  /**
   * Send a streaming chat completion request
   *
   * @param {Array<{role: string, content: string|Array}>} messages - Conversation messages
   * @param {Object} [options] - Request options
   * @param {string} [options.model] - Model to use (defaults to client's default)
   * @param {number} [options.maxTokens] - Maximum tokens to generate
   * @param {number} [options.temperature] - Sampling temperature (auto-set for GPT-5)
   * @param {AbortSignal} [options.signal] - AbortSignal for cancellation
   * @yields {{type: string, content?: string, finishReason?: string}} Stream chunks
   */
  async *chatStream(messages, options = {}) {
    const model = options.model || this.defaultModel;
    const maxTokens = options.maxTokens || this.defaultMaxTokens;
    const temperature = this.getTemperature(model, options.temperature);

    const stream = await this.openai.chat.completions.create({
      model,
      messages,
      max_tokens: maxTokens,
      temperature,
      stream: true
    }, {
      signal: options.signal
    });

    for await (const chunk of stream) {
      const delta = chunk.choices?.[0]?.delta;
      const finishReason = chunk.choices?.[0]?.finish_reason;

      if (delta?.content) {
        yield {
          type: 'text',
          content: delta.content
        };
      }

      if (finishReason) {
        yield {
          type: 'done',
          finishReason
        };
      }
    }
  }

  /**
   * Multi-turn conversation with automatic history management
   *
   * @param {string} sessionId - Unique session identifier
   * @param {string} userMessage - User message to send
   * @param {Object} [options] - Request options
   * @param {string} [options.model] - Model to use
   * @param {number} [options.maxTokens] - Maximum tokens to generate
   * @param {number} [options.temperature] - Sampling temperature
   * @param {string} [options.systemPrompt] - System prompt (added on first message)
   * @returns {Promise<{content: string, finishReason: string, messageCount: number}>}
   */
  async conversation(sessionId, userMessage, options = {}) {
    // Get or initialize conversation history
    let history = this.conversationHistory.get(sessionId) || [];

    // Add system prompt on first message if provided
    if (history.length === 0 && options.systemPrompt) {
      history.push({
        role: 'system',
        content: options.systemPrompt
      });
    }

    // Add user message
    history.push({
      role: 'user',
      content: userMessage
    });

    // Make request
    const response = await this.chat(history, options);

    // Add assistant response to history
    history.push({
      role: 'assistant',
      content: response.content
    });

    // Store updated history
    this.conversationHistory.set(sessionId, history);

    return {
      content: response.content,
      finishReason: response.finishReason,
      messageCount: history.length
    };
  }

  /**
   * Streaming multi-turn conversation with automatic history management
   *
   * @param {string} sessionId - Unique session identifier
   * @param {string} userMessage - User message to send
   * @param {Object} [options] - Request options
   * @yields {{type: string, content?: string, finishReason?: string}} Stream chunks
   */
  async *conversationStream(sessionId, userMessage, options = {}) {
    // Get or initialize conversation history
    let history = this.conversationHistory.get(sessionId) || [];

    // Add system prompt on first message if provided
    if (history.length === 0 && options.systemPrompt) {
      history.push({
        role: 'system',
        content: options.systemPrompt
      });
    }

    // Add user message
    history.push({
      role: 'user',
      content: userMessage
    });

    // Collect full response for history
    let fullContent = '';

    // Stream response
    for await (const chunk of this.chatStream(history, options)) {
      if (chunk.type === 'text') {
        fullContent += chunk.content;
      }
      yield chunk;
    }

    // Add assistant response to history
    history.push({
      role: 'assistant',
      content: fullContent
    });

    // Store updated history
    this.conversationHistory.set(sessionId, history);
  }

  /**
   * Get conversation history for a session
   *
   * @param {string} sessionId - Session identifier
   * @returns {Array<{role: string, content: string}>} Message history
   */
  getHistory(sessionId) {
    return this.conversationHistory.get(sessionId) || [];
  }

  /**
   * Clear conversation history for a session
   *
   * @param {string} sessionId - Session identifier
   */
  clearHistory(sessionId) {
    this.conversationHistory.delete(sessionId);
  }

  /**
   * Create an abort controller for a request
   * Useful for cancelling streaming requests
   *
   * @param {string} requestId - Unique request identifier
   * @returns {AbortController}
   */
  createAbortController(requestId) {
    const controller = new AbortController();
    this.abortControllers.set(requestId, controller);
    return controller;
  }

  /**
   * Abort a request by its ID
   *
   * @param {string} requestId - Request identifier
   * @returns {boolean} True if aborted, false if not found
   */
  abort(requestId) {
    const controller = this.abortControllers.get(requestId);
    if (controller) {
      controller.abort();
      this.abortControllers.delete(requestId);
      return true;
    }
    return false;
  }

  /**
   * Test a specific model with a simple request
   *
   * @param {string} [model] - Model to test (defaults to client's default)
   * @returns {Promise<{success: boolean, message: string, latencyMs?: number}>}
   */
  async testModel(model) {
    const testModel = model || this.defaultModel;
    const startTime = Date.now();

    try {
      const response = await this.chat([
        { role: 'user', content: 'Reply with just the word "OK"' }
      ], {
        model: testModel,
        maxTokens: 10
      });

      const latencyMs = Date.now() - startTime;
      return {
        success: true,
        message: `OK (${latencyMs}ms)`,
        latencyMs
      };
    } catch (error) {
      return {
        success: false,
        message: error.message
      };
    }
  }
}

// Default export for convenience
export default VibeProxyClient;
