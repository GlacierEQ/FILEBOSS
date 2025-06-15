ok im going to list everything that even might be helpful

C:\Users\casey\OneDrive\Documents\GitHub\AI-Automation

C:\Users\casey\OneDrive\Documents\GitHub\aide

C:\Users\casey\OneDrive\Documents\GitHub\AIQuickFix

C:\Users\casey\OneDrive\Documents\GitHub\ai-renamer

C:\Users\casey\OneDrive\Documents\GitHub\Autogen_GraphRAG_Ollama

C:\Users\casey\OneDrive\Documents\GitHub\DeveMultiCompressor

C:\Users\casey\OneDrive\Documents\GitHub\docling

C:\Users\casey\OneDrive\Documents\GitHub\Files

C:\Users\casey\OneDrive\Documents\GitHub\fpdf

C:\Users\casey\OneDrive\Documents\GitHub\gpt4all

C:\Users\casey\OneDrive\Documents\GitHub\granite-3.0-language-models

C:\Users\casey\OneDrive\Documents\GitHub\granite-retrieval-agent

C:\Users\casey\OneDrive\Documents\GitHub\HydraDragonAntivirus

C:\Users\casey\OneDrive\Documents\GitHub\intel-npu-acceleration-library

C:\Users\casey\OneDrive\Documents\GitHub\lawglance

C:\Users\casey\OneDrive\Documents\GitHub\Legal-AI_Project

C:\Users\casey\OneDrive\Documents\GitHub\llama-coder

C:\Users\casey\OneDrive\Documents\GitHub\llama-fs

C:\Users\casey\OneDrive\Documents\GitHub\Local-File-Organizer

C:\Users\casey\OneDrive\Documents\GitHub\Mobile-Security-Framework-MobSF

C:\Users\casey\OneDrive\Documents\GitHub\ninja

C:\Users\casey\OneDrive\Documents\GitHub\ollama

C:\Users\casey\OneDrive\Documents\GitHub\Ollama Mega Resear

C:\Users\casey\OneDrive\Documents\GitHub\ollama-deep-research

C:\Users\casey\OneDrive\Documents\GitHub\organize

C:\Users\casey\OneDrive\Documents\GitHub\overleaf

C:\Users\casey\OneDrive\Documents\GitHub\peft

C:\Users\casey\OneDrive\Documents\GitHub\photoprism

C:\Users\casey\OneDrive\Documents\GitHub\photoprism2

C:\Users\casey\OneDrive\Documents\GitHub\php-dumper-docker-extension

C:\Users\casey\OneDrive\Documents\GitHub\piper

C:\Users\casey\OneDrive\Documents\GitHub\scrapy

C:\Users\casey\OneDrive\Documents\GitHub\selenium

C:\Users\casey\OneDrive\Documents\GitHub\self-operating-computer

C:\Users\casey\OneDrive\Documents\GitHub\tensor2tensor

C:\Users\casey\OneDrive\Documents\GitHub\tensorflow

C:\Users\casey\OneDrive\Documents\GitHub\terminal-gui-designer

C:\Users\casey\OneDrive\Documents\GitHub\TextCraft

C:\Users\casey\OneDrive\Documents\GitHub\toolkit

C:\Users\casey\OneDrive\Documents\GitHub\undetected-chromedriver

C:\Users\casey\OneDrive\Documents\GitHub\univer

C:\Users\casey\OneDrive\Documents\GitHub\VSCode

C:\Users\casey\OneDrive\Documents\GitHub\vscode2

C:\Users\casey\OneDrive\Documents\GitHub\Web-Scraping

C:\Users\casey\OneDrive\Documents\GitHub\whisper

C:\Users\casey\OneDrive\Documents\GitHub\whisperX

C:\Users\casey\OneDrive\Documents\GitHub\xcode-configure

C:\Users\casey\OneDrive\Documents\GitHub\aAzel-LexAI-main.zip

C:\Users\casey\OneDrive\Documents\GitHub\autopsy-develop.zip

C:\Users\casey\OneDrive\Documents\GitHub\JudgerAI-main.zip

C:\Users\casey\OneDrive\Documents\GitHub\sleuthkit-develop.zip/**
 * Advanced Content Analysis for Sorting Hat
 * Provides enhanced file type detection and content extraction
 */
const fs = require('fs');
const path = require('path');
const { promisify } = require('util');
const { spawn } = require('child_process');
const crypto = require('crypto');

// Promisified fs functions
const fsReadFile = promisify(fs.readFile);

class ContentAnalyzer {
  constructor(config = {}) {
    this.config = {
      tempDir: path.join('C:/SORTING HAT/BRAINS', 'temp'),
      externalTools: {
        pdfToText: path.join('C:/SORTING HAT/BRAINS', 'tools', 'pdftotext.exe'),
        imageOcr: path.join('C:/SORTING HAT/BRAINS', 'tools', 'tesseract.exe'),
        officeConverter: path.join('C:/SORTING HAT/BRAINS', 'tools', 'textract.exe')
      },
      cacheResults: true,
      cacheDir: path.join('C:/SORTING HAT/BRAINS', 'cache', 'content-analysis'),
      cacheTTL: 7 * 24 * 60 * 60 * 1000, // 7 days
      ...config
    };
    
    // Create required directories
    [this.config.tempDir, this.config.cacheDir].forEach(dir => {
      if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true });
      }
    });
    
    // Initialize file type analyzers
    this.fileTypeAnalyzers = {
      '.txt': this.extractFromText.bind(this),
      '.md': this.extractFromText.bind(this),
      '.csv': this.extractFromText.bind(this),
      '.json': this.extractFromJson.bind(this),
      '.pdf': this.extractFromPdf.bind(this),
      '.doc': this.extractFromOffice.bind(this),
      '.docx': this.extractFromOffice.bind(this),
      '.xls': this.extractFromOffice.bind(this),
      '.xlsx': this.extractFromOffice.bind(this),
      '.ppt': this.extractFromOffice.bind(this),
      '.pptx': this.extractFromOffice.bind(this),
      '.jpg': this.extractFromImage.bind(this),
      '.jpeg': this.extractFromImage.bind(this),
      '.png': this.extractFromImage.bind(this),
      '.gif': this.extractFromImage.bind(this),
      '.html': this.extractFromHtml.bind(this),
      '.htm': this.extractFromHtml.bind(this)
    };
  }
  
  /**
   * Generate file hash for caching
   * @param {string} filePath - Path to file
   * @returns {Promise<string>} - File hash
   */
  async getFileHash(filePath) {
    try {
      const fileContent = await fsReadFile(filePath);
      return crypto.createHash('md5').update(fileContent).digest('hex');
    } catch (error) {
      console.error(`Error generating file hash: ${error.message}`);
      return null;
    }
  }
  
  /**
   * Check if cached analysis exists and is valid
   * @param {string} filePath - Path to file
   * @returns {Promise<Object|null>} - Cached analysis or null
   */
  async getCachedAnalysis(filePath) {
    if (!this.config.cacheResults) return null;
    
    try {
      const fileHash = await this.getFileHash(filePath);
      if (!fileHash) return null;
      
      const cacheFilePath = path.join(this.config.cacheDir, `${fileHash}.json`);
      
      if (fs.existsSync(cacheFilePath)) {
        const cacheData = JSON.parse(await fsReadFile(cacheFilePath, 'utf8'));
        
        // Check if cache is still valid
        const cacheAge = Date.now() - new Date(cacheData.timestamp).getTime();
        if (cacheAge < this.config.cacheTTL) {
          return cacheData;
        }
      }
    } catch (error) {
      console.error(`Error reading cached analysis: ${error.message}`);
    }
    
    return null;
  }
  
  /**
   * Save analysis to cache
   * @param {string} filePath - Path to file
   * @param {Object} analysis - Analysis results
   */
  async cacheAnalysis(filePath, analysis) {
    if (!this.config.cacheResults) return;
    
    try {
      const fileHash = await this.getFileHash(filePath);
      if (!fileHash) return;
      
      const cacheData = {
        ...analysis,
        timestamp: new Date().toISOString(),
        filePath: filePath,
        fileHash: fileHash
      };
      
      const cacheFilePath = path.join(this.config.cacheDir, `${fileHash}.json`);
      await fs.promises.writeFile(cacheFilePath, JSON.stringify(cacheData, null, 2));
    } catch (error) {
      console.error(`Error caching analysis: ${error.message}`);
    }
  }
  
  /**
   * Analyze file content
   * @param {string} filePath - Path to file
   * @returns {Promise<Object>} - Analysis results
   */
  async analyzeFile(filePath) {
    try {
      // Check cache first
      const cachedResult = await this.getCachedAnalysis(filePath);
      if (cachedResult) {
        return cachedResult;
      }
      
      const fileExt = path.extname(filePath).toLowerCase();
      const fileName = path.basename(filePath);
      
      // Default analysis result
      let analysis = {
        fileName: fileName,
        extension: fileExt,
        type: 'unknown',
        textContent: '',
        keywords: [],
        detectedLanguage: 'unknown',
        metadata: {}
      };
      
      // Use the appropriate analyzer based on file extension
      const analyzer = this.fileTypeAnalyzers[fileExt];
      if (analyzer) {
        const extractedData = await analyzer(filePath);
        
        // Merge extracted data with the default analysis
        analysis = {
          ...analysis,
          ...extractedData
        };
      } else {
        // Handle unknown file types
        analysis.textContent = fileName; // Use filename as content
      }
      
      // Extract keywords
      analysis.keywords = this.extractKeywords(