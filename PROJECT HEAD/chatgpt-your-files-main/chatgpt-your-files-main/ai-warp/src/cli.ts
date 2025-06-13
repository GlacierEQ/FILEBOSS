#!/usr/bin/env node

import { Command } from 'commander';
import os from 'os';
import path from 'path';
import fs from 'fs';
import dotenv from 'dotenv';
import fetch from 'node-fetch';
import { ollama } from './ollama/processor';
import * as db from './db/postgres-client';
import { startServer } from './api/server';

// Load environment variables
dotenv.config();

// API URL
const API_URL = http://localhost:;

// Initialize CLI
const program = new Command();

program
  .name('warp')
  .description('AI-powered Warp CLI with Supabase integration and Ollama for local LLM inference')
  .version('0.1.0');

// Diagnostic command
program
  .command('diagnose')
  .description('Prints a diagnostic summary of the environment')
  .action(async () => {
    console.log('Warp CLI Diagnostic Report');
    console.log('=========================');
    console.log(OS:  );
    console.log(Architecture: );
    console.log(Node.js: );
    console.log(Home Directory: );
    console.log(Current Directory: );
    
    // Check API server health
    try {
      const response = await fetch(${API_URL}/api/health);
      if (response.ok) {
        const data = await response.json();
        console.log(API Server: Running ());
      } else {
        console.log('API Server: Not responding');
      }
    } catch (error) {
      console.log('API Server: Not running or not accessible');
    }
    
    // Check for Ollama
    try {
      const ollamaVersion = require('child_process').execSync('ollama --version').toString().trim();
      console.log(Ollama: );
      
      // List Ollama models
      const modelsList = require('child_process').execSync('ollama list').toString().trim();
      console.log('\nAvailable Ollama Models:');
      console.log(modelsList || 'No models found');
      
    } catch (error) {
      console.log('Ollama: Not installed or not in PATH');
    }
    
    // Check for Docker
    try {
      const dockerVersion = require('child_process').execSync('docker --version').toString().trim();
      console.log(\nDocker: );
      
      // Check Docker containers
      try {
        const dockerPs = require('child_process').execSync('docker ps --format "{{.Names}}: {{.Status}}"').toString().trim();
        console.log('\nRunning Containers:');
        console.log(dockerPs || 'No containers running');
      } catch (e) {
        console.log('Unable to list Docker containers');
      }
      
    } catch (error) {
      console.log('\nDocker: Not installed or not in PATH');
    }
    
    // Check PostgreSQL connection
    try {
      const pgConnected = await db.initDatabase();
      console.log(\nPostgreSQL Connection: );
      if (pgConnected) {
        await db.closeDatabase();
      }
    } catch (error) {
      console.log('\nPostgreSQL Connection: Failed');
    }
  });

// Server commands
program
  .command('server:start')
  .description('Starts the API server for local processing')
  .action(async () => {
    console.log('Starting API server...');
    try {
      await startServer();
      console.log('API server started successfully');
    } catch (error) {
      console.error('Failed to start API server:', error);
      process.exit(1);
    }
  });

// URL fetch and summarize command
program
  .command('agent:fetch')
  .description('Fetches content from a URL and summarizes it using the local LLM')
  .requiredOption('-u, --url <url>', 'The URL to fetch content from')
  .option('-m, --model <model>', 'The model to use for summarization', 'llama2')
  .action(async (options) => {
    console.log(Fetching content from ...);
    
    try {
      // Check if API server is running
      try {
        await fetch(${API_URL}/api/health);
      } catch (error) {
        console.log('API server is not running. Starting it now...');
        startServer().catch(err => {
          console.error('Failed to start API server:', err);
          process.exit(1);
        });
        
        // Wait for server to start
        console.log('Waiting for API server to start...');
        await new Promise(resolve => setTimeout(resolve, 3000));
      }
      
      // Call the summarize endpoint
      const response = await fetch(${API_URL}/api/summarize, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          url: options.url,
          model: options.model,
        }),
      });
      
      if (!response.ok) {
        throw new Error(API request failed with status );
      }
      
      const data = await response.json();
      
      console.log('\nSummary:');
      console.log('========');
      console.log(data.summary);
      console.log('\nSource:', data.source);
      
    } catch (error) {
      console.error('Error fetching and summarizing content:', error);
      process.exit(1);
    }
  });

// Directory scanning command
program
  .command('agent:scan')
  .description('Recursively scans directories and indexes file contents')
  .option('-d, --directory <directory>', 'The directory to scan', process.cwd())
  .option('-m, --model <model>', 'The embedding model to use', 'nomic-embed-text')
  .option('-e, --extensions <extensions>', 'File extensions to include (comma separated)', 'md,txt,js,ts,py,html,css')
  .action(async (options) => {
    console.log(Scanning directory ...);
    
    const extensions = options.extensions.split(',').map(ext => ext.trim());
    console.log(Including file extensions: );
    
    try {
      // Check if API server is running
      try {
        await fetch(${API_URL}/api/health);
      } catch (error) {
        console.log('API server is not running. Starting it now...');
        startServer().catch(err => {
          console.error('Failed to start API server:', err);
          process.exit(1);
        });
        
        // Wait for server to start
        console.log('Waiting for API server to start...');
        await new Promise(resolve => setTimeout(resolve, 3000));
      }
      
      // Initialize database
      await db.initDatabase();
      
      // Walk through the directory recursively
      const walkDir = async (dir, callback) => {
        const files = fs.readdirSync(dir);
        
        for (const file of files) {
          const filePath = path.join(dir, file);
          const stat = fs.statSync(filePath);
          
          if (stat.isDirectory()) {
            await walkDir(filePath, callback);
          } else {
            await callback(filePath, stat);
          }
        }
      };
      
      let processedFiles = 0;
      let errorFiles = 0;
      
      await walkDir(options.directory, async (filePath, stat) => {
        const ext = path.extname(filePath).replace('.', '');
        
        if (extensions.includes(ext)) {
          try {
            console.log(Processing ...);
            
            // Read file content
            const content = fs.readFileSync(filePath, 'utf8');
            
            // Skip if file is too small
            if (content.length < 100) {
              console.log(Skipping  (too small));
              return;
            }
            
            // Generate embedding
            const response = await fetch(${API_URL}/api/generate-embedding, {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
              },
              body: JSON.stringify({
                text: content,
                url: ile://,
              }),
            });
            
            if (!response.ok) {
              throw new Error(API request failed with status );
            }
            
            const data = await response.json();
            console.log(Indexed  with  dimensions);
            processedFiles++;
            
          } catch (error) {
            console.error(Error processing :, error);
            errorFiles++;
          }
        }
      });
      
      console.log('\nScan complete:');
      console.log(Processed  files);
      console.log(Errors in  files);
      
      // Close database connection
      await db.closeDatabase();
      
    } catch (error) {
      console.error('Error scanning directory:', error);
      process.exit(1);
    }
  });

// Similarity search command
program
  .command('search')
  .description('Search for similar content using text query')
  .requiredOption('-q, --query <query>', 'The text query to search for')
  .option('-l, --limit <limit>', 'Maximum number of results to return', '5')
  .option('-m, --model <model>', 'The embedding model to use', 'nomic-embed-text')
  .action(async (options) => {
    console.log(Searching for: "");
    
    try {
      // Check if API server is running
      try {
        await fetch(${API_URL}/api/health);
      } catch (error) {
        console.log('API server is not running. Starting it now...');
        startServer().catch(err => {
          console.error('Failed to start API server:', err);
          process.exit(1);
        });
        
        // Wait for server to start
        console.log('Waiting for API server to start...');
        await new Promise(resolve => setTimeout(resolve, 3000));
      }
      
      // Call the search endpoint
      const response = await fetch(${API_URL}/api/search-similar, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          text: options.query,
          limit: parseInt(options.limit),
        }),
      });
      
      if (!response.ok) {
        throw new Error(API request failed with status );
      }
      
      const data = await response.json();
      
      console.log(\nFound  results:);
      console.log('===================');
      
      if (data.results.length === 0) {
        console.log('No similar content found.');
      } else {
        data.results.forEach((result, index) => {
          console.log(\n. );
          console.log(   Similarity: );
          console.log(   Preview: ...);
        });
      }
      
    } catch (error) {
      console.error('Error searching for similar content:', error);
      process.exit(1);
    }
  });

// Docker commands group
const dockerCmd = program
  .command('docker')
  .description('Manage Docker containers for local services');

dockerCmd
  .command('start')
  .description('Start Docker containers for PostgreSQL and Ollama')
  .action(() => {
    console.log('Starting Docker containers...');
    try {
      require('child_process').execSync('docker-compose up -d', { stdio: 'inherit' });
      console.log('Docker containers started successfully');
    } catch (error) {
      console.error('Failed to start Docker containers:', error);
      process.exit(1);
    }
  });

dockerCmd
  .command('stop')
  .description('Stop Docker containers')
  .action(() => {
    console.log('Stopping Docker containers...');
    try {
      require('child_process').execSync('docker-compose down', { stdio: 'inherit' });
      console.log('Docker containers stopped successfully');
    } catch (error) {
      console.error('Failed to stop Docker containers:', error);
      process.exit(1);
    }
  });

dockerCmd
  .command('status')
  .description('Show Docker container status')
  .action(() => {
    console.log('Docker container status:');
    try {
      require('child_process').execSync('docker-compose ps', { stdio: 'inherit' });
    } catch (error) {
      console.error('Failed to get Docker container status:', error);
      process.exit(1);
    }
  });

// Parse arguments
program.parse(process.argv);

// If no args, show help
if (process.argv.length === 2) {
  program.help();
}
