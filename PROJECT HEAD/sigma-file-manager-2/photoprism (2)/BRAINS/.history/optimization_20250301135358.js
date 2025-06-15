/**
 * Sorting Hat System Optimizer
 * Performs system maintenance and optimization tasks
 */
const fs = require('fs');
const path = require('path');
const { exec } = require('child_process');

// Configuration
const config = {
  sourceDir: 'C:/Users/casey/Documents',
  destDir: 'C:/Users/casey/OrganizeFolder',
  programDir: 'C:/SORTING HAT/BRAINS',
  categories: [
    'Legal', 'Financial', 'Real Estate', 'Family',
    'Business', 'Education', 'Creativity', 'Technology',
    'Miscellaneous'
  ],
  maxCacheAge: 7 * 24 * 60 * 60 * 1000, // 7 days in milliseconds
  maxLogSize: 10 * 1024 * 1024, // 10MB in bytes
  systemFoldersToIgnore: [
    'My Music',
    'My Pictures',
    'My Videos',
    'Start Menu',
    'Templates',
    'NetHood',
    'PrintHood',
    'Recent',
    'SendTo',
    'Application Data',
    'Local Settings'
  ]
};

/**
 * Clean up old cache files
 */
function cleanupCache() {
  console.log("Cleaning up old cache files...");
  
  const cachePath = path.join(config.programDir, 'cache');
  if (!fs.existsSync(cachePath)) {
    console.log("Cache directory doesn't exist. Creating it...");
    fs.mkdirSync(cachePath, { recursive: true });
    return;
  }
  
  try {
    const files = fs.readdirSync(cachePath);
    const now = new Date();
    let removedCount = 0;
    
    for (const file of files) {
      const filePath = path.join(cachePath, file);
      const stats = fs.statSync(filePath);
      
      // Check if file is older than maxCacheAge
      if (now - stats.mtime > config.maxCacheAge) {
        fs.unlinkSync(filePath);
        removedCount++;
      }
    }
    
    console.log(`Removed ${removedCount} old cache files.`);
  } catch (error) {
    console.error(`Error cleaning cache: ${error.message}`);
  }
}

/**
 * Rotate log files if they get too large
 */
function rotateLogs() {
  console.log("Checking log files...");
  
  const logPath = path.join(config.programDir, 'logs');
  if (!fs.existsSync(logPath)) {
    console.log("Log directory doesn't exist. Creating it...");
    fs.mkdirSync(logPath, { recursive: true });
    return;
  }
  
  try {
    const files = fs.readdirSync(logPath);
    
    for (const file of files) {
      if (!file.endsWith('.log')) continue;
      
      const filePath = path.join(logPath, file);
      const stats = fs.statSync(filePath);
      
      if (stats.size > config.maxLogSize) {
        console.log(`Rotating log file: ${file}`);
        
        // Create a timestamp for the archived log
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
        const archivePath = path.join(logPath, `${path.basename(file, '.log')}-${timestamp}.log`);
        
        // Rename current log to archive name
        fs.renameSync(filePath, archivePath);
        
        // Create a new empty log file
        fs.writeFileSync(filePath, `Log rotated at ${new Date().toISOString()}\n`);
      }
    }
  } catch (error) {
    console.error(`Error rotating logs: ${error.message}`);
  }
}

/**
 * Update system rules
 */
function updateSystemRules() {
  console.log("Updating system rules...");
  
  const systemIgnoreFile = path.join(config.programDir, 'system_ignore.json');
  
  try {
    // Save the current system folders to ignore
    fs.writeFileSync(
      systemIgnoreFile, 
      JSON.stringify({
        ignoreFolders: config.systemFoldersToIgnore,
        updatedAt: new Date().toISOString()
      }, null, 2)
    );
    
    console.log("System rules updated successfully.");
  } catch (error) {
    console.error(`Error updating system rules: ${error.message}`);
  }
}

/**
 * Check for duplicate files across categories
 */
function checkDuplicates() {
  console.log("Checking for duplicate files...");
  
  const fileHashes = new Map();
  const duplicates = [];
  
  // Helper function to get file size (simple hash for now)
  function getFileHash(filePath) {
    try {
      const stats = fs.statSync(filePath);
      return `${stats.size}_${path.basename(filePath)}`;
    } catch (error) {
      return null;
    }
  }
  
  // Check each category folder
  for (const category of config.categories) {
    const categoryPath = path.join(config.destDir, category);
    
    if (!fs.existsSync(categoryPath)) continue;
    
    try {
      const files = fs.readdirSync(categoryPath);
      
      for (const file of files) {
        const filePath = path.join(categoryPath, file);
        
        if (fs.statSync(filePath).isDirectory()) continue;
        
        const hash = getFileHash(filePath);
        
        if (!hash) continue;
        
        if (fileHashes.has(hash)) {
          duplicates.push({
            original: fileHashes.get(hash),
            duplicate: {
              path: filePath,
              category: category
            }
          });
        } else {
          fileHashes.set(hash, {
            path: filePath,
            category: category
          });
        }
      }
    } catch (error) {
      console.error(`Error checking category ${category}: ${error.message}`);
    }
  }
  
  // Report duplicates
  if (duplicates.length > 0) {
    console.log(`Found ${duplicates.length} potential duplicate files:`);
    
    for (const dup of duplicates.slice(0, 10)) {
      console.log(`- "${path.basename(dup.duplicate.path)}" in ${dup.duplicate.category} may be a duplicate of "${path.basename(dup.original.path)}" in ${dup.original.category}`);
    }
    
    if (duplicates.length > 10) {
      console.log(`  ... and ${duplicates.length - 10} more`);
    }
  } else {
    console.log("No duplicate files found.");
  }
}

/**
 * Run all optimization tasks
 */
function runOptimization() {
  console.log("=================================================");
  console.log("            SORTING HAT OPTIMIZATION            ");
  console.log("=================================================");
  
  // Run optimization tasks
  cleanupCache();
  rotateLogs();
  updateSystemRules();
  checkDuplicates();
  
  console.log("\nOptimization complete!");
}

// Run optimization
runOptimization();
