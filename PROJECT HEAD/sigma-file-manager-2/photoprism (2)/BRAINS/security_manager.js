/**
 * Security Manager for Sorting Hat
 * Provides enhanced security features, access control, and file validation
 */
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

class SecurityManager {
  constructor(config = {}) {
    this.config = {
      programDir: 'C:/SORTING HAT/BRAINS',
      safelistedExtensions: [
        '.txt', '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
        '.jpg', '.jpeg', '.png', '.gif', '.mp3', '.mp4', '.wav', '.zip',
        '.csv', '.json', '.xml', '.html', '.js', '.py', '.css', '.md'
      ],
      blockedPatterns: [
        /\.exe$/i, /\.bat$/i, /\.cmd$/i, /\.vbs$/i, /\.ps1$/i,
        /\.dll$/i, /\.sys$/i, /\.msi$/i, /\.com$/i, /\.scr$/i
      ],
      maxFileSize: 500 * 1024 * 1024, // 500MB
      allowedCharactersRegex: /^[a-zA-Z0-9_\-. ()[\]{}]+$/,  // Safe filename characters
      ...config
    };
    
    // Initialize log file
    this.logDir = path.join(this.config.programDir, 'logs', 'security');
    if (!fs.existsSync(this.logDir)) {
      fs.mkdirSync(this.logDir, { recursive: true });
    }
  }

  /**
   * Validates if a file is safe to process
   * @param {string} filePath - Path to the file
   * @returns {Object} - Validation result {safe: boolean, reason: string}
   */
  validateFile(filePath) {
    try {
      // Check if file exists
      if (!fs.existsSync(filePath)) {
        return { safe: false, reason: 'File does not exist' };
      }
      
      const stats = fs.statSync(filePath);
      const fileName = path.basename(filePath);
      const fileExt = path.extname(filePath).toLowerCase();
      
      // Check if it's a directory
      if (stats.isDirectory()) {
        return { safe: true, reason: 'Is a directory' };
      }
      
      // Check file size
      if (stats.size > this.config.maxFileSize) {
        this.logSecurityEvent('size_violation', filePath, `File exceeds max size: ${stats.size} bytes`);
        return { 
          safe: false, 
          reason: `File too large (${Math.round(stats.size / 1024 / 1024)}MB > ${Math.round(this.config.maxFileSize / 1024 / 1024)}MB)` 
        };
      }
      
      // Check extension against safelist
      if (!this.config.safelistedExtensions.includes(fileExt) && fileExt !== '') {
        this.logSecurityEvent('extension_blocked', filePath, `Blocked extension: ${fileExt}`);
        return { safe: false, reason: `File type not allowed: ${fileExt}` };
      }
      
      // Check against blocked patterns
      for (const pattern of this.config.blockedPatterns) {
        if (pattern.test(fileName)) {
          this.logSecurityEvent('pattern_blocked', filePath, `Blocked pattern: ${pattern}`);
          return { safe: false, reason: 'Potentially unsafe file pattern' };
        }
      }
      
      // Check filename for unsafe characters (path traversal prevention)
      if (!this.config.allowedCharactersRegex.test(fileName)) {
        this.logSecurityEvent('invalid_chars', filePath, `Invalid characters in filename`);
        return { safe: false, reason: 'Filename contains invalid characters' };
      }

      // File passed all security checks
      return { safe: true, reason: 'Passed all security checks' };
      
    } catch (error) {
      this.logSecurityEvent('validation_error', filePath, error.message);
      return { safe: false, reason: `Error during validation: ${error.message}` };
    }
  }
  
  /**
   * Creates a safe filename by removing unsafe characters
   * @param {string} fileName - Original filename
   * @returns {string} - Sanitized filename
   */
  sanitizeFileName(fileName) {
    // Remove unsafe characters
    let sanitized = fileName.replace(/[^a-zA-Z0-9_\-. ()[\]{}]/g, '_');
    
    // Ensure no duplicate underscores
    sanitized = sanitized.replace(/_{2,}/g, '_');
    
    // Ensure it's not empty
    if (sanitized === '') {
      sanitized = 'file_' + Date.now();
    }
    
    return sanitized;
  }
  
  /**
   * Calculate file hash for integrity checking
   * @param {string} filePath - Path to the file 
   * @returns {string|null} - Hash or null if error
   */
  calculateFileHash(filePath) {
    try {
      const fileBuffer = fs.readFileSync(filePath);
      const hashSum = crypto.createHash('sha256');
      hashSum.update(fileBuffer);
      return hashSum.digest('hex');
    } catch (error) {
      this.logSecurityEvent('hash_error', filePath, error.message);
      return null;
    }
  }
  
  /**
   * Log security events for auditing
   * @param {string} eventType - Type of security event
   * @param {string} filePath - Path to the file involved
   * @param {string} details - Additional details about the event
   */
  logSecurityEvent(eventType, filePath, details) {
    try {
      const timestamp = new Date().toISOString();
      const fileName = path.basename(filePath);
      
      const logEntry = {
        timestamp,
        eventType,
        fileName,
        fileHash: this.calculateFileHash(filePath),
        details
      };
      
      // Write to daily security log
      const today = new Date().toISOString().split('T')[0];
      const logFilePath = path.join(this.logDir, `security-${today}.log`);
      
      fs.appendFileSync(
        logFilePath, 
        JSON.stringify(logEntry) + '\n'
      );
      
      console.log(`Security Event: ${eventType} - ${fileName} - ${details}`);
    } catch (error) {
      console.error(`Failed to log security event: ${error.message}`);
    }
  }
}

module.exports = SecurityManager;
