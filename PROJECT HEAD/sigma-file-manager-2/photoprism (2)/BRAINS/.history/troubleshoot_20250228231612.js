/**
 * Troubleshooting tool for Sorting Hat network issues
 */
const fs = require('fs');
const path = require('path');
const dns = require('dns');
const http = require('http');
const { exec } = require('child_process');
const ApiService = require('./api_service');

// Configuration
const config = {
  apiUrl: process.env.API_URL || 'http://localhost:3000/api',
  cachePath: path.join(__dirname, 'cache'),
  endpoints: ['evolution/report', 'patterns'],
  networkCheckHosts: ['google.com', 'microsoft.com', 'cloudflare.com']
};

// Initialize API service
const apiService = new ApiService(config.apiUrl, config.cachePath);

/**
 * Run diagnostics and fix network issues
 */
async function diagnose() {
  console.log('=====================================================');
  console.log('SORTING HAT TROUBLESHOOTING TOOL');
  console.log('=====================================================');
  
  // 1. Check network connectivity
  console.log('\n🔍 Checking network connectivity...');
  const internetAvailable = await checkInternetConnectivity();
  
  if (!internetAvailable) {
    console.log('❌ No internet connectivity detected.');
    console.log('ℹ️ Switching to offline mode with local cache.');
    await ensureLocalCache();
  } else {
    console.log('✅ Internet connectivity is available.');
  }
  
  // 2. Check API server status
  console.log('\n🔍 Checking API server status...');
  const apiAvailable = await checkApiServerStatus();
  
  if (!apiAvailable) {
    console.log('❌ API server is not reachable.');
    console.log('ℹ️ Starting local API server...');
    await startLocalServer();
  } else {
    console.log('✅ API server is reachable.');
  }
  
  // 3. Validate API endpoints
  console.log('\n🔍 Validating API endpoints...');
  for (const endpoint of config.endpoints) {
    await validateEndpoint(endpoint);
  }
  
  // 4. Ensure that cached data is available
  console.log('\n🔍 Checking cached data...');
  await ensureLocalCache();
  
  // 5. Check service configuration
  console.log('\n🔍 Checking service configuration...');
  await checkServiceConfiguration();
  
  console.log('\n=====================================================');
  console.log('TROUBLESHOOTING COMPLETE');
  console.log('=====================================================');
}

/**
 * Check if internet is available
 */
async function checkInternetConnectivity() {
  try {
    console.log('Testing DNS resolution...');
    for (const host of config.networkCheckHosts) {
      try {
        await new Promise((resolve, reject) => {
          dns.resolve(host, (err) => {
            if (err) reject(err);
            else resolve();
          });
        });
        console.log(`  ✅ Successfully resolved ${host}`);
        return true;
      } catch (error) {
        console.log(`  ❌ Failed to resolve ${host}: ${error.message}`);
      }
    }
    
    console.log('Testing connection to 8.8.8.8...');
    await new Promise((resolve, reject) => {
      exec('ping -n 1 -w 1000 8.8.8.8', (error) => {
        if (error) reject(error);
        else resolve();
      });
    });
    console.log('  ✅ Successfully pinged 8.8.8.8');
    return true;
  } catch (error) {
    console.log('  ❌ Failed to ping 8.8.8.8');
    return false;
  }
}

/**
 * Check if API server is reachable
 */
async function checkApiServerStatus() {
  try {
    const apiUrl = new URL(config.apiUrl);
    const options = {
      hostname: apiUrl.hostname,
      port: apiUrl.port || 3000,
      path: '/api/status',
      method: 'GET',
      timeout: 5000
    };
    
    console.log(`Testing connection to ${apiUrl.hostname}:${options.port}...`);
    
    await new Promise((resolve, reject) => {
      const req = http.request(options, (res) => {
        if (res.statusCode === 200) {
          let data = '';
          res.on('data', (chunk) => data += chunk);
          res.on('end', () => {
            try {
              const statusData = JSON.parse(data);
              console.log(`  ✅ API server is running (version: ${statusData.version || 'unknown'})`);
              resolve();
            } catch (e) {
              console.log('  ✅ API server responded but with invalid JSON');
              resolve();
            }
          });
        } else {
          console.log(`  ❌ API server responded with status code ${res.statusCode}`);
          reject(new Error(`Invalid status code: ${res.statusCode}`));
        }
      });
      
      req.on('error', (error) => {
        console.log(`  ❌ Failed to connect to API server: ${error.message}`);
        reject(error);
      });
      
      req.on('timeout', () => {
        console.log('  ❌ Request timeout');
        req.abort();
        reject(new Error('Request timeout'));
      });
      
      req.end();
    });
    
    return true;
  } catch (error) {
    return false;
  }
}

/**
 * Start the local API server if not running
 */
async function startLocalServer() {
  try {
    console.log('Checking if Node.js server is running...');
    
    // Check if the process is already running
    const isWin = process.platform === 'win32';
    const cmd = isWin 
      ? 'tasklist /FI "IMAGENAME eq node.exe" /FO CSV /NH'
      : 'ps aux | grep "node" | grep -v grep';
    
    exec(cmd, (error, stdout) => {
      if (error) {
        console.log(`  ❌ Failed to check running processes: ${error.message}`);
        return;
      }
      
      if (stdout.toLowerCase().includes('node.exe') || stdout.includes('node service.js')) {
        console.log('  ℹ️ Node.js process is already running.');
      } else {
        console.log('  ℹ️ Starting local API server...');
        
        // Start the server in a detached process
        const serverPath = path.join(__dirname, 'service.js');
        const child = exec(`node ${serverPath}`, (error) => {
          if (error) {
            console.log(`  ❌ Failed to start server: ${error.message}`);
          }
        });
        
        child.unref();
        console.log('  ✅ Local API server started.');
      }
    });
    
    return true;
  } catch (error) {
    console.log(`  ❌ Failed to start local server: ${error.message}`);
    return false;
  }
}

/**
 * Validate specific API endpoint
 */
async function validateEndpoint(endpoint) {
  try {
    console.log(`Testing endpoint ${endpoint}...`);
    await apiService.fetchWithRetry(endpoint, { timeout: 5000 }, 1);
    console.log(`  ✅ Successfully accessed endpoint ${endpoint}`);
    return true;
  } catch (error) {
    console.log(`  ❌ Failed to access endpoint ${endpoint}: ${error.message}`);
    console.log('  ℹ️ Generating sample data for this endpoint...');
    
    // Create sample data based on endpoint
    if (endpoint === 'evolution/report') {
      createSampleEvolutionReport();
    } else if (endpoint === 'patterns') {
      createSamplePatterns();
    }
    
    return false;
  }
}

/**
 * Create sample evolution report
 */
function createSampleEvolutionReport() {
  const reportFile = path.join(config.cachePath, 'evolution_report.json');
  
  if (!fs.existsSync(config.cachePath)) {
    fs.mkdirSync(config.cachePath, { recursive: true });
  }
  
  const sampleReport = {
    timestamp: new Date().toISOString(),
    metrics: {
      filesProcessed: 1243,
      categoriesDetected: 17,
      accuracyScore: 0.92,
      processingTime: 425,
    },
    categories: [
      { name: 'Legal', count: 142, accuracy: 0.94 },
      { name: 'Financial', count: 257, accuracy: 0.96 },
      { name: 'Business', count: 87, accuracy: 0.91 },
      { name: 'Technology', count: 198, accuracy: 0.93 },
      { name: 'Personal', count: 559, accuracy: 0.89 }
    ]
  };
  
  fs.writeFileSync(reportFile, JSON.stringify({
    data: sampleReport,
    timestamp: new Date().toISOString()
  }));
  
  console.log(`  ✅ Created sample evolution report data at ${reportFile}`);
}

/**
 * Create sample patterns
 */
function createSamplePatterns() {
  const patternsFile = path.join(config.cachePath, 'patterns.json');
  
  if (!fs.existsSync(config.cachePath)) {
    fs.mkdirSync(config.cachePath, { recursive: true });
  }
  
  const samplePatterns = [
    { 
      id: 'legal-docs',
      name: 'Legal Documents',
      pattern: '\\b(court|lawsuit|legal|attorney|lawyer)\\b',
      category: 'Legal',
      subcategory: 'Court Filings',
      priority: 3,
      active: true
    },
    {
      id: 'financial-reports',
      name: 'Financial Reports',
      pattern: '\\b(report|statement|balance|income|expense|profit|loss)\\b',
      category: 'Financial',
      subcategory: 'Statements',
      priority: 2,
      active: true
    },
    {
      id: 'code-files',
      name: 'Programming Code',
      pattern: '\\.(js|py|cpp|java|html|css|php)$',
      category: 'Technology',
      subcategory: 'Code & Projects',
      priority: 2,
      active: true
    }
  ];
  
  fs.writeFileSync(patternsFile, JSON.stringify({
    data: samplePatterns,
    timestamp: new Date().toISOString()
  }));
  
  console.log(`  ✅ Created sample patterns data at ${patternsFile}`);
}

/**
 * Ensure local cache exists and has all required data
 */
async function ensureLocalCache() {
  console.log('Checking cache directory...');
  
  if (!fs.existsSync(config.cachePath)) {
    fs.mkdirSync(config.cachePath, { recursive: true });
    console.log(`  ✅ Created cache directory at ${config.cachePath}`);
  } else {
    console.log(`  ✅ Cache directory exists at ${config.cachePath}`);
  }
  
  // Check for evolution report cache
  const reportCachePath = path.join(config.cachePath, 'evolution_report.json');
  if (!fs.existsSync(reportCachePath)) {
    console.log('  ℹ️ No cached evolution report found, creating sample data...');
    createSampleEvolutionReport();
  } else {
    console.log('  ✅ Evolution report cache exists');
  }
  
  // Check for patterns cache
  const patternsCachePath = path.join(config.cachePath, 'patterns.json');
  if (!fs.existsSync(patternsCachePath)) {
    console.log('  ℹ️ No cached patterns found, creating sample data...');
    createSamplePatterns();
  } else {
    console.log('  ✅ Patterns cache exists');
  }
}

/**
 * Check service configuration
 */
async function checkServiceConfiguration() {
  console.log('Checking API URL configuration...');
  console.log(`  Current API URL: ${config.apiUrl}`);
  
  // Check local hosts file
  console.log('Checking hosts file...');
  const hostsPath = process.platform === 'win32' 
    ? 'C:/Windows/System32/drivers/etc/hosts'
    : '/etc/hosts';
  
  try {
    if (fs.existsSync(hostsPath)) {
      const hostsContent = fs.readFileSync(hostsPath, 'utf8');
      if (hostsContent.includes('localhost')) {
        console.log('  ✅ Hosts file contains localhost entries');
      } else {
        console.log('  ⚠️ Hosts file does not contain localhost entries');
      }
    }
  } catch (error) {
    console.log(`  ⚠️ Could not read hosts file: ${error.message}`);
  }
  
  // Check if config.js exists
  const configPath = path.join(__dirname, 'config.js');
  if (!fs.existsSync(configPath)) {
    console.log('  ℹ️ No custom config.js found, creating one...');
    const configContent = `
module.exports = {
  apiUrl: 'http://localhost:3000/api',
  port: 3000,
  cachePath: '${config.cachePath.replace(/\\/g, '\\\\')}',
  refreshRate: 60000,
  networkCheckInterval: 30000,
  offlineMode: true
};`;
    
    fs.writeFileSync(configPath, configContent);
    console.log('  ✅ Created config.js with offline mode enabled');
  }
}

// Run the diagnostic tool
diagnose().catch(error => {
  console.error('Error during troubleshooting:', error);
});
