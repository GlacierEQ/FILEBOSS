package photoprism

import (
	"errors"
	"fmt"
	"path/filepath"
	"runtime"
	"runtime/debug"
	"strings"
	"sync"
	"time"

	"github.com/jinzhu/gorm"

	"github.com/photoprism/photoprism/internal/brains"
	"github.com/photoprism/photoprism/internal/classify"
	"github.com/photoprism/photoprism/internal/config"
	"github.com/photoprism/photoprism/internal/entity"
	"github.com/photoprism/photoprism/internal/event"
	"github.com/photoprism/photoprism/internal/face"
	"github.com/photoprism/photoprism/internal/mutex"
	"github.com/photoprism/photoprism/internal/nsfw"
	"github.com/photoprism/photoprism/internal/query"
	"github.com/photoprism/photoprism/pkg/clean"
	"github.com/photoprism/photoprism/pkg/fs"
)

// IndexPhoto indexes a photo with the given path and returns the result.
func IndexPhoto(conf *config.Config, fileIndexer *Indexer, filePath string, o IndexOptions) (result IndexResult) {
	defer func() {
		if r := recover(); r != nil {
			log.Errorf("index: %s [panic]", filePath)
			log.Errorf("%s", debug.Stack())
			result = IndexResult{Status: IndexFailed, Err: fmt.Errorf("index: %s [panic]", clean.Log(filepath.Base(filePath)))}
		}
	}()

	start := time.Now()

	// ...existing code...

	// Detect faces and persons.
	if !o.SkipFaces && !photoEntity.Skip() && photoEntity.HasID() && MediaFile().IsJpeg() {
		face.SampleFromMedia(conf, MediaFile(), photoEntity, o.Force)
	}

	// Analyze photo with BRAINS if enabled
	if conf.BrainsEnabled() && !photoEntity.Skip() && photoEntity.HasID() && MediaFile().IsJpeg() {
		log.Debugf("indexer: analyzing %s with BRAINS", clean.Log(filePath))
		
		// Initialize BRAINS
		brainsProcessor := brains.New(conf)
		
		// Get file path
		originalPath := MediaFile().AbsPath
		
		// Process file with BRAINS
		fileResult, err := brainsProcessor.ProcessFile(originalPath)
		
		if err != nil {
			log.Warnf("indexer: BRAINS failed for %s: %s", clean.Log(filePath), err)
		} else if fileResult != nil {
			log.Debugf("indexer: BRAINS analysis complete for %s", clean.Log(filePath))
		}
	}

	// Update photo with metadata.
	if err := photoEntity.Save(); err != nil {
		result.Status = IndexFailed
		result.Err = err
		return result
	}

	// ...existing code...

	return result
}