/**
 * Error Recovery System for Sorting Hat
 * Provides enhanced error handling, logging, and recovery mechanisms
 */
const fs = require('fs');
const path = require('path');
const { exec } = require('child_process');

class ErrorRecovery {
  constructor(config = {}) {
    this.config = {
      programDir: 'C:/SORTING HAT/BRAINS',
      maxRetries: 3,
      retryDelays: [1000, 5000, 15000], // ms
      failureThreshold: 10, // Max failures before auto-restart
      criticalServices: ['fileOrganizer', 'apiServer'],
      errorLogPath: path.join('C:/SORTING HAT/BRAINS', 'logs', 'errors'),
      ...config
    };
    
    // Initialize state
    this.failureCount = {};
    this.errorLog = [];
    
    // Create error log directory
    if (!fs.existsSync(this.config.errorLogPath)) {
      fs.mkdirSync(this.config.errorLogPath, { recursive: true });
    }
  }
  
  /**
   * Execute an operation with automatic retries
   * @param {Function} operation - Function to execute
   * @param {string} operationName - Name for logging
   * @param {Object} context - Context information for debugging
   * @returns {Promise} - Result of the operation
   */
  async withRetry(operation, operationName, context = {}) {
    let lastError = null;
    
    for (let attempt = 0; attempt < this.config.maxRetries; attempt++) {
      try {
        const result = await operation();
        
        // If we get here, operation succeeded
        if (attempt > 0) {
          // Log recovery success
          this.logRecovery(operationName, context, attempt);
        }
        
        return result;
      } catch (error) {
        lastError = error;
        this.recordFailure(operationName);
        this.logError(operationName, error, context, attempt);
        
        // Check if we should retry
        if (attempt < this.config.maxRetries - 1) {
          // Wait before retrying
          const delay = this.config.retryDelays[attempt] || 1000;
          await new Promise(resolve => setTimeout(resolve, delay));
        }
      }
    }
    
    // If we get here, all attempts failed
    throw new Error(`Operation '${operationName}' failed after ${this.config.maxRetries} attempts: ${lastError.message}`);
  }
  
  /**
   * Record a failure and check if recovery is needed
   * @param {string} serviceName - Name of the failing service
   */
  recordFailure(serviceName) {
    if (!this.failureCount[serviceName]) {
      this.failureCount[serviceName] = 0;
    }
    
    this.failureCount[serviceName]++;
    
    // Check if service needs recovery
    if (this.failureCount[serviceName] >= this.config.failureThreshold) {
      console.error(`Service ${serviceName} has reached failure threshold (${this.failureCount[serviceName]} failures)`);
      
      if (this.config.criticalServices.includes(serviceName)) {
        this.initiateRecovery(serviceName);
      }
    }
  }
  
  /**
   * Reset failure count for a service
   * @param {string} serviceName - Name of the service
   */
  resetFailures(serviceName) {
    this.failureCount[serviceName] = 0;
  }
  
  /**
   * Log error details to file
   * @param {string} operation - Operation that failed 
   * @param {Error} error - The error that occurred
   * @param {Object} context - Additional context
   * @param {number} attempt - Which retry attempt
   */
  logError(operation, error, context, attempt) {
    try {
      const timestamp = new Date().toISOString();
      const errorEntry = {
        timestamp,
        operation,
        attempt: attempt + 1,
        error: {
          message: error.message,
          stack: error.stack,
          code: error.code
        },
        context
      };
      
      // Add to in-memory log (limited size)
      this.errorLog.unshift(errorEntry);
      if (this.errorLog.length > 100) {
        this.errorLog.pop();
      }
      
      // Write to daily error log file
      const today = new Date().toISOString().split('T')[0];
      const logFile = path.join(this.config.errorLogPath, `errors-${today}.log`);
      
      fs.appendFileSync(logFile, JSON.stringify(errorEntry) + '\n');
      
      console.error(`Error in operation '${operation}' (attempt ${attempt + 1}/${this.config.maxRetries}): ${error.message}`);
    } catch (logError) {
      // Don't let logging errors cause more problems
      console.error(`Failed to log error: ${logError.message}`);
    }
  }
  
  /**
   * Log successful recovery
   * @param {string} operation - Operation that recovered
   * @param {Object} context - Additional context
   * @param {number} attempt - Which retry succeeded
   */
  logRecovery(operation, context, attempt) {
    try {
      const timestamp = new Date().toISOString();
      const recoveryEntry = {
        timestamp,
        operation,
        recoveredOnAttempt: attempt + 1,
        context
      };
      
      // Write to recovery log
      const recoveryLogFile = path.join(this.config.errorLogPath, 'recovery.log');
      fs.appendFileSync(recoveryLogFile, JSON.stringify(recoveryEntry) + '\n');
      
      console.log(`Successfully recovered operation '${operation}' on attempt ${attempt + 1}`);
    } catch (logError) {
      console.error(`Failed to log recovery: ${logError.message}`);
    }
  }
  
  /**
   * Initiate recovery for a critical service
   * @param {string} serviceName - Service to recover
   */
  initiateRecovery(serviceName) {
    console.log(`Initiating recovery for ${serviceName}...`);
    
    try {
      // Reset failure count first to avoid loops
      this.resetFailures(serviceName);
      
      // Use the appropriate restart script
      let restartScript;
      
      switch (serviceName) {
        case 'apiServer':
          restartScript = path.join(this.config.programDir, 'restart_api_server.bat');
          break;
        case 'fileOrganizer':
          restartScript = path.join(this.config.programDir, 'restart_file_organizer.bat');
          break;
        default:
          restartScript = path.join(this.config.programDir, 'fix_network_errors.bat');
      }
      
      if (fs.existsSync(restartScript)) {
        console.log(`Executing restart script: ${restartScript}`);
        exec(`"${restartScript}"`, (error, stdout, stderr) => {
          if (error) {
            console.error(`Error during restart: ${error.message}`);
            console.error(stderr);
          } else {
            console.log(`Service ${serviceName} restarted successfully`);
            console.log(stdout);
          }
        });
      } else {
        console.error(`Restart script not found: ${restartScript}`);
      }
    } catch (error) {
      console.error(`Recovery failed for ${serviceName}: ${error.message}`);
    }
  }
  
  /**
   * Create a restart script for a specific component
   * @param {string} serviceName - Service name
   * @param {string} startCommand - Command to start the service
   */
  createRestartScript(serviceName, startCommand) {
    const scriptContent = `@echo off
echo Restarting ${serviceName}...
taskkill /F /FI "WINDOWTITLE eq ${serviceName}*" /T >nul 2>&1
timeout /t 2 /nobreak >nul
cd /d "%~dp0"
start "${serviceName}" cmd /c "${startCommand}"
echo ${serviceName} restart initiated
`;

    const scriptPath = path.join(this.config.programDir, `restart_${serviceName.toLowerCase()}.bat`);
    fs.writeFileSync(scriptPath, scriptContent);
    
    return scriptPath;
  }
  
  /**
   * Get recent errors for a service
   * @param {string} serviceName - Service to get errors for (optional)
   * @param {number} limit - Maximum number of errors to return
   * @returns {Array} - Recent errors
   */
  getRecentErrors(serviceName, limit = 10) {
    if (serviceName) {
      return this.errorLog
        .filter(entry => entry.operation === serviceName)
        .slice(0, limit);
    } else {
      return this.errorLog.slice(0, limit);
    }
  }
}

module.exports = ErrorRecovery;
