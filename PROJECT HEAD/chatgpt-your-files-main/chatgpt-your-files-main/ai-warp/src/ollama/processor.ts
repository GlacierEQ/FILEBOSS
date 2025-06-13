// src/ollama/processor.ts
import fetch from 'node-fetch';

const OLLAMA_HOST = process.env.OLLAMA_HOST || 'http://localhost:11434';

/**
 * Client for interacting with Ollama API
 */
export class OllamaClient {
  private baseUrl: string;

  constructor(baseUrl: string = OLLAMA_HOST) {
    this.baseUrl = baseUrl;
  }

  /**
   * Generate text using an Ollama model
   * @param model The model name to use
   * @param prompt The prompt to send to the model
   * @returns The generated text response
   */
  async generate({ model, prompt }: { model: string; prompt: string }): Promise<{ text: string }> {
    try {
      const response = await fetch(`${this.baseUrl}/api/generate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          model,
          prompt,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json() as { response: string };
      return { text: data.response };
    } catch (error) {
      console.error('Error generating text with Ollama:', error);
      throw error;
    }
  }

  /**
   * Generate embeddings for a text using an Ollama embedding model
   * @param model The embedding model to use
   * @param prompt The text to generate embeddings for
   * @returns The embedding vector
   */
  async embeddings({ model, prompt }: { model: string; prompt: string }): Promise<number[]> {
    try {
      const response = await fetch(`${this.baseUrl}/api/embeddings`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          model,
          prompt,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json() as { embedding: number[] };
      return data.embedding;
    } catch (error) {
      console.error('Error generating embeddings with Ollama:', error);
      throw error;
    }
  }

  /**
   * Summarize content from a URL
   * @param url The URL to fetch and summarize
   * @param model The model to use for summarization
   * @returns The summarized content
   */
  async summarizeContent(url: string, model: string = 'llama2'): Promise<string> {
    try {
      // First, fetch the content from the URL
      const urlResponse = await fetch(url);
      const html = await urlResponse.text();
      
      // Extract text content from HTML (basic implementation)
      const textContent = this.extractTextFromHtml(html);
      
      // Generate summary using the model
      const prompt = `Summarize the following content concisely:\n\n${textContent}`;
      const response = await this.generate({ model, prompt });
      
      return response.text;
    } catch (error) {
      console.error('Error summarizing content:', error);
      throw error;
    }
  }

  /**
   * Basic function to extract text from HTML
   * @param html The HTML string to process
   * @returns Extracted text content
   */
  private extractTextFromHtml(html: string): string {
    // This is a very basic implementation
    // In a production environment, use a proper HTML parser
    return html
      .replace(/<[^>]*>/g, ' ') // Remove HTML tags
      .replace(/\s+/g, ' ')     // Replace multiple spaces with single space
      .trim();
  }
}

// Export a default instance
export const ollama = new OllamaClient();

export default ollama;
