/**
 * Multi-Turn Conversation Example
 *
 * Demonstrates multi-turn conversations with automatic history management.
 * Run: node examples/multi-turn.js
 */

import { VibeProxyClient } from '../src/index.js';
import readline from 'readline';

async function main() {
  const client = new VibeProxyClient();

  // Check health
  const health = await client.healthCheck();
  if (!health.healthy) {
    console.error('VibeProxy is not available:', health.message);
    process.exit(1);
  }

  const sessionId = `session-${Date.now()}`;

  console.log('Multi-turn Conversation Demo');
  console.log('============================\n');

  // First message with system prompt
  console.log('You: What is 2 + 2?');
  let response = await client.conversation(sessionId, 'What is 2 + 2?', {
    systemPrompt: 'You are a helpful math tutor. Keep answers brief.'
  });
  console.log(`Assistant: ${response.content}\n`);

  // Follow-up referencing previous context
  console.log('You: And if I multiply that by 3?');
  response = await client.conversation(sessionId, 'And if I multiply that by 3?');
  console.log(`Assistant: ${response.content}\n`);

  // Another follow-up
  console.log('You: What operations did we do so far?');
  response = await client.conversation(sessionId, 'What operations did we do so far?');
  console.log(`Assistant: ${response.content}\n`);

  // Show history
  console.log('--- Conversation History ---');
  const history = client.getHistory(sessionId);
  history.forEach((msg, i) => {
    console.log(`${i + 1}. [${msg.role}] ${msg.content.substring(0, 50)}...`);
  });

  // Clear history
  client.clearHistory(sessionId);
  console.log('\nHistory cleared.');
}

// Interactive chat demo
async function interactiveChat() {
  const client = new VibeProxyClient();

  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout
  });

  const sessionId = `interactive-${Date.now()}`;

  console.log('\n\nInteractive Chat (type "exit" to quit, "clear" to reset)');
  console.log('=========================================================\n');

  const question = (prompt) => new Promise(resolve => rl.question(prompt, resolve));

  // Set system prompt
  const systemPrompt = 'You are a friendly and helpful assistant.';

  while (true) {
    const userInput = await question('You: ');

    if (userInput.toLowerCase() === 'exit') {
      console.log('Goodbye!');
      rl.close();
      break;
    }

    if (userInput.toLowerCase() === 'clear') {
      client.clearHistory(sessionId);
      console.log('[History cleared]\n');
      continue;
    }

    if (!userInput.trim()) {
      continue;
    }

    // Stream the response
    process.stdout.write('Assistant: ');
    for await (const chunk of client.conversationStream(sessionId, userInput, {
      systemPrompt
    })) {
      if (chunk.type === 'text') {
        process.stdout.write(chunk.content);
      }
    }
    console.log('\n');
  }
}

// Run demos
main()
  .then(() => {
    // Comment out the interactive part for automated testing
    // return interactiveChat();
    console.log('\nTo try interactive chat, uncomment the interactiveChat() call.');
  })
  .catch(console.error);
