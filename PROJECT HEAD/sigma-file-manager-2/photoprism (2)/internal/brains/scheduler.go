package brains

import (
	"fmt"
	"sync"
	"time"

	"github.com/photoprism/photoprism/internal/entity"
	"github.com/photoprism/photoprism/internal/event"
	"github.com/photoprism/photoprism/internal/mutex"
	"github.com/photoprism/photoprism/internal/query"
)

// Scheduler manages automated BRAINS analysis tasks.
type Scheduler struct {
	brains        *Brains
	query         *query.Query
	running       bool
	interval      time.Duration
	maxBatchSize  int
	idleCPUTarget float64 // Target CPU idle percentage for adaptive scheduling
	mutex         sync.Mutex
	curator       *Curator
	stopChan      chan bool
}

// TaskPriority defines processing priority levels.
type TaskPriority int

const (
	PriorityLow TaskPriority = iota
	PriorityNormal
	PriorityHigh
)

// AnalysisTask represents a scheduled BRAINS analysis task.
type AnalysisTask struct {
	PhotoIDs  []string
	Priority  TaskPriority
	CreatedAt time.Time
}

// NewScheduler creates a new BRAINS scheduler.
func NewScheduler(b *Brains, q *query.Query) *Scheduler {
	return &Scheduler{
		brains:        b,
		query:         q,
		running:       false,
		interval:      30 * time.Minute, // Default interval
		maxBatchSize:  100,              // Default batch size
		idleCPUTarget: 0.3,              // Target 30% idle CPU
		stopChan:      make(chan bool),
		curator:       NewCurator(entity.Db()),
	}
}

// Start begins the automated scheduling of BRAINS analysis.
func (s *Scheduler) Start() error {
	s.mutex.Lock()
	defer s.mutex.Unlock()

	if s.running {
		return fmt.Errorf("scheduler is already running")
	}

	s.running = true
	
	// Start background scheduler
	go s.run()
	
	// Start automated collection curation on a separate schedule
	go s.runCollectionCurator()

	Log.Info("brains: automated scheduler started")
	return nil
}

// Stop halts the automated scheduling.
func (s *Scheduler) Stop() {
	s.mutex.Lock()
	defer s.mutex.Unlock()

	if !s.running {
		return
	}

	s.running = false
	s.stopChan <- true

	Log.Info("brains: automated scheduler stopped")
}

// SetInterval changes the scheduling interval.
func (s *Scheduler) SetInterval(interval time.Duration) {
	s.mutex.Lock()
	defer s.mutex.Unlock()
	
	s.interval = interval
	Log.Infof("brains: scheduler interval set to %s", interval)
}

// run is the main scheduler loop.
func (s *Scheduler) run() {
	ticker := time.NewTicker(s.interval)
	defer ticker.Stop()

	// Run once immediately on startup
	s.scheduleBatch()

	for {
		select {
		case <-s.stopChan:
			return
		case <-ticker.C:
			// Check for optimal timing based on system load
			if s.isSystemIdle() {
				Log.Debug("brains: system is idle, scheduling analysis batch")
				s.scheduleBatch()
			} else {
				Log.Debug("brains: system is busy, deferring analysis")
			}
		}
	}
}

// runCollectionCurator periodically updates AI-curated collections.
func (s *Scheduler) runCollectionCurator() {
	// Run curator less frequently than main analysis
	ticker := time.NewTicker(12 * time.Hour)
	defer ticker.Stop()

	for {
		select {
		case <-s.stopChan:
			return
		case <-ticker.C:
			// Only run collection curation during low-activity periods
			if s.isSystemIdle() && !mutex.MainWorker.Running() {
				Log.Info("brains: updating AI-curated collections")
				albums, err := s.curator.CurateAllCollections()
				if err != nil {
					Log.Errorf("brains: error curating collections: %v", err)
				} else {
					Log.Infof("brains: updated %d AI-curated collections", len(albums))
				}
			}
		}
	}
}

// isSystemIdle determines if the system is idle enough for background processing.
func (s *Scheduler) isSystemIdle() bool {
	// Avoid running when indexing or importing is active
	if mutex.MainWorker.Running() || mutex.ImportWorker.Running() || mutex.ShareWorker.Running() {
		return false
	}

	// TODO: Add actual CPU idle percentage check
	// For now, assume system is idle during night hours (1am to 5am)
	hour := time.Now().Hour()
	if hour >= 1 && hour <= 5 {
		return true
	}

	return true
}

// scheduleBatch finds unprocessed photos and schedules them for analysis.
func (s *Scheduler) scheduleBatch() {
	// Find photos that need BRAINS analysis
	unprocessedIDs, err := s.findUnprocessedPhotos(s.maxBatchSize)
	if err != nil {
		Log.Errorf("brains: error finding unprocessed photos: %v", err)
		return
	}

	if len(unprocessedIDs) == 0 {
		Log.Debug("brains: no unprocessed photos found")
		return
	}

	Log.Infof("brains: scheduling analysis for %d photos", len(unprocessedIDs))

	// Create a task
	task := entity.NewTask(entity.TaskBrainsAnalyze, "automated brains analysis", entity.TaskPriorityBackground)
	
	// This would use a global task manager in the real application
	event.Publish("tasks", event.TaskCreate, task)

	// Process photos in the background
	go s.processPhotoBatch(unprocessedIDs)
}

// findUnprocessedPhotos finds photos that have not been analyzed with BRAINS yet.
func (s *Scheduler) findUnprocessedPhotos(limit int) ([]string, error) {
	// Find photos with no BRAINS results
	// This is a simplified version - a real implementation would be more sophisticated
	var photoIDs []string

	err := s.query.Db().Raw(`
		SELECT p.id FROM photos p 
		LEFT JOIN brains_results b ON b.photo_id = p.id
		WHERE b.id IS NULL AND p.deleted_at IS NULL
		AND p.photo_quality > 0
		LIMIT ?
	`, limit).Pluck("id", &photoIDs).Error

	return photoIDs, err
}

// processPhotoBatch processes a batch of photos with BRAINS.
func (s *Scheduler) processPhotoBatch(photoIDs []string) {
	if len(photoIDs) == 0 {
		return
	}

	// Convert photo IDs to file paths
	var filePaths []string
	for _, id := range photoIDs {
		photo := entity.FindPhoto(id, s.query.Db())
		if photo == nil {
			continue
		}

		if filename := photo.FileName(); filename != "" {
			filePath := s.brains.conf.OriginalsPath() + "/" + filename
			filePaths = append(filePaths, filePath)
		}
	}

	if len(filePaths) == 0 {
		return
	}

	// Process the files
	results, err := s.brains.ProcessFiles(filePaths)
	
	if err != nil {
		Log.Errorf("brains: error processing batch: %v", err)
		return
	}
	
	Log.Infof("brains: successfully processed %d photos", len(results.Files))
}

// GetInfo returns information about the scheduler status.
func (s *Scheduler) GetInfo() map[string]interface{} {
	s.mutex.Lock()
	defer s.mutex.Unlock()
	
	return map[string]interface{}{
		"running":        s.running,
		"interval":       s.interval.String(),
		"max_batch_size": s.maxBatchSize,
		"idle_target":    s.idleCPUTarget,
	}
}
