/**
 * VibeProxy Node.js Client - TypeScript Definitions
 */

export interface VibeProxyClientOptions {
  /** VibeProxy base URL (default: 'http://localhost:8317/v1') */
  baseUrl?: string;
  /** Default model to use (default: 'claude-sonnet-4-5-20250929') */
  model?: string;
  /** API key - any non-empty string works (default: 'x') */
  apiKey?: string;
  /** Default max tokens for responses (default: 4096) */
  maxTokens?: number;
  /** Request timeout in milliseconds (default: 60000) */
  timeout?: number;
}

export interface Message {
  role: 'system' | 'user' | 'assistant';
  content: string | MessageContent[];
}

export interface MessageContent {
  type: 'text' | 'image_url';
  text?: string;
  image_url?: {
    url: string;
  };
}

export interface ChatOptions {
  /** Model to use (overrides client default) */
  model?: string;
  /** Maximum tokens to generate */
  maxTokens?: number;
  /** Sampling temperature (auto-set for GPT-5 models) */
  temperature?: number;
  /** AbortSignal for cancellation */
  signal?: AbortSignal;
}

export interface ConversationOptions extends ChatOptions {
  /** System prompt (added on first message of conversation) */
  systemPrompt?: string;
}

export interface ChatResponse {
  /** Generated content */
  content: string;
  /** Reason for completion ('stop', 'length', etc.) */
  finishReason: string;
  /** Token usage statistics */
  usage: {
    prompt_tokens?: number;
    completion_tokens?: number;
    total_tokens?: number;
  };
  /** Model that was used */
  model: string;
}

export interface ConversationResponse {
  /** Generated content */
  content: string;
  /** Reason for completion */
  finishReason: string;
  /** Total messages in conversation history */
  messageCount: number;
}

export interface StreamChunk {
  type: 'text' | 'done';
  /** Text content (when type='text') */
  content?: string;
  /** Finish reason (when type='done') */
  finishReason?: string;
}

export interface HealthCheckResult {
  healthy: boolean;
  message: string;
  modelCount?: number;
}

export interface Model {
  id: string;
  object: string;
  created: number;
  owned_by: string;
}

export interface TestModelResult {
  success: boolean;
  message: string;
  latencyMs?: number;
}

/**
 * VibeProxy Client
 *
 * A lightweight OpenAI SDK wrapper for communicating with VibeProxy,
 * which provides a unified OpenAI-compatible API for Claude, GPT, Gemini, and other models.
 *
 * @example
 * ```typescript
 * import { VibeProxyClient } from 'vibeproxy-client';
 *
 * const client = new VibeProxyClient();
 * const response = await client.chat([
 *   { role: 'user', content: 'Hello!' }
 * ]);
 * console.log(response.content);
 * ```
 */
export class VibeProxyClient {
  /** VibeProxy base URL */
  baseUrl: string;
  /** Default model for requests */
  defaultModel: string;
  /** API key (any non-empty string) */
  apiKey: string;
  /** Default max tokens */
  defaultMaxTokens: number;
  /** Request timeout in ms */
  timeout: number;

  /**
   * Create a new VibeProxy client
   */
  constructor(options?: VibeProxyClientOptions);

  /**
   * Get appropriate temperature for a model
   * GPT-5 requires temperature=1, others use 0-1
   */
  getTemperature(model: string, requestedTemp?: number | null): number;

  /**
   * Check if VibeProxy is healthy and responding
   */
  healthCheck(): Promise<HealthCheckResult>;

  /**
   * List available models from VibeProxy
   */
  listModels(): Promise<Model[]>;

  /**
   * Send a chat completion request (non-streaming)
   */
  chat(messages: Message[], options?: ChatOptions): Promise<ChatResponse>;

  /**
   * Send a streaming chat completion request
   */
  chatStream(messages: Message[], options?: ChatOptions): AsyncGenerator<StreamChunk, void, unknown>;

  /**
   * Multi-turn conversation with automatic history management
   */
  conversation(sessionId: string, userMessage: string, options?: ConversationOptions): Promise<ConversationResponse>;

  /**
   * Streaming multi-turn conversation with automatic history management
   */
  conversationStream(sessionId: string, userMessage: string, options?: ConversationOptions): AsyncGenerator<StreamChunk, void, unknown>;

  /**
   * Get conversation history for a session
   */
  getHistory(sessionId: string): Message[];

  /**
   * Clear conversation history for a session
   */
  clearHistory(sessionId: string): void;

  /**
   * Create an abort controller for a request
   */
  createAbortController(requestId: string): AbortController;

  /**
   * Abort a request by its ID
   */
  abort(requestId: string): boolean;

  /**
   * Test a specific model with a simple request
   */
  testModel(model?: string): Promise<TestModelResult>;
}

export default VibeProxyClient;
