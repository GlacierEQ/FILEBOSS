// tests/ollama/processor.test.ts
import { OllamaClient } from '../../src/ollama/processor';

// Mock fetch
global.fetch = jest.fn();

describe('OllamaClient', () => {
  let ollamaClient: OllamaClient;
  
  beforeEach(() => {
    ollamaClient = new OllamaClient('http://localhost:11434');
    (global.fetch as jest.Mock).mockClear();
  });

  describe('generate', () => {
    it('should call the Ollama API correctly', async () => {
      // Mock successful response
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ response: 'Generated text response' }),
      });

      const result = await ollamaClient.generate({
        model: 'llama2',
        prompt: 'Test prompt',
      });

      // Check fetch was called correctly
      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:11434/api/generate',
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            model: 'llama2',
            prompt: 'Test prompt',
          }),
        }
      );

      // Check response
      expect(result).toEqual({ text: 'Generated text response' });
    });

    it('should handle API errors', async () => {
      // Mock error response
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        status: 500,
      });

      await expect(
        ollamaClient.generate({
          model: 'llama2',
          prompt: 'Test prompt',
        })
      ).rejects.toThrow('HTTP error! status: 500');
    });
  });

  describe('embeddings', () => {
    it('should call the Ollama API correctly', async () => {
      // Mock successful response
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ embedding: [0.1, 0.2, 0.3] }),
      });

      const result = await ollamaClient.embeddings({
        model: 'nomic-embed-text',
        prompt: 'Test text',
      });

      // Check fetch was called correctly
      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:11434/api/embeddings',
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            model: 'nomic-embed-text',
            prompt: 'Test text',
          }),
        }
      );

      // Check response
      expect(result).toEqual([0.1, 0.2, 0.3]);
    });
  });

  describe('summarizeContent', () => {
    it('should fetch URL content and summarize it', async () => {
      // Mock fetch for URL content
      (global.fetch as jest.Mock)
        .mockResolvedValueOnce({
          text: async () => '<html><body><p>Test content</p></body></html>',
        })
        // Mock fetch for generate API
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ response: 'Summarized content' }),
        });

      const result = await ollamaClient.summarizeContent('https://example.com');

      // Check second fetch (generate) was called with correct params
      expect((global.fetch as jest.Mock).mock.calls[1][0]).toBe('http://localhost:11434/api/generate');
      expect(JSON.parse((global.fetch as jest.Mock).mock.calls[1][1].body).prompt).toContain('Summarize the following content');

      // Check response
      expect(result).toBe('Summarized content');
    });
  });
});
