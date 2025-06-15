const axios = require('axios');
const fs = require('fs');
const path = require('path');

class ApiService {
  constructor(baseUrl, cachePath) {
    this.baseUrl = baseUrl || 'http://localhost:3000/api';
    this.cachePath = cachePath || path.join(__dirname, 'cache');
    this.retryDelays = [1000, 2000, 5000, 10000, 30000]; // Exponential backoff in ms
    
    // Create cache directory if it doesn't exist
    if (!fs.existsSync(this.cachePath)) {
      fs.mkdirSync(this.cachePath, { recursive: true });
    }
  }

  async fetchWithRetry(endpoint, options = {}, retryCount = 0) {
    try {
      const response = await axios({
        url: `${this.baseUrl}/${endpoint}`,
        method: options.method || 'GET',
        data: options.data,
        headers: options.headers,
        timeout: options.timeout || 10000
      });
      
      // Cache successful responses
      this.cacheResponse(endpoint, response.data);
      
      return response.data;
    } catch (error) {
      console.error(`Error fetching ${endpoint}: ${error.message}`);
      
      // Check if we should retry
      if (retryCount < this.retryDelays.length && this.isRetryableError(error)) {
        const delay = this.retryDelays[retryCount];
        console.log(`Retrying in ${delay/1000} seconds... (Attempt ${retryCount + 1})`);
        
        await new Promise(resolve => setTimeout(resolve, delay));
        return this.fetchWithRetry(endpoint, options, retryCount + 1);
      }
      
      // Return cached data if available
      const cachedData = this.getFromCache(endpoint);
      if (cachedData) {
        console.log(`Returning cached data for ${endpoint}`);
        return { 
          data: cachedData, 
          fromCache: true,
          timestamp: this.getCacheTimestamp(endpoint)
        };
      }
      
      throw error;
    }
  }
  
  isRetryableError(error) {
    // Network errors and server errors (5xx) are retryable
    return !error.response || (error.response && error.response.status >= 500);
  }
  
  getCachePath(endpoint) {
    return path.join(this.cachePath, `${endpoint.replace(/\//g, '_')}.json`);
  }
  
  cacheResponse(endpoint, data) {
    try {
      const cachePath = this.getCachePath(endpoint);
      fs.writeFileSync(cachePath, JSON.stringify({
        data,
        timestamp: new Date().toISOString()
      }));
    } catch (error) {
      console.error(`Failed to cache response: ${error.message}`);
    }
  }
  
  getFromCache(endpoint) {
    try {
      const cachePath = this.getCachePath(endpoint);
      if (fs.existsSync(cachePath)) {
        const cacheData = JSON.parse(fs.readFileSync(cachePath, 'utf8'));
        return cacheData.data;
      }
    } catch (error) {
      console.error(`Failed to read from cache: ${error.message}`);
    }
    return null;
  }
  
  getCacheTimestamp(endpoint) {
    try {
      const cachePath = this.getCachePath(endpoint);
      if (fs.existsSync(cachePath)) {
        const cacheData = JSON.parse(fs.readFileSync(cachePath, 'utf8'));
        return cacheData.timestamp;
      }
    } catch (error) {
      console.error(`Failed to get cache timestamp: ${error.message}`);
    }
    return null;
  }
  
  clearCache() {
    try {
      const files = fs.readdirSync(this.cachePath);
      for (const file of files) {
        fs.unlinkSync(path.join(this.cachePath, file));
      }
      console.log('Cache cleared successfully');
    } catch (error) {
      console.error(`Failed to clear cache: ${error.message}`);
    }
  }
  
  // Specific API methods
  async getEvolutionReport() {
    return this.fetchWithRetry('evolution/report');
  }
  
  async getPatterns() {
    return this.fetchWithRetry('patterns');
  }
  
  async updatePattern(pattern) {
    return this.fetchWithRetry('patterns/update', {
      method: 'POST',
      data: pattern
    });
  }
}

module.exports = ApiService;
