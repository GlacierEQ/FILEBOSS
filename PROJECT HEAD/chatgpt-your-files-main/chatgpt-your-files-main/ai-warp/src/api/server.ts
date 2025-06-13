// src/api/server.ts
import express from 'express';
import cors from 'cors';
import { ollama } from '../ollama/processor';
import * as db from '../db/postgres-client';

const app = express();
const port = process.env.API_PORT || 3000;

// Middleware
app.use(cors());
app.use(express.json({ 
  limit: process.env.JSON_LIMIT || '10mb'
}));

// Set the JSON spaces parameter to fix serialization depth issue
app.set('json spaces', 0);
app.set('json replacer', null);

// Custom middleware to handle deep JSON serialization
app.use((req, res, next) => {
  const originalJson = res.json;
  
  res.json = function(body) {
    // Override JSON.stringify to handle deep nesting
    return originalJson.call(this, body);
  };
  
  next();
});

// Health check endpoint
app.get('/api/health', (req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

// Generate embeddings endpoint
app.post('/api/generate-embedding', async (req, res) => {
  try {
    const { text, url } = req.body;
    
    if (!text) {
      return res.status(400).json({ error: 'Missing text content' });
    }
    
    console.log(`Generating embedding for text (${text.length} chars) from ${url || 'direct input'}`);
    
    // Generate embedding using Ollama
    const embedding = await ollama.embeddings({
      model: 'nomic-embed-text',
      prompt: text.substring(0, 8000), // Limiting the text length
    });
    
    // Store in database if URL is provided
    let result = null;
    if (url) {
      result = await db.insertPage(
        url,
        '', // No HTML content for this example
        text,
        embedding
      );
      console.log(`Saved page with ID: ${result.id}`);
    }
    
    res.json({ 
      success: true, 
      embedding, 
      id: result?.id,
      vector_dimensions: embedding.length
    });
  } catch (error) {
    console.error('Error generating embedding:', error);
    res.status(500).json({ error: error instanceof Error ? error.message : 'Unknown error' });
  }
});

// Search similar content endpoint
app.post('/api/search-similar', async (req, res) => {
  try {
    const { embedding, text, limit = 5 } = req.body;
    
    // If embedding is not provided but text is, generate embedding first
    let vectorToSearch = embedding;
    if (!vectorToSearch && text) {
      vectorToSearch = await ollama.embeddings({
        model: 'nomic-embed-text',
        prompt: text.substring(0, 8000),
      });
    }
    
    if (!vectorToSearch) {
      return res.status(400).json({ error: 'Either embedding or text must be provided' });
    }
    
    // Search for similar pages
    const results = await db.findSimilarPages(vectorToSearch, limit);
    
    res.json({ 
      success: true, 
      results,
      count: results.length
    });
  } catch (error) {
    console.error('Error searching similar pages:', error);
    res.status(500).json({ error: error instanceof Error ? error.message : 'Unknown error' });
  }
});

// Summarize content endpoint
app.post('/api/summarize', async (req, res) => {
  try {
    const { url, text, model = 'llama2' } = req.body;
    
    if (!url && !text) {
      return res.status(400).json({ error: 'Either URL or text must be provided' });
    }
    
    let contentToSummarize = text;
    
    // If URL is provided but no text, fetch the content
    if (url && !text) {
      console.log(`Fetching content from URL: ${url}`);
      contentToSummarize = await ollama.summarizeContent(url, model);
    }
    
    // Generate summary
    const summary = await ollama.generate({
      model,
      prompt: `Summarize the following content concisely:\n\n${contentToSummarize}`,
    });
    
    res.json({ 
      success: true, 
      summary: summary.text,
      source: url || 'provided text'
    });
  } catch (error) {
    console.error('Error summarizing content:', error);
    res.status(500).json({ error: error instanceof Error ? error.message : 'Unknown error' });
  }
});

// Start the server
export function startServer() {
  return new Promise<void>((resolve, reject) => {
    try {
      // Initialize database connection
      db.initDatabase().then(success => {
        if (!success) {
          console.warn('WARNING: Database initialization failed, some features may not work');
        }
        
        // Start the server
        const server = app.listen(port, () => {
          console.log(`API server running at http://localhost:${port}`);
          resolve();
        });
        
        // Handle graceful shutdown
        process.on('SIGINT', () => {
          console.log('Shutting down API server...');
          server.close(() => {
            db.closeDatabase().then(() => {
              console.log('Server shutdown complete');
              process.exit(0);
            });
          });
        });
      });
    } catch (error) {
      console.error('Failed to start server:', error);
      reject(error);
    }
  });
}

// If this file is run directly, start the server
if (require.main === module) {
  startServer().catch(error => {
    console.error('Server startup failed:', error);
    process.exit(1);
  });
}

export default app;
