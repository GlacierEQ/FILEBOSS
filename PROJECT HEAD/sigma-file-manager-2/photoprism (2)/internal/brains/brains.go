package brains

import (
	"fmt"
	"os"
	"path/filepath"
	"runtime"
	"sync"
	"time"

	"github.com/photoprism/photoprism/internal/config"
	"github.com/photoprism/photoprism/internal/entity"
	"github.com/photoprism/photoprism/internal/event"
	"github.com/photoprism/photoprism/internal/query"
	"github.com/photoprism/photoprism/pkg/fs"
)

// Log outputs messages to log.
var Log = event.Log

// Brains represents the main BRAINS service for enhanced photo analysis.
type Brains struct {
	conf          *config.Config
	modelPath     string
	cachePath     string
	initialized   bool
	modelVersions map[string]string
	batchSize     int
	mutex         sync.Mutex
	processors    map[string]Processor
	capabilities  map[string]bool
	cache         *Cache
	db            *entity.Db
	query         *query.Query
	scheduler     *Scheduler // Added scheduler for automation
}

// New returns a new BRAINS instance.
func New(conf *config.Config) *Brains {
	cachePath := filepath.Join(conf.CachePath(), "brains")
	
	b := &Brains{
		conf:          conf,
		modelPath:     filepath.Join(conf.AssetsPath(), "brains"),
		cachePath:     cachePath,
		initialized:   false,
		batchSize:     calculateOptimalBatchSize(),
		processors:    make(map[string]Processor),
		capabilities:  make(map[string]bool),
		modelVersions: make(map[string]string),
		cache:         NewCache(cachePath),
	}

	return b
}

// calculateOptimalBatchSize determines batch size based on available resources.
func calculateOptimalBatchSize() int {
	cpuCores := runtime.NumCPU()
	
	// Base batch size on available CPU cores
	if cpuCores <= 2 {
		return 8 // Small batch for limited resources
	} else if cpuCores <= 4 {
		return 16 // Medium batch for average systems
	} else {
		return 32 // Larger batch for high-performance systems
	}
}

// Init initializes the BRAINS service and loads models.
func (b *Brains) Init() error {
	b.mutex.Lock()
	defer b.mutex.Unlock()

	if b.initialized {
		return nil
	}

	Log.Info("brains: initializing enhanced neural processing")

	// Check if BRAINS model directory exists
	if !fs.DirectoryExists(b.modelPath) {
		return fmt.Errorf("brains: model directory not found at %s", b.modelPath)
	}

	// Initialize database connection
	b.db = entity.Db()
	b.query = query.New(b.db)

	// Check and create database table if needed
	if err := b.db.AutoMigrate(&entity.BrainsResult{}).Error; err != nil {
		return fmt.Errorf("brains: failed to migrate database schema: %v", err)
	}

	// Load model versions
	if err := b.loadModelVersions(); err != nil {
		Log.Warnf("brains: failed to load model versions: %v", err)
	}

	// Initialize processors
	if err := b.initProcessors(); err != nil {
		return fmt.Errorf("brains: failed to initialize processors: %v", err)
	}

	b.initialized = true
	Log.Info("brains: initialization complete")

	return nil
}

// StartScheduler initializes and starts the automated scheduler.
func (b *Brains) StartScheduler() error {
	if !b.initialized {
		if err := b.Init(); err != nil {
			return err
		}
	}

	// Create and start scheduler if not already running
	if b.scheduler == nil {
		b.scheduler = NewScheduler(b, b.query)
	}
	
	return b.scheduler.Start()
}

// StopScheduler stops the automated scheduler.
func (b *Brains) StopScheduler() {
	if b.scheduler != nil {
		b.scheduler.Stop()
	}
}

// SetSchedulerInterval adjusts the scheduler interval.
func (b *Brains) SetSchedulerInterval(interval time.Duration) {
	if b.scheduler != nil {
		b.scheduler.SetInterval(interval)
	}
}

// GetSchedulerInfo returns scheduler status information.
func (b *Brains) GetSchedulerInfo() map[string]interface{} {
	if b.scheduler == nil {
		return map[string]interface{}{
			"running": false,
		}
	}
	
	return b.scheduler.GetInfo()
}

// AutoCurateCollections triggers automatic creation of AI-curated collections.
func (b *Brains) AutoCurateCollections() ([]*entity.Album, error) {
	if !b.initialized {
		if err := b.Init(); err != nil {
			return nil, err
		}
	}
	
	curator := NewCurator(b.db)
	return curator.CurateAllCollections()
}

// loadModelVersions reads model version information from version files.
func (b *Brains) loadModelVersions() error {
	versionFile := filepath.Join(b.modelPath, "version.txt")
	
	if !fs.FileExists(versionFile) {
		return fmt.Errorf("version file not found")
	}
	
	data, err := os.ReadFile(versionFile)
	if err != nil {
		return err
	}
	
	b.modelVersions["main"] = string(data)
	
	// Try loading individual model versions
	modelTypes := []string{"object", "aesthetic", "scene"}
	
	for _, modelType := range modelTypes {
		versionFile := filepath.Join(b.modelPath, modelType, "version.txt")
		if fs.FileExists(versionFile) {
			if data, err := os.ReadFile(versionFile); err == nil {
				b.modelVersions[modelType] = string(data)
			}
		}
	}
	
	return nil
}

// initProcessors sets up the different BRAINS processors.
func (b *Brains) initProcessors() error {
	// Initialize object detection processor
	objectProcessor, err := NewObjectProcessor(b.conf, b.modelPath)
	if err != nil {
		return err
	}
	b.processors["object"] = objectProcessor
	b.capabilities["object_detection"] = true

	// Initialize aesthetic scoring processor
	aestheticProcessor, err := NewAestheticProcessor(b.conf, b.modelPath)
	if err != nil {
		return err
	}
	b.processors["aesthetic"] = aestheticProcessor
	b.capabilities["aesthetic_scoring"] = true

	// Initialize scene understanding processor
	sceneProcessor, err := NewSceneProcessor(b.conf, b.modelPath)
	if err != nil {
		return err
	}
	b.processors["scene"] = sceneProcessor
	b.capabilities["scene_understanding"] = true

	return nil
}

// ProcessFiles analyzes a batch of files using the BRAINS neural system.
func (b *Brains) ProcessFiles(files []string) (*ProcessingResults, error) {
	if !b.initialized {
		if err := b.Init(); err != nil {
			return nil, err
		}
	}

	Log.Infof("brains: processing %d files", len(files))
	
	results := NewProcessingResults()
	
	// Process files in batches
	for i := 0; i < len(files); i += b.batchSize {
		end := i + b.batchSize
		if end > len(files) {
			end = len(files)
		}
		
		batch := files[i:end]
		batchResults, err := b.processBatch(batch)
		if err != nil {
			Log.Errorf("brains: error processing batch: %v", err)
			continue
		}
		
		results.Merge(batchResults)
	}
	
	return results, nil
}

// ProcessFile analyzes a single file and returns the results.
// It uses caching to avoid unnecessary reprocessing.
func (b *Brains) ProcessFile(filePath string) (*FileResult, error) {
	if !b.initialized {
		if err := b.Init(); err != nil {
			return nil, err
		}
	}

	// Check cache first
	if cached, ok := b.cache.Get(filePath); ok {
		for _, file := range cached.Files {
			if file.Path == filePath {
				return file, nil
			}
		}
	}

	// Process file
	results, err := b.ProcessFiles([]string{filePath})
	if err != nil {
		return nil, err
	}

	if len(results.Files) == 0 {
		return nil, fmt.Errorf("no results generated for file")
	}

	// Cache results
	if err := b.cache.Set(filePath, results); err != nil {
		Log.Warnf("brains: failed to cache results: %v", err)
	}

	// Save to database
	if err := b.saveResultsToDatabase(results); err != nil {
		Log.Warnf("brains: failed to save results to database: %v", err)
	}

	return results.Files[0], nil
}

// saveResultsToDatabase stores the processing results in the database.
func (b *Brains) saveResultsToDatabase(results *ProcessingResults) error {
	for _, fileResult := range results.Files {
		// Get photo ID from path
		fileName := filepath.Base(fileResult.Path)
		var photoID string
		
		if photo, err := b.query.PhotoByName(fileName); err == nil {
			photoID = photo.ID
		} else {
			Log.Warnf("brains: couldn't find photo ID for %s: %v", fileName, err)
			continue
		}
		
		// Create or update BRAINS result
		brainsResult, err := entity.GetOrCreateBrainsResult(photoID)
		if err != nil {
			Log.Errorf("brains: failed to get/create result entity: %v", err)
			continue
		}

		// Update result with new data
		if aesthetic, ok := fileResult.Results["aesthetic"].(AestheticResult); ok {
			brainsResult.AestheticScore = aesthetic.Score
			brainsResult.Composition = aesthetic.Composition
			brainsResult.Contrast = aesthetic.Contrast
			brainsResult.Exposure = aesthetic.Exposure
			brainsResult.ColorHarmony = aesthetic.ColorHarmony
		}
		
		if scene, ok := fileResult.Results["scene"].(SceneResult); ok {
			brainsResult.SceneType = scene.SceneType
			brainsResult.IndoorOutdoor = scene.IndoorOutdoor
			brainsResult.TimeOfDay = scene.TimeOfDay
			brainsResult.Weather = scene.Weather
			brainsResult.Keywords = strings.Join(scene.Keywords, ",")
			
			// Sort keywords alphabetically for consistent searching
			sorted := append([]string{}, scene.Keywords...)
			sort.Strings(sorted)
			brainsResult.KeywordsSorted = strings.Join(sorted, ",")
			
			// Save emotions as JSON
			if len(scene.Emotions) > 0 {
				if emotionsJSON, err := json.Marshal(scene.Emotions); err == nil {
					brainsResult.Emotions = string(emotionsJSON)
				}
			}
		}
		
		if object, ok := fileResult.Results["object"].(ObjectResult); ok {
			if objectJSON, err := json.Marshal(object.Objects); err == nil {
				brainsResult.ObjectResults = string(objectJSON)
			}
		}
		
		// Update processing time
		brainsResult.ProcessedAt = sql.NullTime{Time: time.Now(), Valid: true}
		
		// Save to database
		if err := brainsResult.Save(); err != nil {
			Log.Errorf("brains: failed to save result to database: %v", err)
			continue
		}
	}
	
	return nil
}

// processBatch handles processing of a single batch of files.
func (b *Brains) processBatch(batch []string) (*ProcessingResults, error) {
	results := NewProcessingResults()
	
	var wg sync.WaitGroup
	resultsMutex := sync.Mutex{}
	errors := make([]error, 0)
	errorsMutex := sync.Mutex{}
	
	// Enhanced: Use adaptive concurrency based on system resources
	maxConcurrent := runtime.NumCPU()
	if maxConcurrent > 4 {
		// Use 75% of available cores for batch processing
		maxConcurrent = int(float64(maxConcurrent) * 0.75)
	}
	
	// Use a semaphore to limit concurrency
	sem := make(chan bool, maxConcurrent)
	
	// Process each file in the batch with controlled concurrency
	for _, filePath := range batch {
		wg.Add(1)
		sem <- true // Acquire semaphore
		
		go func(path string) {
			defer func() {
				<-sem // Release semaphore
				
				if r := recover(); r != nil {
					Log.Errorf("brains: panic recovered when processing %s: %v", path, r)
					debug.PrintStack()
				}
				
				wg.Done()
			}()
			
			// Skip if file doesn't exist
			if !fs.FileExists(path) {
				Log.Warnf("brains: file not found: %s", path)
				return
			}
			
			// Check cache first
			if cached, ok := b.cache.Get(path); ok {
				for _, file := range cached.Files {
					if file.Path == path {
						resultsMutex.Lock()
						results.Files = append(results.Files, file)
						resultsMutex.Unlock()
						return
					}
				}
			}
			
			// Process with each available processor
			fileResults := NewFileResult(path)
			
			for name, processor := range b.processors {
				// Skip disabled processors
				if !b.conf.BrainsCapabilities()[name+"_detection"] && 
				   !b.conf.BrainsCapabilities()[name+"_scoring"] && 
				   !b.conf.BrainsCapabilities()[name+"_understanding"] {
					continue
				}
				
				processorResults, err := processor.Process(path)
				if err != nil {
					Log.Warnf("brains: %s processor failed for %s: %v", name, path, err)
					errorsMutex.Lock()
					errors = append(errors, fmt.Errorf("processing %s with %s: %v", path, name, err))
					errorsMutex.Unlock()
					continue
				}
				
				fileResults.Results[name] = processorResults
			}
			
			// Add to overall results
			resultsMutex.Lock()
			results.Files = append(results.Files, fileResults)
			resultsMutex.Unlock()
			
		}(filePath)
	}
	
	wg.Wait()
	
	// Return first error if any occurred
	if len(errors) > 0 {
		return results, errors[0]
	}
	
	return results, nil
}

// HasCapability checks if a specific capability is available.
func (b *Brains) HasCapability(name string) bool {
	if !b.initialized {
		_ = b.Init()
	}
	
	return b.capabilities[name]
}

// GetProcessor returns a specific processor by name.
func (b *Brains) GetProcessor(name string) (Processor, bool) {
	if !b.initialized {
		_ = b.Init()
	}
	
	proc, ok := b.processors[name]
	return proc, ok
}

// GetModelVersion returns the version of the specified model.
func (b *Brains) GetModelVersion(modelType string) string {
	if !b.initialized {
		_ = b.Init()
	}
	
	if version, ok := b.modelVersions[modelType]; ok {
		return version
	}
	
	return "unknown"
}

// CheckForModelUpdates checks if model updates are available.
func (b *Brains) CheckForModelUpdates() (bool, error) {
	// This would typically check a remote server for updates
	// For now, just return a placeholder implementation
	return false, nil
}

// UpdateModels downloads and installs updated BRAINS models.
func (b *Brains) UpdateModels() error {
	scriptPath := filepath.Join(b.conf.AppPath(), "scripts", "download-brains.sh")
	if (!fs.FileExists(scriptPath)) {
		return fmt.Errorf("download script not found: %s", scriptPath)
	}
	
	if err := fs.Shell("bash", scriptPath); err != nil {
		return fmt.Errorf("failed to update models: %v", err)
	}
	
	// Reload model versions
	if err := b.loadModelVersions(); err != nil {
		Log.Warnf("brains: failed to reload model versions: %v", err)
	}
	
	return nil
}

// ClearCache clears the BRAINS cache.
func (b *Brains) ClearCache() error {
	return b.cache.ClearAll()
}
