const DashboardController = require('./dashboard_controller');
const fs = require('fs');
const path = require('path');
const express = require('express');
const cors = require('cors');
const http = require('http');

// Load configuration
const configPath = path.join(__dirname, 'config.js');
const config = fs.existsSync(configPath) ? require('./config') : {
  port: process.env.PORT || 3000,
  apiUrl: process.env.API_URL || 'http://localhost:3000/api',
  cachePath: path.join(__dirname, 'cache'),
  networkCheckInterval: 30000,
  refreshRate: 60000
};

// Create express app with improved error handling
const app = express();

// Enhanced CORS configuration
app.use(cors({
  origin: '*', // Allow all origins
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization'],
  credentials: true
}));

app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

// Add error handling middleware
app.use((err, req, res, next) => {
  console.error(`API Error: ${err.message}`);
  res.status(500).json({
    error: 'Server Error',
    message: err.message
  });
});

// Initialize dashboard controller
const dashboardController = new DashboardController(config);

// Improved API routes with better error handling
app.get('/api/status', (req, res) => {
  try {
    res.json({
      status: 'ok',
      networkStatus: dashboardController.networkMonitor.getStatus(),
      offlineMode: dashboardController.isOfflineMode,
      version: '1.0.1',
      server: {
        uptime: process.uptime(),
        timestamp: new Date().toISOString(),
        nodeVersion: process.version
      }
    });
  } catch (error) {
    console.error(`Error in /api/status: ${error.message}`);
    res.status(500).json({ error: 'Failed to get status' });
  }
});

app.get('/api/evolution/report', (req, res) => {
  try {
    // Simulated report data
    const reportFile = path.join(config.cachePath, 'evolution_report.json');
    
    if (fs.existsSync(reportFile)) {
      try {
        const report = JSON.parse(fs.readFileSync(reportFile));
        res.json(report);
      } catch (error) {
        console.error(`Error reading report file: ${error.message}`);
        generateSampleReport(res);
      }
    } else {
      generateSampleReport(res);
    }
  } catch (error) {
    console.error(`Error in /api/evolution/report: ${error.message}`);
    res.status(500).json({ error: 'Failed to get report data' });
  }
});

app.get('/api/patterns', (req, res) => {
  try {
    // Simulated patterns data
    const patternsFile = path.join(config.cachePath, 'patterns.json');
    
    if (fs.existsSync(patternsFile)) {
      try {
        const patterns = JSON.parse(fs.readFileSync(patternsFile));
        res.json(patterns);
      } catch (error) {
        console.error(`Error reading patterns file: ${error.message}`);
        generateSamplePatterns(res);
      }
    } else {
      generateSamplePatterns(res);
    }
  } catch (error) {
    console.error(`Error in /api/patterns: ${error.message}`);
    res.status(500).json({ error: 'Failed to get patterns data' });
  }
});

// Helper functions for generating sample data
function generateSampleReport(res) {
  console.log('Generating sample evolution report');
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
  
  try {
    // Ensure cache directory exists
    if (!fs.existsSync(config.cachePath)) {
      fs.mkdirSync(config.cachePath, { recursive: true });
    }
    
    fs.writeFileSync(path.join(config.cachePath, 'evolution_report.json'), JSON.stringify(sampleReport));
    res.json(sampleReport);
  } catch (error) {
    console.error(`Failed to generate report data: ${error.message}`);
    res.status(500).json({ error: 'Failed to generate report data' });
  }
}

function generateSamplePatterns(res) {
  console.log('Generating sample patterns');
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
  
  try {
    // Ensure cache directory exists
    if (!fs.existsSync(config.cachePath)) {
      fs.mkdirSync(config.cachePath, { recursive: true });
    }
    
    fs.writeFileSync(path.join(config.cachePath, 'patterns.json'), JSON.stringify(samplePatterns));
    res.json(samplePatterns);
  } catch (error) {
    console.error(`Failed to generate patterns data: ${error.message}`);
    res.status(500).json({ error: 'Failed to generate patterns data' });
  }
}

// Create server with proper error handling
const server = http.createServer(app);

server.on('error', (error) => {
  console.error(`Server error: ${error.message}`);
  if (error.code === 'EADDRINUSE') {
    console.error(`Port ${config.port} is already in use. Trying again in 5 seconds...`);
    setTimeout(() => {
      server.close();
      server.listen(config.port);
    }, 5000);
  }
});

// Start the server
server.listen(config.port, () => {
  console.log(`Sorting Hat API service running on port ${config.port}`);
  console.log(`API URL: ${config.apiUrl}`);
  dashboardController.initialize();
});

// Handle graceful shutdown
process.on('SIGINT', () => {
  console.log('Shutting down API server...');
  server.close(() => {
    dashboardController.shutdown();
    console.log('Server shutdown complete.');
    process.exit(0);
  });
});

// Handle uncaught exceptions
process.on('uncaughtException', (error) => {
  console.error(`Uncaught exception: ${error.message}`);
  console.error(error.stack);
});
