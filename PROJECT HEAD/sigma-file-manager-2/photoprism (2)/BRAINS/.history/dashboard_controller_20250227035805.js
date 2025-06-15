const ApiService = require('./api_service');
const NetworkMonitor = require('./network_monitor');
const fs = require('fs');
const path = require('path');

class DashboardController {
  constructor(config = {}) {
    this.apiService = new ApiService(
      config.apiUrl || 'http://localhost:3000/api',
      config.cachePath || path.join(__dirname, 'cache')
    );
    
    this.networkMonitor = new NetworkMonitor(config.networkCheckInterval || 30000);
    this.isOfflineMode = false;
    this.autoRefreshInterval = null;
    this.refreshRate = config.refreshRate || 60000; // 1 minute
    this.eventListeners = {};
    
    // Set up network monitoring
    this.networkMonitor.on('online', () => this.handleOnline());
    this.networkMonitor.on('offline', () => this.handleOffline());
    
    // Start network monitoring
    this.networkMonitor.start();
  }
  
  async initialize() {
    console.log('Evolution dashboard initializing...');
    
    // Log initialization
    this.logMessage('Evolution log initialized...');
    
    // Start auto-refresh
    this.startAutoRefresh();
    
    // Initial data load
    await this.refreshData();
  }
  
  startAutoRefresh() {
    if (this.autoRefreshInterval) {
      clearInterval(this.autoRefreshInterval);
    }
    
    this.autoRefreshInterval = setInterval(() => this.refreshData(), this.refreshRate);
    console.log(`Auto-refresh started (every ${this.refreshRate/1000} seconds)`);
  }
  
  stopAutoRefresh() {
    if (this.autoRefreshInterval) {
      clearInterval(this.autoRefreshInterval);
      this.autoRefreshInterval = null;
      console.log('Auto-refresh stopped');
    }
  }
  
  async refreshData() {
    this.logMessage('Refreshed data');
    
    try {
      // Load evolution report
      const report = await this.apiService.getEvolutionReport();
      this.updateEvolutionReport(report);
    } catch (error) {
      this.logMessage(`Failed to load report: ${error.message}`);
      this.updateEvolutionReport(null);
    }
    
    try {
      // Load patterns
      const patterns = await this.apiService.getPatterns();
      this.updatePatterns(patterns);
    } catch (error) {
      this.logMessage(`Failed to load patterns: ${error.message}`);
      this.updatePatterns(null);
    }
  }
  
  updateEvolutionReport(report) {
    if (report) {
      // Update UI with report data
      this.emit('reportLoaded', report);
    } else {
      // Show error state
      this.emit('reportError');
    }
  }
  
  updatePatterns(patterns) {
    if (patterns) {
      // Update UI with patterns
      this.emit('patternsLoaded', patterns);
    } else {
      // Show error state
      this.emit('patternsError');
    }
  }
  
  handleOnline() {
    this.isOfflineMode = false;
    this.logMessage('Network connection restored, exiting offline mode');
    this.emit('onlineMode');
    
    // Refresh data immediately upon going online
    this.refreshData();
  }
  
  handleOffline() {
    this.isOfflineMode = true;
    this.logMessage('Network connection lost, entering offline mode');
    this.emit('offlineMode');
  }
  
  logMessage(message) {
    const timestamp = new Date().toLocaleTimeString();
    const logEntry = `[${timestamp}] ${message}`;
    console.log(logEntry);
    this.emit('logUpdate', logEntry);
  }
  
  // Event handling methods
  on(event, callback) {
    if (!this.eventListeners[event]) {
      this.eventListeners[event] = [];
    }
    this.eventListeners[event].push(callback);
  }
  
  emit(event, data) {
    if (this.eventListeners[event]) {
      this.eventListeners[event].forEach(callback => callback(data));
    }
  }
  
  // Cleanup method
  shutdown() {
    this.stopAutoRefresh();
    this.networkMonitor.stop();
    this.logMessage('Dashboard controller shutdown');
  }
}

module.exports = DashboardController;
