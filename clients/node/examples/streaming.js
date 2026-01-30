/**
 * Streaming Example
 *
 * Demonstrates streaming chat responses from VibeProxy.
 * Run: node examples/streaming.js
 */

import { VibeProxyClient } from '../src/index.js';

async function main() {
  const client = new VibeProxyClient();

  // Check health
  const health = await client.healthCheck();
  if (!health.healthy) {
    console.error('VibeProxy is not available:', health.message);
    process.exit(1);
  }

  console.log('Streaming response:\n');
  console.log('-'.repeat(50));

  // Stream a response
  for await (const chunk of client.chatStream([
    { role: 'user', content: 'Write a haiku about coding.' }
  ])) {
    if (chunk.type === 'text') {
      process.stdout.write(chunk.content);
    } else if (chunk.type === 'done') {
      console.log('\n' + '-'.repeat(50));
      console.log(`\nFinish reason: ${chunk.finishReason}`);
    }
  }
}

// Example with abort controller
async function streamWithAbort() {
  const client = new VibeProxyClient();

  console.log('\n\nStreaming with abort capability:\n');
  console.log('-'.repeat(50));

  // Create abort controller
  const controller = client.createAbortController('request-1');

  // Abort after 2 seconds
  setTimeout(() => {
    console.log('\n[Aborting request...]');
    client.abort('request-1');
  }, 2000);

  try {
    for await (const chunk of client.chatStream([
      { role: 'user', content: 'Write a very long story about a programmer...' }
    ], { signal: controller.signal })) {
      if (chunk.type === 'text') {
        process.stdout.write(chunk.content);
      }
    }
  } catch (error) {
    if (error.name === 'AbortError') {
      console.log('\nRequest was aborted.');
    } else {
      throw error;
    }
  }
}

main()
  .then(streamWithAbort)
  .catch(console.error);
