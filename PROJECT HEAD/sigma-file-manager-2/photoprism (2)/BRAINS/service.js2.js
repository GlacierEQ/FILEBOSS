const DashboardController = require('./dashboard_controller');
const fs = require('fs');
const path = require('path');
const express = require('express');
const cors = require('cors');

// Configuration
const config = {
  port: process.env.PORT || 3000,
  apiUrl: process.env.API_URL || 'http://localhost:3000/api',
  cachePath: path.join(__dirname, 'cache'),
  networkCheckInterval: 30000,
  refreshRate: 60000
};

// Create express app
const app = express();
app.use(cors());
app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

// Initialize dashboard controller
const dashboardController = new DashboardController(config);

// Set up API routes
app.get('/api/status', (req, res) => {
  res.json({
    status: 'ok',
    networkStatus: dashboardController.networkMonitor.getStatus(),
    offlineMode: dashboardController.isOfflineMode,
    version: '1.0.0'
  });
});

app.get('/api/evolution/report', (req, res) => {
  // Simulated report data
  const reportFile = path.join(__dirname, 'cache', 'evolution_report.json');
  
  if (fs.existsSync(reportFile)) {
    try {
      const report = JSON.parse(fs.readFileSync(reportFile));
      res.json(report);
    } catch (error) {
      res.status(500).json({ error: 'Failed to read report data' });
    }
  } else {
    // Generate sample report data if none exists
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
      fs.writeFileSync(reportFile, JSON.stringify(sampleReport));
      res.json(sampleReport);
    } catch (error) {
      res.status(500).json({ error: 'Failed to generate report data' });
    }
  }
});

app.get('/api/patterns', (req, res) => {
  // Simulated patterns data
  const patternsFile = path.join(__dirname, 'cache', 'patterns.json');
  
  if (fs.existsSync(patternsFile)) {
    try {
      const patterns = JSON.parse(fs.readFileSync(patternsFile));
      res.json(patterns);
    } catch (error) {
      res.status(500).json({ error: 'Failed to read patterns data' });
    }
  } else {
    // Generate sample patterns data if none exists
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
      fs.writeFileSync(patternsFile, JSON.stringify(samplePatterns));
      res.json(samplePatterns);
    } catch (error) {
      res.status(500).json({ error: 'Failed to generate patterns data' });
    }
  }
});

// Start the server
app.listen(config.port, () => {
  console.log(`Sorting Hat service running on port ${config.port}`);
  dashboardController.initialize();
});

// Handle graceful shutdown
process.on('SIGINT', () => {
  console.log('Shutting down...');
  dashboardController.shutdown();
  process.exit(0);
});
