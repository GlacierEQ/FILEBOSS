package api

import (
	"net/http"
	"path/filepath"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/photoprism/photoprism/internal/acl"
	"github.com/photoprism/photoprism/internal/brains"
	"github.com/photoprism/photoprism/internal/entity"
	"github.com/photoprism/photoprism/internal/event"
	"github.com/photoprism/photoprism/internal/form"
	"github.com/photoprism/photoprism/internal/get"
	"github.com/photoprism/photoprism/internal/i18n"
	"github.com/photoprism/photoprism/internal/photoprism"
	"github.com/photoprism/photoprism/internal/query"
	"github.com/photoprism/photoprism/pkg/fs"
	"github.com/photoprism/photoprism/pkg/txt"
)

// RegisterBrainsRoutes registers all BRAINS API routes.
func RegisterBrainsRoutes(router *gin.RouterGroup) {
	GetBrainsStatus(router)
	DownloadBrainsModels(router)
	UpdateBrainsModels(router)
	GetBrainsModelVersions(router)
	SetBrainsCapabilities(router)
	GetBrainsCapabilities(router)
	AnalyzeBrainsPhotos(router)
	GetBrainsResults(router)
	GetPhotoAesthetic(router)
	GetPhotoScene(router)
	GetPhotoObjects(router)
	ClearBrainsCache(router)
	// Add new automation routes
	StartBrainsScheduler(router)
	StopBrainsScheduler(router)
	GetBrainsSchedulerStatus(router)
	CurateBrainsCollections(router)
}

// GetBrainsStatus returns the status of BRAINS.
func GetBrainsStatus(router *gin.RouterGroup) {
	router.GET("/api/v1/brains/status", func(c *gin.Context) {
		s := Auth(c, acl.ResourceConfig, acl.ActionRead)

		if !s.Admin() {
			AbortForbidden(c)
			return
		}

		conf := Config(c)

		// Initialize BRAINS to get model versions
		b := brains.New(conf)
		if err := b.Init(); err != nil {
			log.Warnf("brains: failed to initialize: %v", err)
		}

		// Check for pending tasks
		task := get.TaskManager()
		pendingTasks := task.FindPending("brains")

		// Create the response
		result := gin.H{
			"enabled":           conf.BrainsEnabled(),
			"models_downloaded": conf.BrainsModelsDownloaded(),
			"models_path":       conf.BrainsPath(),
			"capabilities":      conf.BrainsCapabilities(),
			"model_versions": gin.H{
				"main":      b.GetModelVersion("main"),
				"object":    b.GetModelVersion("object"),
				"aesthetic": b.GetModelVersion("aesthetic"),
				"scene":     b.GetModelVersion("scene"),
			},
			"pending_tasks": len(pendingTasks),
		}

		c.JSON(http.StatusOK, result)
	})
}

// DownloadBrainsModels initiates a download of BRAINS models.
func DownloadBrainsModels(router *gin.RouterGroup) {
	router.POST("/api/v1/brains/models/download", func(c *gin.Context) {
		s := Auth(c, acl.ResourceConfig, acl.ActionUpdate)

		if !s.Admin() {
			AbortForbidden(c)
			return
		}

		conf := Config(c)

		if !conf.BrainsEnabled() {
			AbortBadRequest(c, i18n.ErrFeatureDisabled)
			return
		}

		// Create a task for model download
		task := get.TaskManager()
		downloadTask := entity.NewTask(entity.TaskBrainsDownload, "download brains models", entity.TaskPriorityHigh)
		task.Start(downloadTask, func(task *entity.Task) {
			task.SetStatus(entity.TaskStatusRunning)
			scriptPath := filepath.Join(conf.AppPath(), "scripts", "download-brains.sh")
			
			if !fs.FileExists(scriptPath) {
				task.SetStatus(entity.TaskStatusError)
				task.SetErrorMessage("download script not found")
				return
			}
			
			if err := fs.Shell("bash", scriptPath); err != nil {
				task.SetStatus(entity.TaskStatusError)
				task.SetErrorMessage(err.Error())
				return
			}
			
			task.SetStatus(entity.TaskStatusCompleted)
		})

		c.JSON(http.StatusOK, gin.H{
			"message": i18n.Msg(i18n.MsgTaskStarted),
			"task_id": downloadTask.ID,
		})
	})
}

// UpdateBrainsModels checks for and downloads updated BRAINS models.
func UpdateBrainsModels(router *gin.RouterGroup) {
	router.POST("/api/v1/brains/models/update", func(c *gin.Context) {
		s := Auth(c, acl.ResourceConfig, acl.ActionUpdate)

		if !s.Admin() {
			AbortForbidden(c)
			return
		}

		conf := Config(c)

		if !conf.BrainsEnabled() {
			AbortBadRequest(c, i18n.ErrFeatureDisabled)
			return
		}

		// Initialize BRAINS
		b := brains.New(conf)
		if err := b.Init(); err != nil {
			AbortSaveFailed(c, i18n.ErrUnexpected)
			return
		}

		// Check for updates
		hasUpdates, err := b.CheckForModelUpdates()
		if err != nil {
			AbortSaveFailed(c, i18n.ErrUnexpected)
			return
		}

		if !hasUpdates {
			c.JSON(http.StatusOK, gin.H{
				"message": "models already up-to-date",
				"updated": false,
			})
			return
		}

		// Create a task for model update
		task := get.TaskManager()
		updateTask := entity.NewTask(entity.TaskBrainsUpdate, "update brains models", entity.TaskPriorityHigh)
		task.Start(updateTask, func(task *entity.Task) {
			task.SetStatus(entity.TaskStatusRunning)
			
			if err := b.UpdateModels(); err != nil {
				task.SetStatus(entity.TaskStatusError)
				task.SetErrorMessage(err.Error())
				return
			}
			
			task.SetStatus(entity.TaskStatusCompleted)
		})

		c.JSON(http.StatusOK, gin.H{
			"message": i18n.Msg(i18n.MsgTaskStarted),
			"task_id": updateTask.ID,
			"updated": true,
		})
	})
}

// GetBrainsModelVersions returns information about installed model versions.
func GetBrainsModelVersions(router *gin.RouterGroup) {
	router.GET("/api/v1/brains/models/versions", func(c *gin.Context) {
		s := Auth(c, acl.ResourceConfig, acl.ActionRead)

		if !s.Admin() {
			AbortForbidden(c)
			return
		}

		conf := Config(c)

		if !conf.BrainsEnabled() {
			AbortBadRequest(c, i18n.ErrFeatureDisabled)
			return
		}

		// Initialize BRAINS
		b := brains.New(conf)
		if err := b.Init(); err != nil {
			AbortSaveFailed(c, i18n.ErrUnexpected)
			return
		}

		c.JSON(http.StatusOK, gin.H{
			"main":      b.GetModelVersion("main"),
			"object":    b.GetModelVersion("object"),
			"aesthetic": b.GetModelVersion("aesthetic"),
			"scene":     b.GetModelVersion("scene"),
		})
	})
}

// SetBrainsCapabilities updates BRAINS capability settings.
func SetBrainsCapabilities(router *gin.RouterGroup) {
	router.POST("/api/v1/brains/capabilities", func(c *gin.Context) {
		s := Auth(c, acl.ResourceConfig, acl.ActionUpdate)

		if !s.Admin() {
			AbortForbidden(c)
			return
		}

		conf := Config(c)

		if !conf.BrainsEnabled() {
			AbortBadRequest(c, i18n.ErrFeatureDisabled)
			return
		}

		var capabilities map[string]bool
		if err := c.BindJSON(&capabilities); err != nil {
			AbortBadRequest(c, txt.UcFirst(err.Error()))
			return
		}

		// Update capabilities in settings
		settings := conf.Settings()
		settings.SetBrainsCapability("object_detection", capabilities["object_detection"])
		settings.SetBrainsCapability("aesthetic_scoring", capabilities["aesthetic_scoring"])
		settings.SetBrainsCapability("scene_understanding", capabilities["scene_understanding"])

		// Save settings
		if err := settings.Save(); err != nil {
			AbortSaveFailed(c, i18n.ErrUnexpected)
			return
		}

		// Return updated capabilities
		c.JSON(http.StatusOK, gin.H{
			"capabilities": conf.BrainsCapabilities(),
		})
	})
}

// GetBrainsCapabilities returns the current BRAINS capability settings.
func GetBrainsCapabilities(router *gin.RouterGroup) {
	router.GET("/api/v1/brains/capabilities", func(c *gin.Context) {
		s := Auth(c, acl.ResourceConfig, acl.ActionRead)

		if !s.Admin() {
			AbortForbidden(c)
			return
		}

		conf := Config(c)

		c.JSON(http.StatusOK, gin.H{
			"capabilities": conf.BrainsCapabilities(),
		})
	})
}

// AnalyzePhotoRequest contains parameters for analyzing a photo.
type AnalyzePhotoRequest struct {
	PhotoID string   `json:"photo_id"`
	PhotoIDs []string `json:"photo_ids"`
	Type     string   `json:"type"`
	Force    bool     `json:"force"`
}

// AnalyzeBrainsPhotos runs BRAINS analysis on photos.
func AnalyzeBrainsPhotos(router *gin.RouterGroup) {
	router.POST("/api/v1/brains/analyze", func(c *gin.Context) {
		s := Auth(c, acl.ResourcePhotos, acl.ActionUpdate)

		conf := Config(c)

		if !conf.BrainsEnabled() {
			AbortBadRequest(c, i18n.ErrFeatureDisabled)
			return
		}

		if !conf.BrainsModelsDownloaded() {
			AbortBadRequest(c, i18n.ErrModelNotFound)
			return
		}

		// Parse request
		var req AnalyzePhotoRequest
		if err := c.BindJSON(&req); err != nil {
			AbortBadRequest(c, txt.UcFirst(err.Error()))
			return
		}

		// Validate request
		if req.Type == "" {
			req.Type = "all"
		}

		// Handle single photo ID
		if req.PhotoID != "" && len(req.PhotoIDs) == 0 {
			req.PhotoIDs = []string{req.PhotoID}
		}

		// Handle scope based analysis if no specific photos provided
		if len(req.PhotoIDs) == 0 {
			// Create a task for analyzing all photos
			task := get.TaskManager()
			analyzeTask := entity.NewTask(entity.TaskBrainsAnalyze, "analyze photos with brains", entity.TaskPriorityHigh)
			task.Start(analyzeTask, func(task *entity.Task) {
				task.SetStatus(entity.TaskStatusRunning)
				
				// Get database connection and query client
				db := conf.Db()
				q := query.New(db)
				
				// Get photos to analyze (limited to 1000 for performance)
				photos, err := q.RecentPhotos(1000)
				if err != nil {
					task.SetStatus(entity.TaskStatusError)
					task.SetErrorMessage(err.Error())
					return
				}
				
				// Initialize BRAINS
				b := brains.New(conf)
				if err := b.Init(); err != nil {
					task.SetStatus(entity.TaskStatusError)
					task.SetErrorMessage(err.Error())
					return
				}
				
				// Create a list of file paths
				var files []string
				for _, photo := range photos {
					if filename := photo.FileName(); filename != "" {
						files = append(files, filepath.Join(conf.OriginalsPath(), filename))
					}
					
					// Update progress
					progress := float64(len(files)) / float64(len(photos)) * 100
					task.SetProgressPercent(int(progress))
				}
				
				// Process files
				_, err = b.ProcessFiles(files)
				
				if err != nil {
					task.SetStatus(entity.TaskStatusError)
					task.SetErrorMessage(err.Error())
					return
				}
				
				task.SetStatus(entity.TaskStatusCompleted)
			})

			c.JSON(http.StatusOK, gin.H{
				"message": i18n.Msg(i18n.MsgTaskStarted),
				"task_id": analyzeTask.ID,
			})
			return
		}

		// Handle specific photo IDs
		photoUids := req.PhotoIDs

		// Create a task for analyzing specific photos
		task := get.TaskManager()
		analyzeTask := entity.NewTask(entity.TaskBrainsAnalyze, "analyze specific photos with brains", entity.TaskPriorityHigh)
		task.Start(analyzeTask, func(task *entity.Task) {
			task.SetStatus(entity.TaskStatusRunning)
			
			// Initialize BRAINS
			b := brains.New(conf)
			if err := b.Init(); err != nil {
				task.SetStatus(entity.TaskStatusError)
				task.SetErrorMessage(err.Error())
				return
			}
			
			// Get database connection and query client
			db := conf.Db()
			q := query.New(db)
			
			var files []string
			
			// Process each photo ID
			for i, uid := range photoUids {
				photo, err := q.PhotoByUID(uid)
				if err != nil {
					continue
				}
				
				if filename := photo.FileName(); filename != "" {
					filePath := filepath.Join(conf.OriginalsPath(), filename)
					files = append(files, filePath)
				}
				
				// Update progress
				progress := float64(i+1) / float64(len(photoUids)) * 100
				task.SetProgressPercent(int(progress))
			}
			
			// Process files
			_, err := b.ProcessFiles(files)
			
			if err != nil {
				task.SetStatus(entity.TaskStatusError)
				task.SetErrorMessage(err.Error())
				return
			}
			
			task.SetStatus(entity.TaskStatusCompleted)
		})

		c.JSON(http.StatusOK, gin.H{
			"message": i18n.Msg(i18n.MsgTaskStarted),
			"task_id": analyzeTask.ID,
		})
	})
}

// GetBrainsResults returns BRAINS analysis results for a photo.
func GetBrainsResults(router *gin.RouterGroup) {
	router.GET("/api/v1/brains/:uid", func(c *gin.Context) {
		s := Auth(c, acl.ResourcePhotos, acl.ActionRead)

		conf := Config(c)
		
		if !conf.BrainsEnabled() {
			AbortBadRequest(c, i18n.ErrFeatureDisabled)
			return
		}

		uid := c.Param("uid")
		if uid == "" {
			AbortBadRequest(c, i18n.ErrInvalidID)
			return
		}

		// Get database connection
		db := conf.Db()
		
		// Find the photo
		photo := entity.FindPhoto(uid, db)
		if photo == nil {
			AbortEntityNotFound(c)
			return
		}

		// Find BRAINS result
		result, err := entity.FindBrainsResult(photo.ID)
		if err != nil {
			c.JSON(http.StatusOK, gin.H{
				"error": "no brains results found for this photo",
				"available": false,
			})
			return
		}

		// Parse JSON data for objects
		var objects []brains.DetectedObject
		if result.ObjectResults != "" {
			if err := json.Unmarshal([]byte(result.ObjectResults), &objects); err != nil {
				log.Warnf("brains: failed to parse object results: %v", err)
			}
		}

		// Parse JSON data for emotions
		var emotions map[string]float32
		if result.Emotions != "" {
			if err := json.Unmarshal([]byte(result.Emotions), &emotions); err != nil {
				log.Warnf("brains: failed to parse emotions: %v", err)
			}
		}

		// Extract keywords
		var keywords []string
		if result.Keywords != "" {
			keywords = strings.Split(result.Keywords, ",")
		}

		c.JSON(http.StatusOK, gin.H{
			"available": true,
			"aesthetic": gin.H{
				"score":         result.AestheticScore,
				"composition":   result.Composition,
				"contrast":      result.Contrast,
				"exposure":      result.Exposure,
				"color_harmony": result.ColorHarmony,
			},
			"scene": gin.H{
				"scene_type":     result.SceneType,
				"indoor_outdoor": result.IndoorOutdoor,
				"time_of_day":    result.TimeOfDay,
				"weather":        result.Weather,
				"emotions":       emotions,
				"keywords":       keywords,
			},
			"objects":      objects,
			"processed_at": result.ProcessedAt.Time,
		})
	})
}

// GetPhotoAesthetic returns aesthetic scoring results for a photo.
func GetPhotoAesthetic(router *gin.RouterGroup) {
	router.GET("/api/v1/brains/:uid/aesthetic", func(c *gin.Context) {
		s := Auth(c, acl.ResourcePhotos, acl.ActionRead)

		conf := Config(c)
		
		if !conf.BrainsEnabled() {
			AbortBadRequest(c, i18n.ErrFeatureDisabled)
			return
		}

		uid := c.Param("uid")
		if uid == "" {
			AbortBadRequest(c, i18n.ErrInvalidID)
			return
		}

		// Get database connection
		db := conf.Db()
		
		// Find the photo
		photo := entity.FindPhoto(uid, db)
		if photo == nil {
			AbortEntityNotFound(c)
			return
		}

		// Find BRAINS result
		result, err := entity.FindBrainsResult(photo.ID)
		if err != nil {
			c.JSON(http.StatusOK, gin.H{
				"error": "no aesthetic results found for this photo",
				"available": false,
			})
			return
		}

		c.JSON(http.StatusOK, gin.H{
			"available": true,
			"score":     result.AestheticScore,
			"details": gin.H{
				"composition":   result.Composition,
				"contrast":      result.Contrast,
				"exposure":      result.Exposure,
				"color_harmony": result.ColorHarmony,
			},
			"processed_at": result.ProcessedAt.Time,
		})
	})
}

// GetPhotoScene returns scene understanding results for a photo.
func GetPhotoScene(router *gin.RouterGroup) {
	router.GET("/api/v1/brains/:uid/scene", func(c *gin.Context) {
		s := Auth(c, acl.ResourcePhotos, acl.ActionRead)

		conf := Config(c)
		
		if !conf.BrainsEnabled() {
			AbortBadRequest(c, i18n.ErrFeatureDisabled)
			return
		}

		uid := c.Param("uid")
		if uid == "" {
			AbortBadRequest(c, i18n.ErrInvalidID)
			return
		}

		// Get database connection
		db := conf.Db()
		
		// Find the photo
		photo := entity.FindPhoto(uid, db)
		if photo == nil {
			AbortEntityNotFound(c)
			return
		}

		// Find BRAINS result
		result, err := entity.FindBrainsResult(photo.ID)
		if err != nil {
			c.JSON(http.StatusOK, gin.H{
				"error": "no scene understanding results found for this photo",
				"available": false,
			})
			return
		}

		// Parse JSON data for emotions
		var emotions map[string]float32
		if result.Emotions != "" {
			if err := json.Unmarshal([]byte(result.Emotions), &emotions); err != nil {
				log.Warnf("brains: failed to parse emotions: %v", err)
			}
		}

		// Extract keywords
		var keywords []string
		if result.Keywords != "" {
			keywords = strings.Split(result.Keywords, ",")
		}

		c.JSON(http.StatusOK, gin.H{
			"available":      true,
			"scene_type":     result.SceneType,
			"indoor_outdoor": result.IndoorOutdoor,
			"time_of_day":    result.TimeOfDay,
			"weather":        result.Weather,
			"emotions":       emotions,
			"keywords":       keywords,
			"processed_at":   result.ProcessedAt.Time,
		})
	})
}

// GetPhotoObjects returns object detection results for a photo.
func GetPhotoObjects(router *gin.RouterGroup) {
	router.GET("/api/v1/brains/:uid/objects", func(c *gin.Context) {
		s := Auth(c, acl.ResourcePhotos, acl.ActionRead)

		conf := Config(c)
		
		if !conf.BrainsEnabled() {
			AbortBadRequest(c, i18n.ErrFeatureDisabled)
			return
		}

		uid := c.Param("uid")
		if uid == "" {
			AbortBadRequest(c, i18n.ErrInvalidID)
			return
		}

		// Get database connection
		db := conf.Db()
		
		// Find the photo
		photo := entity.FindPhoto(uid, db)
		if photo == nil {
			AbortEntityNotFound(c)
			return
		}

		// Find BRAINS result
		result, err := entity.FindBrainsResult(photo.ID)
		if err != nil {
			c.JSON(http.StatusOK, gin.H{
				"error": "no object detection results found for this photo",
				"available": false,
			})
			return
		}

		// Parse JSON data for objects
		var objects []brains.DetectedObject
		if result.ObjectResults != "" {
			if err := json.Unmarshal([]byte(result.ObjectResults), &objects); err != nil {
				log.Warnf("brains: failed to parse object results: %v", err)
			}
		}

		c.JSON(http.StatusOK, gin.H{
			"available":    true,
			"objects":      objects,
			"count":        len(objects),
			"processed_at": result.ProcessedAt.Time,
		})
	})
}

// ClearBrainsCache clears the BRAINS result cache.
func ClearBrainsCache(router *gin.RouterGroup) {
	router.DELETE("/api/v1/brains/cache", func(c *gin.Context) {
		s := Auth(c, acl.ResourceConfig, acl.ActionUpdate)

		if !s.Admin() {
			AbortForbidden(c)
			return
		}

		conf := Config(c)
		
		if !conf.BrainsEnabled() {
			AbortBadRequest(c, i18n.ErrFeatureDisabled)
			return
		}

		// Initialize BRAINS
		b := brains.New(conf)
		if err := b.Init(); err != nil {
			AbortSaveFailed(c, i18n.ErrUnexpected)
			return
		}

		// Clear cache
		if err := b.ClearCache(); err != nil {
			AbortSaveFailed(c, i18n.ErrUnexpected)
			return
		}

		c.JSON(http.StatusOK, gin.H{
			"message": "cache cleared successfully",
		})
	})
}

// StartBrainsScheduler starts the automated BRAINS scheduler.
func StartBrainsScheduler(router *gin.RouterGroup) {
	router.POST("/api/v1/brains/scheduler/start", func(c *gin.Context) {
		s := Auth(c, acl.ResourceConfig, acl.ActionUpdate)

		if !s.Admin() {
			AbortForbidden(c)
			return
		}

		conf := Config(c)
		
		if !conf.BrainsEnabled() {
			AbortBadRequest(c, i18n.ErrFeatureDisabled)
			return
		}

		// Initialize BRAINS
		b := brains.New(conf)
		
		// Parse request for interval configuration
		var req struct {
			Interval int `json:"interval"` // Interval in minutes
		}
		
		if err := c.BindJSON(&req); err == nil && req.Interval > 0 {
			b.SetSchedulerInterval(time.Duration(req.Interval) * time.Minute)
		}
		
		// Start scheduler
		if err := b.StartScheduler(); err != nil {
			log.Errorf("brains: failed to start scheduler: %v", err)
			AbortSaveFailed(c, i18n.ErrUnexpected)
			return
		}

		c.JSON(http.StatusOK, gin.H{
			"message": "BRAINS scheduler started",
			"status": b.GetSchedulerInfo(),
		})
	})
}

// StopBrainsScheduler stops the automated BRAINS scheduler.
func StopBrainsScheduler(router *gin.RouterGroup) {
	router.POST("/api/v1/brains/scheduler/stop", func(c *gin.Context) {
		s := Auth(c, acl.ResourceConfig, acl.ActionUpdate)

		if !s.Admin() {
			AbortForbidden(c)
			return
		}

		conf := Config(c)
		
		if !conf.BrainsEnabled() {
			AbortBadRequest(c, i18n.ErrFeatureDisabled)
			return
		}

		// Initialize BRAINS
		b := brains.New(conf)
		
		// Stop scheduler
		b.StopScheduler()

		c.JSON(http.StatusOK, gin.H{
			"message": "BRAINS scheduler stopped",
		})
	})
}

// GetBrainsSchedulerStatus returns the status of the BRAINS scheduler.
func GetBrainsSchedulerStatus(router *gin.RouterGroup) {
	router.GET("/api/v1/brains/scheduler", func(c *gin.Context) {
		s := Auth(c, acl.ResourceConfig, acl.ActionRead)

		if !s.Admin() {
			AbortForbidden(c)
			return
		}

		conf := Config(c)
		
		if !conf.BrainsEnabled() {
			AbortBadRequest(c, i18n.ErrFeatureDisabled)
			return
		}

		// Initialize BRAINS
		b := brains.New(conf)
		
		c.JSON(http.StatusOK, gin.H{
			"scheduler": b.GetSchedulerInfo(),
		})
	})
}

// CurateBrainsCollections triggers automated collection curation based on BRAINS analysis.
func CurateBrainsCollections(router *gin.RouterGroup) {
	router.POST("/api/v1/brains/curate", func(c *gin.Context) {
		s := Auth(c, acl.ResourceConfig, acl.ActionUpdate)

		if !s.Admin() {
			AbortForbidden(c)
			return
		}

		conf := Config(c)
		
		if !conf.BrainsEnabled() {
			AbortBadRequest(c, i18n.ErrFeatureDisabled)
			return
		}

		// Parse request
		var req struct {
			Refresh bool `json:"refresh"` // Whether to force refresh existing collections
		}
		
		if err := c.BindJSON(&req); err != nil {
			// Set default values if parsing fails
			req.Refresh = false
		}

		// Create a task for collection curation
		task := get.TaskManager()
		curateTask := entity.NewTask(entity.TaskBrainsCurate, "curate collections with brains", entity.TaskPriorityNormal)
		task.Start(curateTask, func(task *entity.Task) {
			task.SetStatus(entity.TaskStatusRunning)
			
			// Initialize BRAINS
			b := brains.New(conf)
			if err := b.Init(); err != nil {
				task.SetStatus(entity.TaskStatusError)
				task.SetErrorMessage(err.Error())
				return
			}
			
			// Run auto-curation
			albums, err := b.AutoCurateCollections()
			
			if err != nil {
				task.SetStatus(entity.TaskStatusError)
				task.SetErrorMessage(err.Error())
				return
			}
			
			task.SetStatus(entity.TaskStatusCompleted)
			task.SetNotes(fmt.Sprintf("Curated %d collections", len(albums)))
		})

		c.JSON(http.StatusOK, gin.H{
			"message": i18n.Msg(i18n.MsgTaskStarted),
			"task_id": curateTask.ID,
		})
	})
}
