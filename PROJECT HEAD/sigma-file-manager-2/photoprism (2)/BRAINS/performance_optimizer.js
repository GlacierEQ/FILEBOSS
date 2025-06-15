/**
 * Performance Optimizer for Sorting Hat
 * Implements throttling, batching, and resource management
 */
const os = require('os');
const fs = require('fs');
const path = require('path');
const { promisify } = require('util');

// Promisified versions of fs functions
const fsAccess = promisify(fs.access);
const fsRename = promisify(fs.rename);
const fsReadFile = promisify(fs.readFile);
const fsStat = promisify(fs.stat);

class PerformanceOptimizer {
  constructor(config = {}) {
    this.config = {
      maxConcurrentOperations: Math.max(1, os.cpus().length - 1),
      batchSize: 20,
      fileSizeThreshold: 100 * 1024 * 1024, // 100MB
      logDirectory: path.join('C:/SORTING HAT/BRAINS', 'logs'),
      ...config
    };
    
    // Initialize state
    this.activeOperations = 0;
    this.queue = [];
    this.isProcessing = false;
    
    // Initialize metrics
    this.metrics = {
      operationsCompleted: 0,
      operationsFailed: 0,
      totalBytesProcessed: 0,
      processingTimeMs: 0,
      lastGcTime: Date.now()
    };
    
    // Ensure log directory exists
    if (!fs.existsSync(this.config.logDirectory)) {
      fs.mkdirSync(this.config.logDirectory, { recursive: true });
    }
  }
  
  /**
   * Add a file operation to the queue
   * @param {Function} operation - Async function to execute
   * @param {string} filePath - Path to the file
   * @param {Object} metadata - Additional information about the operation
   * @returns {Promise} - Resolves when operation completes
   */
  async scheduleOperation(operation, filePath, metadata = {}) {
    return new Promise((resolve, reject) => {
      this.queue.push({
        operation,
        filePath,
        metadata,
        resolve,
        reject,
        addedTime: Date.now()
      });
      
      // Start processing if not already in progress
      if (!this.isProcessing) {
        this.processQueue();
      }
    });
  }
  
  /**
   * Process operations in the queue
   */
  async processQueue() {
    if (this.isProcessing) return;
    this.isProcessing = true;
    
    try {
      while (this.queue.length > 0 && this.activeOperations < this.config.maxConcurrentOperations) {
        // Get next batch of operations
        const batchSize = Math.min(this.queue.length, this.config.batchSize);
        const batch = this.queue.splice(0, batchSize);
        
        // Sort by priority and size
        batch.sort((a, b) => {
          // First by priority if specified
          if (a.metadata.priority !== b.metadata.priority) {
            return (b.metadata.priority || 0) - (a.metadata.priority || 0);
          }
          
          // Then by waiting time (oldest first)
          return a.addedTime - b.addedTime;
        });
        
        // Process batch in parallel
        const promises = batch.map(async (item) => {
          this.activeOperations++;
          
          try {
            // Check if file exists and get stats for metrics
            let stats = null;
            try {
              await fsAccess(item.filePath, fs.constants.F_OK);
              stats = await fsStat(item.filePath);
            } catch (error) {
              // File might not exist, that's ok for some operations
            }
            
            const startTime = Date.now();
            
            // Execute the operation
            const result = await item.operation(item.filePath, item.metadata);
            
            // Update metrics
            this.metrics.operationsCompleted++;
            this.metrics.processingTimeMs += (Date.now() - startTime);
            if (stats) {
              this.metrics.totalBytesProcessed += stats.size;
            }
            
            item.resolve(result);
          } catch (error) {
            // Log the failure and reject the promise
            this.metrics.operationsFailed++;
            console.error(`Operation failed for ${item.filePath}: ${error.message}`);
            item.reject(error);
          } finally {
            this.activeOperations--;
          }
        });
        
        // Wait for the batch to complete before processing more
        await Promise.allSettled(promises);
        
        // Run garbage collection if available and warranted
        const timeSinceLastGc = Date.now() - this.metrics.lastGcTime;
        if (global.gc && timeSinceLastGc > 60000) { // 1 minute
          global.gc();
          this.metrics.lastGcTime = Date.now();
        }
      }
    } finally {
      this.isProcessing = false;
      
      // If there are still items in the queue, continue processing
      if (this.queue.length > 0) {
        setImmediate(() => this.processQueue());
      }
    }
  }
  
  /**
   * Safe rename with performance optimization
   * @param {string} source - Source path
   * @param {string} destination - Destination path
   * @returns {Promise} - Resolves when rename completes
   */
  async safeRename(source, destination) {
    return this.scheduleOperation(async (filePath, metadata) => {
      await fsRename(source, destination);
      return { source, destination };
    }, source, { operation: 'rename', destination });
  }
  
  /**
   * Safe read file with performance optimization
   * @param {string} filePath - Path to the file
   * @param {Object} options - Read options
   * @returns {Promise} - Resolves with file contents
   */
  async safeReadFile(filePath, options = {}) {
    const stats = await fsStat(filePath);
    
    // For large files, use lower priority
    const priority = stats.size > this.config.fileSizeThreshold ? 1 : 2;
    
    return this.scheduleOperation(async (path) => {
      return await fsReadFile(path, options);
    }, filePath, { operation: 'read', priority, size: stats.size });
  }
  
  /**
   * Get performance metrics
   * @returns {Object} - Current performance metrics
   */
  getMetrics() {
    return {
      ...this.metrics,
      queueLength: this.queue.length,
      activeOperations: this.activeOperations,
      timestamp: new Date().toISOString(),
      systemMemory: {
        total: os.totalmem(),
        free: os.freemem(),
        usagePercent: ((os.totalmem() - os.freemem()) / os.totalmem() * 100).toFixed(1) + '%'
      },
      cpuLoad: os.loadavg()
    };
  }
  
  /**
   * Log performance metrics
   */
  logMetrics() {
    const metrics = this.getMetrics();
    
    try {
      const logFile = path.join(this.config.logDirectory, 'performance.log');
      fs.appendFileSync(logFile, JSON.stringify(metrics) + '\n');
    } catch (error) {
      console.error(`Failed to log metrics: ${error.message}`);
    }
    
    return metrics;
  }
}

module.exports = PerformanceOptimizer;
