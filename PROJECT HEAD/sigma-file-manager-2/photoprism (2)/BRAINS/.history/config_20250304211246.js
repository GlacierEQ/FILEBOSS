/**
 * Configuration for Sorting Hat System Optimizer
 */
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

module.exports = config;
