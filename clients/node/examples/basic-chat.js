/**
 * Basic Chat Example
 *
 * Demonstrates simple non-streaming chat with VibeProxy.
 * Run: node examples/basic-chat.js
 */

import { VibeProxyClient } from '../src/index.js';

async function main() {
  // Create client with default settings
  const client = new VibeProxyClient();

  // Check health first
  console.log('Checking VibeProxy health...');
  const health = await client.healthCheck();
  console.log(`Status: ${health.message}\n`);

  if (!health.healthy) {
    console.error('VibeProxy is not available. Make sure it is running.');
    process.exit(1);
  }

  // Simple chat request
  console.log('Sending chat request...\n');

  const response = await client.chat([
    { role: 'system', content: 'You are a helpful assistant that gives concise answers.' },
    { role: 'user', content: 'What is VibeProxy in one sentence?' }
  ]);

  console.log('Response:', response.content);
  console.log('\nUsage:', response.usage);
  console.log('Finish reason:', response.finishReason);
}

main().catch(console.error);
