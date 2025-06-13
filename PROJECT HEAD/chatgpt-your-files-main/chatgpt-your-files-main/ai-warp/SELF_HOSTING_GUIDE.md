# Complete Self-Hosting Guide for AI-Warp CLI

This guide outlines how to make the AI-Warp CLI completely self-hosted with no reliance on external payment plans or cloud services, focusing on security and local-only operation.

## Current Architecture Overview

The current AI-Warp CLI architecture uses:

1. **Ollama** - Already operates locally
2. **Supabase** - Can run locally but has cloud deployment options
3. **Warp SDK** - Potential connection to commercial Warp Terminal service
4. **Edge Functions** - Typically deployed to Supabase cloud

## Making Everything Completely Self-Hosted

### 1. Replace Supabase with Direct PostgreSQL + Express API

While Supabase can run locally, it's designed for eventual cloud deployment. For complete independence:

```bash
# Install PostgreSQL directly
# Windows (using Chocolatey)
choco install postgresql

# Or download from PostgreSQL website
# https://www.postgresql.org/download/windows/
```

Create a Docker Compose setup for easy local deployment:

```yaml
# docker-compose.yml
version: '3.8'
services:
  postgres:
    image: postgres:15
    restart: always
    environment:
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_USER: postgres
      POSTGRES_DB: warp
    volumes:
      - postgres-data:/var/lib/postgresql/data
      - ./init-scripts:/docker-entrypoint-initdb.d
    ports:
      - "5432:5432"

  pgadmin:
    image: dpage/pgadmin4
    restart: always
    environment:
      PGADMIN_DEFAULT_EMAIL: admin@admin.com
      PGADMIN_DEFAULT_PASSWORD: ${PGADMIN_PASSWORD}
    ports:
      - "5050:80"
    depends_on:
      - postgres

volumes:
  postgres-data:
```

Replace Supabase client with direct PostgreSQL client:

```typescript
// src/db/postgres-client.ts
import { Pool } from 'pg';
import dotenv from 'dotenv';

dotenv.config();

// Create a PostgreSQL connection pool
const pool = new Pool({
  host: process.env.POSTGRES_HOST || 'localhost',
  port: parseInt(process.env.POSTGRES_PORT || '5432'),
  database: process.env.POSTGRES_DB || 'warp',
  user: process.env.POSTGRES_USER || 'postgres',
  password: process.env.POSTGRES_PASSWORD,
});

export async function insertPage(url, content, textContent, embedding) {
  const client = await pool.connect();
  try {
    const result = await client.query(
      'INSERT INTO pages(url, html_content, text_content, embedding) VALUES($1, $2, $3, $4) RETURNING *',
      [url, content, textContent, embedding]
    );
    return result.rows[0];
  } finally {
    client.release();
  }
}

export async function findSimilarPages(embedding, limit = 5) {
  const client = await pool.connect();
  try {
    const result = await client.query(
      'SELECT * FROM pages ORDER BY embedding <-> $1 LIMIT $2',
      [embedding, limit]
    );
    return result.rows;
  } finally {
    client.release();
  }
}
```

### 2. Replace Edge Functions with Local Express API

Instead of using Supabase Edge Functions, implement a local Express API:

```bash
# Install Express and related packages
npm install express cors body-parser
```

Create a simple Express server for embedding generation:

```typescript
// src/api/server.ts
import express from 'express';
import cors from 'cors';
import bodyParser from 'body-parser';
import { ollama } from '../ollama/processor';
import { insertPage, findSimilarPages } from '../db/postgres-client';

const app = express();
const port = process.env.API_PORT || 3000;

app.use(cors());
app.use(bodyParser.json());

// Generate embeddings endpoint
app.post('/api/generate-embedding', async (req, res) => {
  try {
    const { record } = req.body;
    
    if (!record.text_content) {
      return res.status(400).json({ error: 'Missing text_content in record' });
    }
    
    // Generate embedding using Ollama
    const embedding = await ollama.embeddings({
      model: 'nomic-embed-text',
      prompt: record.text_content.substring(0, 8000),
    });
    
    // Update record with embedding
    const result = await insertPage(
      record.url,
      record.html_content,
      record.text_content,
      embedding
    );
    
    res.json({ success: true, data: result });
  } catch (error) {
    console.error('Error generating embedding:', error);
    res.status(500).json({ error: error.message });
  }
});

// Search similar content endpoint
app.post('/api/search-similar', async (req, res) => {
  try {
    const { embedding, limit } = req.body;
    
    const results = await findSimilarPages(embedding, limit);
    
    res.json({ success: true, data: results });
  } catch (error) {
    console.error('Error searching similar pages:', error);
    res.status(500).json({ error: error.message });
  }
});

app.listen(port, () => {
  console.log(`API server running at http://localhost:${port}`);
});
```

### 3. Enable Vector Search in PostgreSQL

Install pgvector directly instead of relying on Supabase:

```sql
-- Run in PostgreSQL
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE pages (
  id SERIAL PRIMARY KEY,
  url TEXT NOT NULL,
  html_content TEXT,
  text_content TEXT,
  embedding vector(1536),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX ON pages USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
```

### 4. Replace Warp SDK Dependencies

If the Warp SDK has any commercial connections, replace it with open-source alternatives:

1. For CLI framework, use Commander.js directly (which we already do)
2. For filesystem operations, use Node.js built-in 'fs' module
3. For system introspection, use 'os' module in Node.js

### 5. Secure Local Storage

For secure data storage:

```typescript
// src/storage/secure-storage.ts
import fs from 'fs';
import path from 'path';
import crypto from 'crypto';
import os from 'os';

const STORAGE_DIR = path.join(os.homedir(), '.ai-warp');
const ENCRYPTION_KEY = process.env.ENCRYPTION_KEY || 'your-local-encryption-key';

// Ensure storage directory exists
if (!fs.existsSync(STORAGE_DIR)) {
  fs.mkdirSync(STORAGE_DIR, { recursive: true });
}

// Encrypt data before storing
function encrypt(text) {
  const iv = crypto.randomBytes(16);
  const cipher = crypto.createCipheriv('aes-256-cbc', Buffer.from(ENCRYPTION_KEY), iv);
  let encrypted = cipher.update(text);
  encrypted = Buffer.concat([encrypted, cipher.final()]);
  return iv.toString('hex') + ':' + encrypted.toString('hex');
}

// Decrypt stored data
function decrypt(text) {
  const parts = text.split(':');
  const iv = Buffer.from(parts[0], 'hex');
  const encryptedText = Buffer.from(parts[1], 'hex');
  const decipher = crypto.createDecipheriv('aes-256-cbc', Buffer.from(ENCRYPTION_KEY), iv);
  let decrypted = decipher.update(encryptedText);
  decrypted = Buffer.concat([decrypted, decipher.final()]);
  return decrypted.toString();
}

// Store data securely
export function storeData(key, data) {
  const filePath = path.join(STORAGE_DIR, `${key}.enc`);
  const encryptedData = encrypt(JSON.stringify(data));
  fs.writeFileSync(filePath, encryptedData);
}

// Retrieve stored data
export function retrieveData(key) {
  const filePath = path.join(STORAGE_DIR, `${key}.enc`);
  if (!fs.existsSync(filePath)) {
    return null;
  }
  const encryptedData = fs.readFileSync(filePath, 'utf8');
  return JSON.parse(decrypt(encryptedData));
}
```

### 6. Use Docker Compose for Complete Local Deployment

Create a comprehensive Docker Compose file to run everything locally:

```yaml
# Full docker-compose.yml
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_USER: postgres
      POSTGRES_DB: warp
    volumes:
      - postgres-data:/var/lib/postgresql/data
      - ./init-scripts:/docker-entrypoint-initdb.d
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5

  ollama:
    image: ollama/ollama:latest
    volumes:
      - ollama-data:/root/.ollama
    ports:
      - "11434:11434"

  api:
    build:
      context: .
      dockerfile: Dockerfile.api
    depends_on:
      postgres:
        condition: service_healthy
    ports:
      - "3000:3000"
    environment:
      - POSTGRES_HOST=postgres
      - POSTGRES_PORT=5432
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
      - POSTGRES_DB=warp
      - OLLAMA_HOST=http://ollama:11434
      - ENCRYPTION_KEY=${ENCRYPTION_KEY}

volumes:
  postgres-data:
  ollama-data:
```

### 7. Replace Any Remote Data Fetching with Local Alternatives

Instead of fetching data from remote APIs, implement local options:

1. **Web content fetching**: Store cached copies locally
2. **Model downloads**: Use Ollama's local model management
3. **Updates**: Implement manual update checking

### 8. Secure Authentication Without External Services

Implement a simple local authentication system:

```typescript
// src/auth/local-auth.ts
import fs from 'fs';
import path from 'path';
import crypto from 'crypto';
import os from 'os';

const AUTH_FILE = path.join(os.homedir(), '.ai-warp', 'auth.json');

// Initialize auth file if it doesn't exist
if (!fs.existsSync(path.dirname(AUTH_FILE))) {
  fs.mkdirSync(path.dirname(AUTH_FILE), { recursive: true });
}

if (!fs.existsSync(AUTH_FILE)) {
  fs.writeFileSync(AUTH_FILE, JSON.stringify({ users: [] }));
}

// Create a new user
export function createUser(username, password) {
  const authData = JSON.parse(fs.readFileSync(AUTH_FILE, 'utf8'));
  
  // Check if user already exists
  if (authData.users.some(user => user.username === username)) {
    throw new Error('User already exists');
  }
  
  // Hash password
  const salt = crypto.randomBytes(16).toString('hex');
  const hash = crypto.pbkdf2Sync(password, salt, 1000, 64, 'sha512').toString('hex');
  
  // Add user
  authData.users.push({
    username,
    salt,
    hash,
  });
  
  fs.writeFileSync(AUTH_FILE, JSON.stringify(authData));
  return { username };
}

// Verify user
export function verifyUser(username, password) {
  const authData = JSON.parse(fs.readFileSync(AUTH_FILE, 'utf8'));
  const user = authData.users.find(user => user.username === username);
  
  if (!user) {
    return false;
  }
  
  const hash = crypto.pbkdf2Sync(password, user.salt, 1000, 64, 'sha512').toString('hex');
  return hash === user.hash;
}
```

## Complete Self-Hosted Architecture

With these changes, the AI-Warp CLI will be fully self-hosted and independent of any external services:

1. **Local LLM** - Ollama running locally
2. **Local Database** - PostgreSQL with pgvector running locally
3. **Local API** - Express API instead of Edge Functions
4. **Local Storage** - Encrypted filesystem storage
5. **Local Authentication** - Simple file-based authentication

This architecture ensures:
- No data leaves your system
- No dependency on cloud services
- No payment plans required
- Complete control over your data and infrastructure

## Security Considerations

1. **Encryption at Rest**: All sensitive data is encrypted on disk
2. **Local Network Only**: By default, services only bind to localhost
3. **No External API Calls**: All operations happen within your network
4. **No Telemetry**: Remove any usage tracking or analytics
5. **Regular Backups**: Implement local backup solutions for your data

## Scaling Considerations

While this self-hosted solution provides maximum independence and security, it has scaling limitations:

1. Limited to local hardware resources
2. No built-in high availability
3. Manual updates and maintenance

For larger deployments, consider:
- Kubernetes for orchestration
- Replicated PostgreSQL for high availability
- Load balancing for the API service

## Conclusion

By following this guide, you can transform the AI-Warp CLI into a completely self-contained, payment-free, and security-focused tool that operates entirely within your control, with no external dependencies or potential data leakage.

