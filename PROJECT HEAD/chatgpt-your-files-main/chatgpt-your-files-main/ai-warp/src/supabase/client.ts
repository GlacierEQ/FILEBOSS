// src/supabase/client.ts
import { createClient } from '@supabase/supabase-js';
import dotenv from 'dotenv';

// Load environment variables
dotenv.config();

const supabaseUrl = process.env.SUPABASE_URL || 'http://localhost:54321';
const supabaseKey = process.env.SUPABASE_KEY || '';

if (!supabaseKey) {
  console.warn('Warning: SUPABASE_KEY is not set in the environment variables.');
}

/**
 * Supabase client for database operations
 */
export const supabase = createClient(supabaseUrl, supabaseKey);

/**
 * Insert a new page with content and embedding
 * @param url The URL of the page
 * @param content The HTML content of the page
 * @param textContent The extracted text content
 * @param embedding The vector embedding of the text content
 * @returns The result of the insertion
 */
export async function insertPage(
  url: string,
  content: string,
  textContent: string,
  embedding: number[]
) {
  try {
    const { data, error } = await supabase
      .from('pages')
      .insert([
        {
          url,
          html_content: content,
          text_content: textContent,
          embedding,
          created_at: new Date().toISOString(),
        },
      ])
      .select();

    if (error) {
      throw error;
    }

    return data;
  } catch (error) {
    console.error('Error inserting page into Supabase:', error);
    throw error;
  }
}

/**
 * Find similar pages based on embedding vector similarity
 * @param embedding The vector embedding to compare against
 * @param limit The maximum number of results to return
 * @returns Similar pages in descending order of similarity
 */
export async function findSimilarPages(embedding: number[], limit: number = 5) {
  try {
    // Using pgvector's <-> operator for cosine distance
    const { data, error } = await supabase
      .from('pages')
      .select('*')
      .order(mbedding <-> ''::vector, { ascending: true })
      .limit(limit);

    if (error) {
      throw error;
    }

    return data;
  } catch (error) {
    console.error('Error finding similar pages in Supabase:', error);
    throw error;
  }
}

export default supabase;
