/**
 * File Organizer for Sorting Hat
 * This script monitors and organizes files according to the defined categories
 */
const fs = require('fs');
const path = require('path');
const chokidar = require('chokidar');
const { exec } = require('child_process');

// Configuration
const config = {
  // Source directory to monitor for new files
  sourceDir: 'C:/Users/casey/Documents',
  
  // Destination directory for organized files
  destDir: 'C:/Users/casey/OrganizeFolder',
  
  // Categories and their patterns
  categories: [
    {
      name: 'Legal',
      pattern: /\b(court|lawsuit|legal|attorney|lawyer|filing|evidence|custody|visitation|restraining|appeal)\b/i,
      extensions: ['.pdf', '.doc', '.docx', '.txt']
    },
    {
      name: 'Financial',
      pattern: /\b(tax|bank|statement|bill|receipt|invest|retirement|credit|insurance|loan|debt|expense|budget)\b/i,
      extensions: ['.pdf', '.xls', '.xlsx', '.csv']
    },
    {
      name: 'Real Estate',
      pattern: /\b(mortgage|rent|home|inspection|repair|maintenance|utility|property|moving|storage|house|apartment)\b/i,
      extensions: ['.pdf', '.doc', '.docx', '.jpg', '.png']
    },
    {
      name: 'Family',
      pattern: /\b(parenting|visitation|school|medical|doctor|fitness|diet|travel|family|contact|history|health)\b/i,
      extensions: ['.pdf', '.doc', '.docx', '.jpg', '.png']
    },
    {
      name: 'Business',
      pattern: /\b(client|contract|agreement|invoice|payment|marketing|branding|business|compliance|plan|hr|network)\b/i,
      extensions: ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx']
    },
    {
      name: 'Education',
      pattern: /\b(course|certificate|study|note|research|paper|ebook|ai|programming|development|learn|class|school)\b/i,
      extensions: ['.pdf', '.doc', '.docx', '.ppt', '.pptx', '.txt']
    },
    {
      name: 'Creativity',
      pattern: /\b(photo|video|music|graphic|design|writing|draft|screenplay|project|creative|art|drawing)\b/i,
      extensions: ['.jpg', '.png', '.gif', '.mp4', '.mp3', '.wav', '.psd', '.ai', '.indd', '.svg']
    },
    {
      name: 'Technology',
      pattern: /\b(code|project|github|software|tool|script|automation|troubleshoot|hardware|cloud|backup|tech)\b/i,
      extensions: ['.js', '.py', '.html', '.css', '.cpp', '.java', '.php', '.json', '.xml', '.log']
    },
    {
      name: 'Miscellaneous',
      pattern: /.*/,
      extensions: ['*']
    }
  ],
  
  // Special Windows folders to ignore (these often cause permission errors)
  ignoreFolders: [
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
    'Local Settings',
    'Cookies',
    'History',
    'Temporary Internet Files'
  ],
  
  // Whether to run in debug mode with extra logging
  debug: true
};

// Ensure all destination folders exist
function ensureFolders() {
  console.log('Ensuring destination folders exist...');
  
  if (!fs.existsSync(config.destDir)) {
    fs.mkdirSync(config.destDir, { recursive: true });
    console.log(`Created main destination directory: ${config.destDir}`);
  }
  
  for (const category of config.categories) {
    const categoryPath = path.join(config.destDir, category.name);
    if (!fs.existsSync(categoryPath)) {
      fs.mkdirSync(categoryPath, { recursive: true });
      console.log(`Created category directory: ${categoryPath}`);
    }
  }
}

// Determine category for a file based on name and content
async function categorizeFile(filePath) {
  const fileName = path.basename(filePath).toLowerCase();
  const fileExt = path.extname(filePath).toLowerCase();
  
  // Skip hidden files and temp files
  if (fileName.startsWith('.') || fileName.startsWith('~$') || fileName.endsWith('.tmp')) {
    return null;
  }
  
  // Try to categorize based on filename first
  for (const category of config.categories) {
    // Skip miscellaneous category for now, we'll use it as fallback
    if (category.name === 'Miscellaneous') continue;
    
    // Check if extension matches if extensions are defined
    if (category.extensions && category.extensions[0] !== '*') {
      if (!category.extensions.includes(fileExt)) {
        continue;
      }
    }
    
    if (category.pattern.test(fileName)) {
      if (config.debug) console.log(`Categorized "${fileName}" as "${category.name}" by filename`);
      return category;
    }
  }
  
  // For text-based files, check content as well
  const textExtensions = ['.txt', '.md', '.csv', '.json', '.xml', '.html', '.js', '.py', '.doc', '.docx', '.pdf'];
  if (textExtensions.includes(fileExt)) {
    try {
      let content = '';
      
      // Special handling for PDF files
      if (fileExt === '.pdf') {
        content = await extractTextFromPdf(filePath);
      }
      // Special handling for Word files
      else if (['.doc', '.docx'].includes(fileExt)) {
        content = await extractTextFromWord(filePath);
      }
      // Regular text files
      else {
        content = fs.readFileSync(filePath, 'utf8').toLowerCase();
      }
      
      for (const category of config.categories) {
        // Skip miscellaneous category for now
        if (category.name === 'Miscellaneous') continue;
        
        if (category.pattern.test(content)) {
          if (config.debug) console.log(`Categorized "${fileName}" as "${category.name}" by content`);
          return category;
        }
      }
    } catch (error) {
      console.error(`Error reading file ${filePath}: ${error.message}`);
    }
  }
  
  // If no category matched, use Miscellaneous
  const miscCategory = config.categories.find(cat => cat.name === 'Miscellaneous');
  if (config.debug) console.log(`Categorized "${fileName}" as "Miscellaneous" (default)`);
  return miscCategory;
}

// Extract text from PDF files (placeholder - requires external library)
async function extractTextFromPdf(filePath) {
  // This is a placeholder. In a real implementation, you would use a library like pdf-parse
  // For now, we'll just return the filename to avoid dependencies
  return path.basename(filePath).toLowerCase();
}

// Extract text from Word files (placeholder - requires external library)
async function extractTextFromWord(filePath) {
  // This is a placeholder. In a real implementation, you would use a library like textract
  // For now, we'll just return the filename to avoid dependencies
  return path.basename(filePath).toLowerCase();
}

// Move file to appropriate category folder
async function moveFileToCategory(filePath, category) {
  const fileName = path.basename(filePath);
  const destFolder = path.join(config.destDir, category.name);
  const destPath = path.join(destFolder, fileName);
  
  // If destination file already exists, create a unique name
  let uniqueDestPath = destPath;
  let counter = 1;
  while (fs.existsSync(uniqueDestPath)) {
    const ext = path.extname(fileName);
    const baseName = path.basename(fileName, ext);
    uniqueDestPath = path.join(destFolder, `${baseName} (${counter})${ext}`);
    counter++;
  }
  
  try {
    fs.renameSync(filePath, uniqueDestPath);
    console.log(`Moved "${fileName}" to ${category.name} folder`);
    return true;
  } catch (error) {
    console.error(`Error moving ${fileName}: ${error.message}`);
    return false;
  }
}

// Process a new file
async function processFile(filePath) {
  console.log(`Processing new file: ${filePath}`);
  
  try {
    // Skip directories
    if (fs.statSync(filePath).isDirectory()) {
      return;
    }
    
    const category = await categorizeFile(filePath);
    if (category) {
      await moveFileToCategory(filePath, category);
    }
  } catch (error) {
    console.error(`Error processing ${filePath}: ${error.message}`);
  }
}

// Initialize and start file watching
function initialize() {
  console.log('Initializing Sorting Hat File Organizer...');
  
  // Ensure all folders exist
  ensureFolders();
  
  // Build ignore patterns for special Windows folders
  const ignoredFolders = config.ignoreFolders.map(folder => 
    new RegExp(`.*\\${path.sep}${folder}(\\${path.sep}.*)?$`, 'i')
  );
  
  // Set up file watcher with improved options
  console.log(`Watching directory: ${config.sourceDir}`);
  const watcher = chokidar.watch(config.sourceDir, {
    ignored: [
      /(^|[\/\\])\../, // ignore hidden files
      ...ignoredFolders  // ignore special Windows folders
    ],
    persistent: true,
    ignorePermissionErrors: true, // Ignore permission errors
    awaitWriteFinish: {           // Wait until file writing is complete
      stabilityThreshold: 2000,
      pollInterval: 100
    },
    depth: 1 // Only watch the immediate files in the directory, not deep subfolders
  });
  
  // Log watcher events in debug mode
  if (config.debug) {
    watcher
      .on('add', path => console.log(`File added: ${path}`))
      .on('change', path => console.log(`File changed: ${path}`))
      .on('unlink', path => console.log(`File removed: ${path}`));
  }
  
  // File events
  watcher
    .on('add', filePath => {
      // Only process new files, not files that already existed
      processFile(filePath);
    })
    .on('error', error => {
      // More informative error handling
      if (error.code === 'EPERM') {
        console.error(`Permission error: Cannot watch '${error.path}' - This is normal for some system folders.`);
      } else {
        console.error(`Watcher error: ${error.message}`);
      }
    })
    .on('ready', () => console.log('Initial scan complete. Ready for changes'));
  
  console.log('File Organizer started successfully');
  
  // Return the watcher so it can be closed if needed
  return watcher;
}

// Start the file organizer
initialize();

// Handle graceful shutdown
process.on('SIGINT', () => {
  console.log('Shutting down file organizer...');
  process.exit(0);
});
