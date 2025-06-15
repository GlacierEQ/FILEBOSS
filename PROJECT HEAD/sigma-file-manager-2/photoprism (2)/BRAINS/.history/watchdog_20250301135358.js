/**
 * Watchdog Process for Sorting Hat
 * 
 * This watchdog monitors the main services and restarts them if they crash
 */
const fs = require('fs');
const path = require('path');
const { exec, spawn } = require('child_process');
const SystemProtection = require('./system_protection');

// Constants
const CHECK_INTERVAL = 30000; // Check every 30 seconds
const MAX_FAILURES = 5;       // Maximum failures before giving up
const RECOVERY_TIME = 300000; // Time to wait after max failures (5 minutes)

class Watchdog {
  constructor(config = {}) {
    this.config = {
      programDir: 'C:/SORTING HAT/BRAINS',
      servicesMap: {
        fileOrganizer: {
          processName: 'node.exe',
          windowTitle: 'Sorting Hat - File Monitor',
          startScript: 'node file_organizer.js',
          importance: 'critical'
        },
        apiServer: {
          processName: 'node.exe',
          windowTitle: 'Sorting Hat API Server',
          startScript: 'node service.js',
          importance: 'critical'
        }
      },
      ...config
    };
    
    this.failures = {};
    this.intervals = {};
    this.systemProtection = new SystemProtection().initialize();
    this.lastRecoveryAttempt = {};
  }
  
  /**
   * Start watchdog monitoring
   */
  start() {
    console.log('Starting Sorting Hat Watchdog...');
    
    // Initialize failure counters
    Object.keys(this.config.servicesMap).forEach(service => {
      this.failures[service] = 0;
      this.lastRecoveryAttempt[service] = 0;
    });
    
    // Set up monitoring for each service
    Object.entries(this.config.servicesMap).forEach(([serviceName, serviceConfig]) => {
      this.intervals[serviceName] = setInterval(() => {
        this.checkService(serviceName, serviceConfig);
      }, CHECK_INTERVAL);
    });
    
    console.log('Watchdog started - monitoring all services');
  }
  
  /**
   * Stop watchdog monitoring
   */
  stop() {
    console.log('Stopping watchdog...');
    
    // Clear all monitoring intervals
    Object.keys(this.intervals).forEach(service => {
      clearInterval(this.intervals[service]);
    });
    
    this.intervals = {};
    this.systemProtection.stopProcessMonitoring();
    
    console.log('Watchdog stopped');
  }
  
  /**
   * Check if a service is running
   */
  checkService(serviceName, serviceConfig) {
    const cmd = process.platform === 'win32'
      ? `tasklist /FI "WINDOWTITLE eq ${serviceConfig.windowTitle}*" /FO CSV /NH`
      : `ps aux | grep "${serviceConfig.windowTitle}" | grep -v grep`;
    
    exec(cmd, (error, stdout) => {
      const isRunning = !error && stdout.trim() !== '';
      
      if (!isRunning) {
        console.log(`Service ${serviceName} is not running!`);
        this.handleServiceFailure(serviceName, serviceConfig);
      } else {
        // Reset failure counter if service is running
        if (this.failures[serviceName] > 0) {
          console.log(`Service ${serviceName} is now running properly. Resetting failure counter.`);
          this.failures[serviceName] = 0;
        }
      }
    });
  }
  
  /**
   * Handle service failure
   */
  handleServiceFailure(serviceName, serviceConfig) {
    this.failures[serviceName]++;
    console.log(`${serviceName} failure count: ${this.failures[serviceName]}`);
    
    // Check if we've reached the max failures and are within recovery time
    const now = Date.now();
    if (this.failures[serviceName] >= MAX_FAILURES) {
      if (now - this.lastRecoveryAttempt[serviceName] < RECOVERY_TIME) {
        console.log(`Maximum failures reached for ${serviceName}. Waiting for recovery time...`);
        return;
      } else {
        // Reset failure counter after recovery time
        this.failures[serviceName] = 0;
      }
    }
    
    // Try to restart the service
    console.log(`Attempting to restart ${serviceName}...`);
    this.lastRecoveryAttempt[serviceName] = now;
    
    try {
      if (serviceConfig.importance === 'critical') {
        // For critical services, backup files first
        this.systemProtection.backupCriticalFiles();
      }
      
      // Kill any zombie processes first
      this.killZombieProcesses(serviceConfig.processName, serviceConfig.windowTitle);
      
      // Start the service
      const startCmd = serviceConfig.startScript;
      
      exec(`cd "${this.config.programDir}" && start "${serviceConfig.windowTitle}" cmd /c ${startCmd}`, (error) => {
        if (error) {
          console.error(`Failed to restart ${serviceName}: ${error.message}`);
        } else {
          console.log(`${serviceName} restart initiated`);
        }
      });
    } catch (error) {
      console.error(`Error during ${serviceName} restart: ${error.message}`);
    }
  }
  
  /**
   * Kill any zombie processes of a service
   */
  killZombieProcesses(processName, windowTitle) {
    const killCmd = process.platform === 'win32'
      ? `taskkill /F /FI "WINDOWTITLE eq ${windowTitle}*" /T`
      : `pkill -f "${windowTitle}"`;
    
    exec(killCmd, (error) => {
      if (error && error.code !== 128) { // 128 means no processes found, which is fine
        console.log(`Note: No zombie processes found for ${windowTitle} (this is normal if it crashed completely)`);
      }
    });
  }
  
  /**
   * Write health status report
   */
  writeHealthReport() {
    try {
      const report = {
        timestamp: new Date().toISOString(),
        services: {}
      };
      
      // Get status for each service
      Object.entries(this.config.servicesMap).forEach(([serviceName, serviceConfig]) => {
        report.services[serviceName] = {
          failures: this.failures[serviceName],
          lastRecovery: this.lastRecoveryAttempt[serviceName] ? new Date(this.lastRecoveryAttempt[serviceName]).toISOString() : null
        };
      });
      
      // Add system info
      report.system = {
        memory: {
          total: Math.round(require('os').totalmem() / (1024 * 1024)) + ' MB',
          free: Math.round(require('os').freemem() / (1024 * 1024)) + ' MB',
          usage: Math.round((1 - require('os').freemem() / require('os').totalmem()) * 100) + '%'
        },
        uptime: Math.round(require('os').uptime() / 60) + ' minutes'
      };
      
      // Write report to file
      const reportDir = path.join(this.config.programDir, 'logs');
      if (!fs.existsSync(reportDir)) {
        fs.mkdirSync(reportDir, { recursive: true });
      }
      
      const reportFile = path.join(reportDir, 'watchdog_health.json');
      fs.writeFileSync(reportFile, JSON.stringify(report, null, 2));
    } catch (error) {
      console.error(`Failed to write health report: ${error.message}`);
    }
  }
}

// Create and start the watchdog
const watchdog = new Watchdog();
watchdog.start();

// Write health report every hour
setInterval(() => {
  watchdog.writeHealthReport();
}, 60 * 60 * 1000);

// Handle process termination
process.on('SIGINT', () => {
  console.log('Watchdog terminating...');
  watchdog.stop();
  process.exit(0);
});

process.on('uncaughtException', (error) => {
  console.error(`Watchdog uncaught exception: ${error.message}`);
  console.error(error.stack);
  
  // Write final health report
  watchdog.writeHealthReport();
  
  // Try to restart main services before exiting
  Object.entries(watchdog.config.servicesMap)
    .filter(([_, config]) => config.importance === 'critical')
    .forEach(([name, config]) => {
      watchdog.handleServiceFailure(name, config);
    });
  
  // Exit after a delay to allow restart attempts to complete
  setTimeout(() => {
    process.exit(1);
  }, 5000);
});
