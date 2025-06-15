/**
 * Sorting Hat Activity Monitor
 * Shows real-time progress and statistics for file organization
 */
const fs = require('fs');
const path = require('path');
const readline = require('readline');

// Configuration
const config = {
  sourceDir: 'C:/Users/casey/Documents',
  destDir: 'C:/Users/casey/OrganizeFolder',
  updateInterval: 2000, // ms
  categories: [
    'Legal', 'Financial', 'Real Estate', 'Family',
    'Business', 'Education', 'Creativity', 'Technology',
    'Miscellaneous'
  ]
};

// Statistics storage
const stats = {
  totalProcessed: 0,
  categoryCounts: {},
  startTime: new Date(),
  lastUpdate: new Date(),
  recentlyMoved: []
};

// Initialize stats
for (const category of config.categories) {
  stats.categoryCounts[category] = 0;
}

// Clear the console and render the UI
function renderUI() {
  readline.cursorTo(process.stdout, 0, 0);
  readline.clearScreenDown(process.stdout);
  
  const runTime = Math.round((new Date() - stats.startTime) / 1000);
  const hours = Math.floor(runTime / 3600);
  const minutes = Math.floor((runTime % 3600) / 60);
  const seconds = runTime % 60;
  
  console.log('==================================================');
  console.log('            SORTING HAT ACTIVITY MONITOR          ');
  console.log('==================================================');
  console.log(`Runtime: ${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`);
  console.log(`Files Processed: ${stats.totalProcessed}`);
  console.log('--------------------------------------------------');
  console.log('CATEGORY STATISTICS:');
  
  // Get max category name length for padding
  const maxLength = Math.max(...config.categories.map(c => c.length));
  
  // Sort categories by count (descending)
  const sortedCategories = [...config.categories].sort(
    (a, b) => stats.categoryCounts[b] - stats.categoryCounts[a]
  );
  
  // Print category stats
  for (const category of sortedCategories) {
    const count = stats.categoryCounts[category];
    const percentage = stats.totalProcessed ? Math.round((count / stats.totalProcessed) * 100) : 0;
    const bar = '█'.repeat(Math.floor(percentage / 5)).padEnd(20, '░');
    console.log(`${category.padEnd(maxLength + 2)}: ${count.toString().padStart(5)} | ${bar} ${percentage}%`);
  }
  
  console.log('--------------------------------------------------');
  console.log('RECENTLY PROCESSED FILES:');
  
  // Show last 5 processed files
  const recentFiles = stats.recentlyMoved.slice(-5);
  if (recentFiles.length === 0) {
    console.log('(No files processed yet)');
  } else {
    for (const file of recentFiles) {
      console.log(`- ${file.name} → ${file.category}`);
    }
  }
  
  console.log('==================================================');
  console.log('Press Ctrl+C to stop monitoring');
}

// Update category statistics by scanning the destination folders
function updateStats() {
  let totalFiles = 0;
  
  // Reset counts
  for (const category of config.categories) {
    const categoryPath = path.join(config.destDir, category);
    
    if (fs.existsSync(categoryPath)) {
      try {
        const files = fs.readdirSync(categoryPath).filter(
          file => !fs.statSync(path.join(categoryPath, file)).isDirectory()
        );
        
        stats.categoryCounts[category] = files.length;
        totalFiles += files.length;
      } catch (error) {
        console.error(`Error reading directory ${categoryPath}: ${error.message}`);
      }
    }
  }
  
  // If total changed, we can assume files were moved
  if (totalFiles > stats.totalProcessed) {
    // Something was added, check for new files
    for (const category of config.categories) {
      const categoryPath = path.join(config.destDir, category);
      
      if (fs.existsSync(categoryPath)) {
        try {
          const files = fs.readdirSync(categoryPath);
          
          for (const file of files) {
            const filePath = path.join(categoryPath, file);
            
            // Check if file is new since last update
            try {
              const stats = fs.statSync(filePath);
              if (stats.mtime > this.stats.lastUpdate && !fs.statSync(filePath).isDirectory()) {
                // This is a newly added file
                this.stats.recentlyMoved.push({
                  name: file,
                  category: category,
                  time: new Date()
                });
              }
            } catch (e) {
              // Ignore errors, file might have been moved/deleted
            }
          }
        } catch (e) {
          // Ignore errors reading directory
        }
      }
    }
  }
  
  // Update totals
  stats.totalProcessed = totalFiles;
  stats.lastUpdate = new Date();
}

// Start monitoring
function startMonitoring() {
  console.log('Starting Sorting Hat Activity Monitor...');
  
  // Do initial stats collection
  updateStats();
  renderUI();
  
  // Set up interval for updates
  setInterval(() => {
    updateStats();
    renderUI();
  }, config.updateInterval);
}

// Clean up recent files list (remove items older than 5 minutes)
setInterval(() => {
  const fiveMinutesAgo = new Date(Date.now() - 5 * 60 * 1000);
  stats.recentlyMoved = stats.recentlyMoved.filter(item => item.time > fiveMinutesAgo);
}, 60000);

// Handle exit
process.on('SIGINT', () => {
  readline.cursorTo(process.stdout, 0, process.stdout.rows);
  console.log('\nSorting Hat Activity Monitor stopped.');
  process.exit(0);
});

// Start the monitor
startMonitoring();
