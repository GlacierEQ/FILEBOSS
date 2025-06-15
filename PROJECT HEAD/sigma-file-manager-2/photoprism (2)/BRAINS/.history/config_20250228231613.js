/**
 * Sorting Hat Configuration
 */
module.exports = {
  // API configuration
  apiUrl: 'http://localhost:3000/api',
  port: 3000,
  
  // File system paths
  cachePath: 'C:/SORTING HAT/BRAINS/cache',
  
  // Performance settings
  refreshRate: 60000,         // Data refresh rate in ms
  networkCheckInterval: 30000, // Network check interval in ms
  
  // Operation modes
  offlineMode: true,          // Enable offline mode by default
  cacheFirst: true,           // Use cache-first strategy
  
  // Sorting rules location
  rulesPath: 'C:/SORTING HAT/BRAINS/rules',
  
  // Logging
  logLevel: 'info',           // debug, info, warn, error
  logToFile: true,
  logFilePath: 'C:/SORTING HAT/BRAINS/logs/sorting-hat.log'
};
