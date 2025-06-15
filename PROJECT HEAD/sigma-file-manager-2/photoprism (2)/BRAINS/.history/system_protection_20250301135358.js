/**
 * System Protection Module for Sorting Hat
 * 
 * This module provides protection against:
 * 1. System file access/modification
 * 2. Program file corruption
 * 3. Memory leaks and OOM errors
 * 4. Process crashes and failures
 */
const fs = require('fs');
const path = require('path');
const os = require('os');
const { exec, spawn } = require('child_process');
const crypto = require('crypto');

class SystemProtection {
  constructor(config = {}) {
    // Default configuration
    this.config = {
      programDir: 'C:/SORTING HAT/BRAINS',
      backupDir: 'C:/SORTING HAT/BRAINS/backups',
      memoryThreshold: 80, // percentage of total RAM to trigger warning
      memoryLimit: 90,     // percentage of total RAM to trigger action
      checkInterval: 60000, // memory check interval in ms
      systemFiles: [
        'C:/Windows',
        'C:/Program Files',
        'C:/Program Files (x86)',
        'C:/ProgramData',
        'C:/System Volume Information'
      ],
      criticalProgramFiles: [
        'service.js',
        'file_organizer.js',
        'api_service.js',
        'dashboard_controller.js',
        'network_monitor.js',
        'system_protection.js',
        'config.js',
        'package.json'
      ],
      watchdogInterval: 120000, // watchdog check interval in ms
      ...config
    };
    
    // Initialize state
    this.memoryCheckInterval = null;
    this.watchdogInterval = null;
    this.processInfo = {};
    this.criticalFileHashes = {};
    
    // Create backup directory if it doesn't exist
    if (!fs.existsSync(this.config.backupDir)) {
      fs.mkdirSync(this.config.backupDir, { recursive: true });
      console.log(`Created backup directory at ${this.config.backupDir}`);
    }
  }
  
  /**
   * Calculate file hash for integrity checks
   */
  calculateFileHash(filePath) {
    try {
      const fileBuffer = fs.readFileSync(filePath);
      const hashSum = crypto.createHash('sha256');
      hashSum.update(fileBuffer);
      return hashSum.digest('hex');
    } catch (error) {
      console.error(`Error calculating hash for ${filePath}: ${error.message}`);
      return null;
    }
  }
  
  /**
   * Backup critical program files
   */
  backupCriticalFiles() {
    console.log('Backing up critical program files...');
    
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const backupFolder = path.join(this.config.backupDir, `backup-${timestamp}`);
    
    try {
      fs.mkdirSync(backupFolder, { recursive: true });
      
      for (const file of this.config.criticalProgramFiles) {
        const sourcePath = path.join(this.config.programDir, file);
        const destPath = path.join(backupFolder, file);
        
        if (fs.existsSync(sourcePath)) {
          fs.copyFileSync(sourcePath, destPath);
          
          // Store file hash for integrity checks
          this.criticalFileHashes[file] = this.calculateFileHash(sourcePath);
        }
      }
      
      console.log(`Backup completed to ${backupFolder}`);
      
      // Clean up old backups (keep only 5 most recent)
      this.cleanupOldBackups();
      
      return backupFolder;
    } catch (error) {
      console.error(`Backup failed: ${error.message}`);
      return null;
    }
  }
  
  /**
   * Clean up old backups, keeping only the most recent ones
   */
  cleanupOldBackups(maxBackups = 5) {
    try {
      const backups = fs.readdirSync(this.config.backupDir)
        .filter(folder => folder.startsWith('backup-'))
        .map(folder => ({
          name: folder,
          path: path.join(this.config.backupDir, folder),
          time: fs.statSync(path.join(this.config.backupDir, folder)).mtime.getTime()
        }))
        .sort((a, b) => b.time - a.time); // Sort newest first
      
      // Delete all but the newest maxBackups
      for (const backup of backups.slice(maxBackups)) {
        this.deleteFolder(backup.path);
        console.log(`Removed old backup: ${backup.name}`);
      }
    } catch (error) {
      console.error(`Error cleaning up old backups: ${error.message}`);
    }
  }
  
  /**
   * Recursively delete a folder
   */
  deleteFolder(folderPath) {
    if (fs.existsSync(folderPath)) {
      fs.readdirSync(folderPath).forEach(file => {
        const curPath = path.join(folderPath, file);
        if (fs.lstatSync(curPath).isDirectory()) {
          this.deleteFolder(curPath);
        } else {
          fs.unlinkSync(curPath);
        }
      });
      fs.rmdirSync(folderPath);
    }
  }
  
  /**
   * Check if a path is a protected system file/directory
   */
  isSystemFile(filePath) {
    const normalizedPath = filePath.replace(/\\/g, '/');
    return this.config.systemFiles.some(sysPath => 
      normalizedPath.toLowerCase().startsWith(sysPath.toLowerCase())
    );
  }
  
  /**
   * Check if a path is a protected program file
   */
  isProgramFile(filePath) {
    const normalizedPath = filePath.replace(/\\/g, '/');
    const programDirNormalized = this.config.programDir.replace(/\\/g, '/');
    
    return normalizedPath.toLowerCase().startsWith(programDirNormalized.toLowerCase());
  }
  
  /**
   * Safe file operation wrapper - prevents operations on system/program files
   */
  safeFileOperation(operation, filePath, ...args) {
    if (this.isSystemFile(filePath)) {
      console.error(`BLOCKED: Attempted operation on system file: ${filePath}`);
      return false;
    }
    
    if (this.isProgramFile(filePath)) {
      console.error(`BLOCKED: Attempted operation on program file: ${filePath}`);
      return false;
    }
    
    try {
      return operation(filePath, ...args);
    } catch (error) {
      console.error(`File operation error: ${error.message}`);
      return false;
    }
  }
  
  /**
   * Check memory usage and take action if over threshold
   */
  checkMemoryUsage() {
    try {
      const totalMemory = os.totalmem();
      const freeMemory = os.freemem();
      const usedMemory = totalMemory - freeMemory;
      const memoryUsagePercent = (usedMemory / totalMemory) * 100;
      
      if (memoryUsagePercent > this.config.memoryLimit) {
        console.error(`CRITICAL: Memory usage at ${memoryUsagePercent.toFixed(1)}% - Above limit of ${this.config.memoryLimit}%`);
        this.handleExcessiveMemoryUsage();
      } else if (memoryUsagePercent > this.config.memoryThreshold) {
        console.warn(`WARNING: Memory usage at ${memoryUsagePercent.toFixed(1)}% - Above threshold of ${this.config.memoryThreshold}%`);
        this.collectGarbage();
      } else {
        // Normal operation, memory usage is fine
      }
    } catch (error) {
      console.error(`Error checking memory: ${error.message}`);
    }
  }
  
  /**
   * Attempt to collect garbage when memory usage is high
   */
  collectGarbage() {
    if (global.gc) {
      try {
        global.gc();
        console.log('Manual garbage collection executed');
      } catch (error) {
        console.error(`Error during manual garbage collection: ${error.message}`);
      }
    } else {
      console.log('Manual garbage collection not available. Run with --expose-gc flag to enable.');
    }
  }
  
  /**
   * Handle excessive memory usage by restarting services
   */
  handleExcessiveMemoryUsage() {
    console.log('Taking action to reduce memory usage...');
    
    // Collect garbage first
    this.collectGarbage();
    
    // Check memory again after garbage collection
    const totalMemory = os.totalmem();
    const freeMemory = os.freemem();
    const usedMemory = totalMemory - freeMemory;
    const memoryUsagePercent = (usedMemory / totalMemory) * 100;
    
    if (memoryUsagePercent > this.config.memoryLimit) {
      console.log('Memory usage still excessive, restarting services...');
      this.restartService();
    } else {
      console.log(`Memory usage reduced to ${memoryUsagePercent.toFixed(1)}% after garbage collection`);
    }
  }
  
  /**
   * Restart a service
   */
  restartService(service = 'all') {
    console.log(`Restarting service: ${service}`);
    
    // Backup critical files before restart
    this.backupCriticalFiles();
    
    if (service === 'all' || service === 'sorting') {
      // Execute the restart script
      exec('restart_api_server.bat', (error) => {
        if (error) {
          console.error(`Error restarting service: ${error.message}`);
        }
      });
    }
  }
  
  /**
   * Check integrity of critical program files
   */
  checkFileIntegrity() {
    console.log('Checking file integrity...');
    const corruptedFiles = [];
    
    for (const file of this.config.criticalProgramFiles) {
      const filePath = path.join(this.config.programDir, file);
      
      if (!fs.existsSync(filePath)) {
        console.error(`Critical file missing: ${file}`);
        corruptedFiles.push(file);
        continue;
      }
      
      // Skip hash check if we don't have a stored hash
      if (!this.criticalFileHashes[file]) {
        continue;
      }
      
      // Check file hash
      const currentHash = this.calculateFileHash(filePath);
      if (currentHash !== this.criticalFileHashes[file]) {
        console.error(`File integrity check failed for: ${file}`);
        corruptedFiles.push(file);
      }
    }
    
    if (corruptedFiles.length > 0) {
      console.error(`Found ${corruptedFiles.length} corrupted files. Attempting to restore...`);
      this.restoreFromBackup(corruptedFiles);
    } else {
      console.log('All critical files passed integrity check');
    }
  }
  
  /**
   * Restore corrupted files from most recent backup
   */
  restoreFromBackup(corruptedFiles) {
    try {
      // Find most recent backup
      const backups = fs.readdirSync(this.config.backupDir)
        .filter(folder => folder.startsWith('backup-'))
        .map(folder => ({
          name: folder,
          path: path.join(this.config.backupDir, folder),
          time: fs.statSync(path.join(this.config.backupDir, folder)).mtime.getTime()
        }))
        .sort((a, b) => b.time - a.time); // Sort newest first
      
      if (backups.length === 0) {
        console.error('No backups found for restoration');
        return;
      }
      
      const latestBackup = backups[0];
      console.log(`Restoring from backup: ${latestBackup.name}`);
      
      for (const file of corruptedFiles) {
        const backupFilePath = path.join(latestBackup.path, file);
        const targetFilePath = path.join(this.config.programDir, file);
        
        if (fs.existsSync(backupFilePath)) {
          fs.copyFileSync(backupFilePath, targetFilePath);
          console.log(`Restored file: ${file}`);
        } else {
          console.error(`Cannot restore ${file}: not found in backup`);
        }
      }
    } catch (error) {
      console.error(`Error during file restoration: ${error.message}`);
    }
  }
  
  /**
   * Start monitoring process health
   */
  startProcessMonitoring() {
    // Get the current process info
    this.processInfo.pid = process.pid;
    this.processInfo.memoryUsage = process.memoryUsage();
    
    // Start memory check interval
    this.memoryCheckInterval = setInterval(() => {
      this.checkMemoryUsage();
    }, this.config.checkInterval);
    
    // Start watchdog interval
    this.watchdogInterval = setInterval(() => {
      this.checkFileIntegrity();
    }, this.config.watchdogInterval);
    
    // Set up process error handlers
    process.on('uncaughtException', (error) => {
      console.error(`Uncaught exception: ${error.message}`);
      console.error(error.stack);
      
      // Log the error and attempt recovery
      this.handleProcessError('uncaughtException', error);
    });
    
    process.on('unhandledRejection', (reason, promise) => {
      console.error('Unhandled promise rejection:', reason);
      
      // Log the error and attempt recovery
      this.handleProcessError('unhandledRejection', reason);
    });
    
    console.log('Process monitoring started');
  }
  
  /**
   * Stop monitoring process health
   */
  stopProcessMonitoring() {
    if (this.memoryCheckInterval) {
      clearInterval(this.memoryCheckInterval);
      this.memoryCheckInterval = null;
    }
    
    if (this.watchdogInterval) {
      clearInterval(this.watchdogInterval);
      this.watchdogInterval = null;
    }
    
    console.log('Process monitoring stopped');
  }
  
  /**
   * Handle process errors
   */
  handleProcessError(type, error) {
    // Create an error report
    const errorReport = {
      timestamp: new Date().toISOString(),
      type: type,
      message: error.message || String(error),
      stack: error.stack,
      memoryUsage: process.memoryUsage()
    };
    
    // Save error report
    try {
      const errorLogDir = path.join(this.config.programDir, 'logs', 'errors');
      if (!fs.existsSync(errorLogDir)) {
        fs.mkdirSync(errorLogDir, { recursive: true });
      }
      
      const errorLogFile = path.join(errorLogDir, `error-${Date.now()}.json`);
      fs.writeFileSync(errorLogFile, JSON.stringify(errorReport, null, 2));
      console.log(`Error report saved to ${errorLogFile}`);
    } catch (logError) {
      console.error(`Failed to save error report: ${logError.message}`);
    }
    
    // For critical errors, restart the service
    const criticalErrorTypes = ['uncaughtException'];
    if (criticalErrorTypes.includes(type)) {
      console.log('Critical error detected, restarting service...');
      this.restartService();
    }
  }
  
  /**
   * Initialize system protection
   */
  initialize() {
    console.log('Initializing system protection...');
    
    // Backup critical files
    this.backupCriticalFiles();
    
    // Start monitoring
    this.startProcessMonitoring();
    
    return this;
  }
}

module.exports = SystemProtection;

// Example usage:
// const protection = new SystemProtection().initialize();
