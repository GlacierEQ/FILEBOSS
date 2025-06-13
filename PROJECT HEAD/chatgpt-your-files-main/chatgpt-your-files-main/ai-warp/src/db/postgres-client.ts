// src/db/postgres-client.ts
import { Pool } from 'pg';
import dotenv from 'dotenv';

// Load environment variables
dotenv.config();

// Create a PostgreSQL connection pool
const pool = new Pool({
  host: process.env.POSTGRES_HOST || 'localhost',
  port: parseInt(process.env.POSTGRES_PORT || '5432'),
  database: process.env.POSTGRES_DB || 'warp',
  user: process.env.POSTGRES_USER || 'postgres',
  password: process.env.POSTGRES_PASSWORD || 'postgres_password',
});

// Initialize database connection
export async function initDatabase() {
  try {
    const client = await pool.connect();
    console.log('Successfully connected to PostgreSQL database');
    
    // Check if pgvector extension is available
    const result = await client.query(
      `SELECT * FROM pg_extension WHERE extname = 'vector'`
    );
    
    if (result.rows.length === 0) {
      console.warn('WARNING: pgvector extension is not installed in the database');
      console.warn('Vector similarity search will not work properly');
    } else {
      console.log('pgvector extension is installed and ready');
    }
    
    client.release();
    return true;
  } catch (error) {
    console.error('Failed to connect to PostgreSQL database:', error);
    return false;
  }
}

/**
 * Insert a new page with content and embedding
 * @param url The URL of the page
 * @param content The HTML content of the page
 * @param textContent The extracted text content
 * @param embedding The vector embedding of the text content
 * @returns The inserted record
 */
export async function insertPage(
  url: string,
  content: string,
  textContent: string,
  embedding: number[]
) {
  const client = await pool.connect();
  try {
    const result = await client.query(
      `INSERT INTO pages(url, html_content, text_content, embedding) 
       VALUES($1, $2, $3, $4) 
       RETURNING *`,
      [url, content, textContent, embedding]
    );
    return result.rows[0];
  } catch (error) {
    console.error('Error inserting page into database:', error);
    throw error;
  } finally {
    client.release();
  }
}

/**
 * Find similar pages based on embedding vector similarity
 * @param embedding The vector embedding to compare against
 * @param limit The maximum number of results to return
 * @returns Similar pages in descending order of similarity
 */
export async function findSimilarPages(embedding: number[], limit: number = 5) {
  const client = await pool.connect();
  try {
    // Using pgvector's <-> operator for cosine distance
    const result = await client.query(
      `SELECT id, url, text_content, embedding <-> $1 AS distance 
       FROM pages 
       ORDER BY distance ASC 
       LIMIT $2`,
      [embedding, limit]
    );
    return result.rows;
  } catch (error) {
    console.error('Error finding similar pages in database:', error);
    throw error;
  } finally {
    client.release();
  }
}

/**
 * Get a page by ID
 * @param id The ID of the page to retrieve
 * @returns The page or null if not found
 */
export async function getPageById(id: string) {
  const client = await pool.connect();
  try {
    const result = await client.query(
      'SELECT * FROM pages WHERE id = $1',
      [id]
    );
    return result.rows.length > 0 ? result.rows[0] : null;
  } catch (error) {
    console.error('Error retrieving page from database:', error);
    throw error;
  } finally {
    client.release();
  }
}

/**
 * Update the embedding for a page
 * @param id The ID of the page
 * @param embedding The new embedding vector
 * @returns The updated page
 */
export async function updatePageEmbedding(id: string, embedding: number[]) {
  const client = await pool.connect();
  try {
    const result = await client.query(
      `UPDATE pages 
       SET embedding = $1, updated_at = CURRENT_TIMESTAMP 
       WHERE id = $2 
       RETURNING *`,
      [embedding, id]
    );
    return result.rows.length > 0 ? result.rows[0] : null;
  } catch (error) {
    console.error('Error updating page embedding:', error);
    throw error;
  } finally {
    client.release();
  }
}

/**
 * Close the database connection pool
 */
export async function closeDatabase() {
  await pool.end();
  console.log('Database connection closed');
}

export default {
  initDatabase,
  insertPage,
  findSimilarPages,
  getPageById,
  updatePageEmbedding,
  closeDatabase
};
