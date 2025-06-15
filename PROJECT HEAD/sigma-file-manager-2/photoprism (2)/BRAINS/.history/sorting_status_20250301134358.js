/**
 * Sorting Hat Status Checker
 * Displays the current status of the sorting system and troubleshooting information
 */

const fs = require('fs');
const path = require('path');
const { exec } = require('child_process');

// Configuration paths
const config = {
  sourceDir: 'C:/Users/casey/Documents',
  destDir: 'C:/Users/casey/OrganizeFolder',
  categories: [
    'Legal', 'Financial', 'Real Estate', 'Family',
    'Business', 'Education', 'Creativity', 'Technology',
    'Miscellaneous'
  ]
};

// Check if a process is running
function isProcessRunning(processName, callback) {
  const cmd = process.platform === 'win32' 
    ? `tasklist /FI "IMAGENAME eq ${processName}" /FO CSV /NH`
    : `ps aux | grep ${processName} | grep -v grep`;
  
  exec(cmd, (error, stdout) => {
    if (error) {
      console.error(`Error checking process: ${error.message}`);
      callback(false);
      return;
    }
    
    callback(stdout.toLowerCase().includes(processName.toLowerCase()));
  });
}

// Check folder permissions
function checkFolderPermissions(folderPath, callback) {
  try {
    // Try to write a test file
    const testFile = path.join(folderPath, '.permission_test');
    fs.writeFileSync(testFile, 'test');
    fs.unlinkSync(testFile);
    callback(true);
  } catch (error) {
    callback(false, error.message);
  }
}

// Count files in a directory
function countFilesInDirectory(dirPath) {
  try {
    if (!fs.existsSync(dirPath)) {
      return 0;
    }
    
    return fs.readdirSync(dirPath)
      .filter(file => fs.statSync(path.join(dirPath, file)).isFile())
      .length;
  } catch (error) {
    console.error(`Error counting files in ${dirPath}: ${error.message}`);
    return 0;
  }
}

// Format as readable file size
function formatBytes(bytes, decimals = 2) {
  if (bytes === 0) return '0 Bytes';
  
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(decimals)) + ' ' + sizes[i];
}

// Get directory size recursively
function getDirSize(dirPath) {
  let size = 0;
  
  try {
    const files = fs.readdirSync(dirPath);
    
    for (const file of files) {
      const filePath = path.join(dirPath, file);
      const stats = fs.statSync(filePath);
      
      if (stats.isDirectory()) {
        size += getDirSize(filePath);
      } else {
        size += stats.size;
      }
    }
  } catch (error) {
    console.error(`Error getting size of ${dirPath}: ${error.message}`);
  }
  
  return size;
}

// Main function to check status
async function checkStatus() {
  console.log("==================================================");
  console.log("            SORTING HAT SYSTEM STATUS             ");
  console.log("==================================================");
  
  // Check if Node.js is running
  isProcessRunning('node.exe', (isRunning) => {
    console.log(`File Organizer Service: ${isRunning ? '✓ RUNNING' : '✗ NOT RUNNING'}`);
    
    if (!isRunning) {
      console.log("  ► To start the service, run: node file_organizer.js");
    }
  });
  
  // Check source directory
  console.log("\nSource Directory:");
  if (fs.existsSync(config.sourceDir)) {
    console.log(`  ✓ ${config.sourceDir} exists`);
    const fileCount = countFilesInDirectory(config.sourceDir);
    console.log(`  ► Contains ${fileCount} files`);
    
    checkFolderPermissions(config.sourceDir, (hasPermission, error) => {
      if (hasPermission) {
        console.log("  ✓ Has correct permissions");
      } else {
        console.log(`  ✗ Permission error: ${error}`);
        console.log("  ► Run permission_fix.bat as administrator to fix");
      }
    });
  } else {
    console.log(`  ✗ ${config.sourceDir} does not exist`);
  }
  
  // Check destination directory
  console.log("\nDestination Directory:");
  if (fs.existsSync(config.destDir)) {
    console.log(`  ✓ ${config.destDir} exists`);
    const size = getDirSize(config.destDir);
    console.log(`  ► Total storage used: ${formatBytes(size)}`);
    
    checkFolderPermissions(config.destDir, (hasPermission, error) => {
      if (hasPermission) {
        console.log("  ✓ Has correct permissions");
      } else {
        console.log(`  ✗ Permission error: ${error}`);
        console.log("  ► Run permission_fix.bat as administrator to fix");
      }
    });
  } else {
    console.log(`  ✗ ${config.destDir} does not exist`);
    console.log("  ► Run setup_folders.bat to create necessary folders");
  }
  
  // Check category folders
  console.log("\nCategory Folders:");
  for (const category of config.categories) {
    const categoryPath = path.join(config.destDir, category);
    
    if (fs.existsSync(categoryPath)) {
      const fileCount = countFilesInDirectory(categoryPath);
      console.log(`  ✓ ${category}: ${fileCount} files`);
    } else {
      console.log(`  ✗ ${category} folder does not exist`);
    }
  }
  
  console.log("\nTroubleshooting Tips:");
  console.log("  1. If permissions errors persist, run permission_fix.bat as administrator");
  console.log("  2. To restart the service, run restart_api_server.bat");
  console.log("  3. Check logs for detailed error messages");
  console.log("==================================================");
}

// Run the status check
checkStatus().catch(error => {
  console.error("Error checking status:", error);
});
