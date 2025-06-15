// Multi-port server for MemoryMesh
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

// Start the original MemoryMesh server for Claude Desktop
const claudeServer = spawn('node', [path.join(__dirname, 'dist', 'index.js')], {
  env: { ...process.env, PORT: '8001' },
  cwd: __dirname,
  stdio: 'inherit'
});

// Start another instance for Highlight
const highlightServer = spawn('node', [path.join(__dirname, 'dist', 'index.js')], {
  env: { ...process.env, PORT: '8002' },
  cwd: __dirname,
  stdio: 'inherit'
});

// Start another instance for AIChat
const aiChatServer = spawn('node', [path.join(__dirname, 'dist', 'index.js')], {
  env: { ...process.env, PORT: '8003' },
  cwd: __dirname,
  stdio: 'inherit'
});

console.log('MemoryMesh running for Claude Desktop on port 8001');
console.log('MemoryMesh running for Highlight on port 8002');
console.log('MemoryMesh running for AIChat on port 8003');

// Handle process termination
process.on('SIGINT', () => {
  claudeServer.kill();
  highlightServer.kill();
  aiChatServer.kill();
  process.exit();
});
