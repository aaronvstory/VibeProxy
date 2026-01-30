# VibeProxy Node.js Client

A lightweight Node.js client for [VibeProxy](https://github.com/yourusername/VibeProxy) - an OAuth proxy that provides a unified OpenAI-compatible API for Claude, GPT, Gemini, and other models.

## Features

- **OpenAI SDK Wrapper** - Familiar API for JavaScript/TypeScript developers
- **Streaming Support** - Async generators for real-time responses
- **Auto-Temperature** - Automatically sets `temperature=1` for GPT-5 models
- **Multi-Turn Conversations** - Built-in history management
- **Abort Support** - Cancel requests with AbortController
- **TypeScript Types** - Full type definitions included

## Installation

```bash
npm install vibeproxy-client
```

Or install from source:

```bash
cd clients/node
npm install
```

## Quick Start

```javascript
import { VibeProxyClient } from 'vibeproxy-client';

const client = new VibeProxyClient();

// Simple chat
const response = await client.chat([
  { role: 'user', content: 'Hello!' }
]);
console.log(response.content);

// Streaming
for await (const chunk of client.chatStream([
  { role: 'user', content: 'Write a haiku' }
])) {
  if (chunk.type === 'text') {
    process.stdout.write(chunk.content);
  }
}
```

## Configuration

```javascript
const client = new VibeProxyClient({
  baseUrl: 'http://localhost:8317/v1',  // VibeProxy URL
  model: 'claude-sonnet-4-5-20250929',   // Default model
  apiKey: 'x',                           // Any non-empty string
  maxTokens: 4096,                       // Default max tokens
  timeout: 60000                         // Request timeout (ms)
});
```

### Environment Variables

```bash
VIBEPROXY_URL=http://localhost:8317/v1
VIBEPROXY_MODEL=claude-sonnet-4-5-20250929
```

## API Reference

### `VibeProxyClient`

#### Constructor

```typescript
new VibeProxyClient(options?: {
  baseUrl?: string;      // Default: 'http://localhost:8317/v1'
  model?: string;        // Default: 'claude-sonnet-4-5-20250929'
  apiKey?: string;       // Default: 'x'
  maxTokens?: number;    // Default: 4096
  timeout?: number;      // Default: 60000
})
```

#### `healthCheck()`

Check if VibeProxy is responding.

```javascript
const { healthy, message, modelCount } = await client.healthCheck();
// { healthy: true, message: 'Healthy (42 models available)', modelCount: 42 }
```

#### `listModels()`

List available models.

```javascript
const models = await client.listModels();
// [{ id: 'claude-sonnet-4-5-20250929', object: 'model', ... }, ...]
```

#### `chat(messages, options?)`

Non-streaming chat completion.

```javascript
const response = await client.chat([
  { role: 'system', content: 'You are helpful.' },
  { role: 'user', content: 'Hello!' }
], {
  model: 'claude-opus-4-5-20251101',
  maxTokens: 1024,
  temperature: 0.7
});

console.log(response.content);      // "Hello! How can I help you?"
console.log(response.finishReason); // "stop"
console.log(response.usage);        // { prompt_tokens: 10, completion_tokens: 8, total_tokens: 18 }
```

#### `chatStream(messages, options?)`

Streaming chat completion using async generator.

```javascript
for await (const chunk of client.chatStream(messages)) {
  if (chunk.type === 'text') {
    process.stdout.write(chunk.content);
  } else if (chunk.type === 'done') {
    console.log(`\nDone: ${chunk.finishReason}`);
  }
}
```

#### `conversation(sessionId, userMessage, options?)`

Multi-turn conversation with automatic history management.

```javascript
// First message (with system prompt)
let response = await client.conversation('session-1', 'What is 2 + 2?', {
  systemPrompt: 'You are a math tutor.'
});

// Follow-up (context is maintained)
response = await client.conversation('session-1', 'Multiply that by 3');
```

#### `conversationStream(sessionId, userMessage, options?)`

Streaming version of `conversation()`.

```javascript
for await (const chunk of client.conversationStream('session-1', 'Tell me more')) {
  if (chunk.type === 'text') {
    process.stdout.write(chunk.content);
  }
}
```

#### `getHistory(sessionId)`

Get conversation history.

```javascript
const history = client.getHistory('session-1');
// [{ role: 'system', content: '...' }, { role: 'user', content: '...' }, ...]
```

#### `clearHistory(sessionId)`

Clear conversation history.

```javascript
client.clearHistory('session-1');
```

#### `testModel(model?)`

Test a model with a simple request.

```javascript
const result = await client.testModel('gpt-5.2-codex');
// { success: true, message: 'OK (1234ms)', latencyMs: 1234 }
```

### Abort Support

Cancel requests using AbortController:

```javascript
const controller = client.createAbortController('request-1');

// Start streaming
const stream = client.chatStream(messages, { signal: controller.signal });

// Cancel after 5 seconds
setTimeout(() => client.abort('request-1'), 5000);

try {
  for await (const chunk of stream) {
    // ...
  }
} catch (error) {
  if (error.name === 'AbortError') {
    console.log('Request cancelled');
  }
}
```

## Model-Specific Notes

### GPT-5 Temperature

GPT-5 models **require** `temperature=1`. The client handles this automatically:

```javascript
// Temperature auto-set to 1 for GPT-5
const response = await client.chat(messages, { model: 'gpt-5.2-codex' });
```

### Claude Models

Claude models support temperatures 0-1:

```javascript
// Deterministic (default)
await client.chat(messages, { temperature: 0 });

// Creative
await client.chat(messages, { temperature: 0.7 });
```

### Extended Thinking (Claude)

Use the `-thinking-N` suffix for Claude's extended thinking:

```javascript
await client.chat(messages, {
  model: 'claude-sonnet-4-5-20250929-thinking-5000'
});
```

## Examples

See the `examples/` directory:

```bash
# Basic chat
node examples/basic-chat.js

# Streaming responses
node examples/streaming.js

# Multi-turn conversations
node examples/multi-turn.js
```

## TypeScript

Full TypeScript support with included type definitions:

```typescript
import { VibeProxyClient, Message, ChatResponse } from 'vibeproxy-client';

const client = new VibeProxyClient();

const messages: Message[] = [
  { role: 'user', content: 'Hello!' }
];

const response: ChatResponse = await client.chat(messages);
```

## Troubleshooting

### Connection Refused

VibeProxy is not running or the SSH tunnel is down:

```javascript
const health = await client.healthCheck();
if (!health.healthy) {
  console.error(health.message);
  // "Connection refused - VibeProxy not running or tunnel down"
}
```

### GPT-5 Empty Responses

Ensure temperature is set to 1 (handled automatically by this client).

### Model Not Found

Use `listModels()` to see available models:

```javascript
const models = await client.listModels();
console.log(models.map(m => m.id));
```

## License

MIT
