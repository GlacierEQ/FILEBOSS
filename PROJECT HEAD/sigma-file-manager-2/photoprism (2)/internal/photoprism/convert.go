package photoprism

import (
	"bytes"
	"encoding/json"
	"errors"
	"fmt"
	"io/ioutil"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"runtime/debug"
	"sync"

	"github.com/karrick/godirwalk"

	"github.com/photoprism/photoprism/internal/config"
	"github.com/photoprism/photoprism/internal/mutex"
	"github.com/photoprism/photoprism/pkg/clean"
	"github.com/photoprism/photoprism/pkg/fs"
	"github.com/photoprism/photoprism/pkg/list"
	"github.com/photoprism/photoprism/pkg/txt"
)

// SupportedFormats is a list of supported image and video formats
var SupportedFormats = []string{
	".jpg", ".jpeg", ".png", ".gif", ".tiff", ".bmp", ".heic", ".heif",
	".mp4", ".mov", ".avi", ".webm", ".mkv",
	".cr2", ".nef", ".arw", ".dng", ".orf", ".rw2", ".pef", ".srw",
}

// CalculateOptimalWorkers determines the optimal number of workers based on system resources
func CalculateOptimalWorkers(maxWorkers int) int {
	cpuCores := runtime.NumCPU()

	// Use 75% of available CPU cores
	optimalWorkers := int(float64(cpuCores) * 0.75)

	// Ensure we don't exceed maxWorkers
	if optimalWorkers > maxWorkers {
		optimalWorkers = maxWorkers
	}

	return optimalWorkers
}

// Convert represents a file format conversion worker.
type Convert struct {
	conf               *config.Config
	cmdMutex           sync.Mutex
	sipsExclude        fs.ExtList
	darktableExclude   fs.ExtList
	rawTherapeeExclude fs.ExtList
	imageMagickExclude fs.ExtList
	supportedFormats   fs.ExtList
}

// NewConvert returns a new file format conversion worker.
func NewConvert(conf *config.Config) *Convert {
	c := &Convert{
		conf:               conf,
		sipsExclude:        fs.NewExtList(conf.SipsExclude()),
		darktableExclude:   fs.NewExtList(conf.DarktableExclude()),
		rawTherapeeExclude: fs.NewExtList(conf.RawTherapeeExclude()),
		imageMagickExclude: fs.NewExtList(conf.ImageMagickExclude()),
		supportedFormats:   fs.NewExtList(SupportedFormats),
	}

	return c
}

// IsSupportedFormat checks if the given file extension is supported
func (c *Convert) IsSupportedFormat(filename string) bool {
	ext := txt.Lower(filepath.Ext(filename))
	return c.supportedFormats.Contains(ext)
}

// handleRawFile processes RAW files using the appropriate converter
func (c *Convert) handleRawFile(f *MediaFile) error {
	if c.conf.RawPresets() {
		if err := c.ConvertToJpeg(f); err != nil {
			log.Errorf("convert: %s", err)
			return err
		}
	}

	if c.conf.SidecarJson() {
		if jsonErr := c.CreateSidecarJson(f); jsonErr != nil {
			log.Errorf("convert: %s", jsonErr)
		}
	}

	return nil
}

// ConvertToJpeg converts a RAW file to JPEG format
func (c *Convert) ConvertToJpeg(f *MediaFile) error {
	if f.IsJpeg() {
		return nil
	}

	jpegFilename := f.AbsPath + ".jpg"

	if _, err := os.Stat(jpegFilename); err == nil {
		return nil // JPEG already exists
	}

	// Use appropriate RAW converter based on configuration
	var cmd *exec.Cmd
	if c.conf.UseDarktable() {
		cmd = exec.Command("darktable-cli", f.AbsPath, jpegFilename)
	} else if c.conf.UseRawTherapee() {
		cmd = exec.Command("rawtherapee-cli", "-o", jpegFilename, "-c", f.AbsPath)
	} else {
		return fmt.Errorf("no suitable RAW converter configured")
	}

	var out bytes.Buffer
	var stderr bytes.Buffer
	cmd.Stdout = &out
	cmd.Stderr = &stderr

	err := cmd.Run()
	if err != nil {
		return fmt.Errorf("error converting RAW to JPEG: %v\nStderr: %s", err, stderr.String())
	}

	return nil
}

// CreateSidecarJson creates a JSON sidecar file for the given media file
func (c *Convert) CreateSidecarJson(f *MediaFile) error {
	jsonFilename := f.AbsPath + ".json"

	if _, err := os.Stat(jsonFilename); err == nil {
		return nil // JSON sidecar already exists
	}

	metadata, err := f.Metadata()
	if err != nil {
		return fmt.Errorf("error extracting metadata: %v", err)
	}

	jsonData, err := json.MarshalIndent(metadata, "", "  ")
	if err != nil {
		return fmt.Errorf("error marshaling metadata to JSON: %v", err)
	}

	err = ioutil.WriteFile(jsonFilename, jsonData, 0644)
	if err != nil {
		return fmt.Errorf("error writing JSON sidecar file: %v", err)
	}

	return nil
}

// Start converts all files in the specified directory based on the current configuration.
func (w *Convert) Start(dir string, ext []string, force bool) (err error) {
	defer func() {
		if r := recover(); r != nil {
			err = fmt.Errorf("convert: %s (panic)\nstack: %s", r, debug.Stack())
			log.Error(err)
		}
	}()

	if err = mutex.IndexWorker.Start(); err != nil {
		return err
	}

	defer mutex.IndexWorker.Stop()

	jobs := make(chan ConvertJob)

	// Start an optimal number of goroutines to convert files.
	var wg sync.WaitGroup
	var numWorkers = CalculateOptimalWorkers(w.conf.IndexWorkers())
	log.Infof("convert: using %d workers for processing", numWorkers)
	wg.Add(numWorkers)
	for i := 0; i < numWorkers; i++ {
		go func() {
			ConvertWorker(jobs)
			wg.Done()
		}()
	}

	done := make(fs.Done)
	ignore := fs.NewIgnoreList(fs.PPIgnoreFilename, true, false)

	if err = ignore.Path(dir); err != nil {
		log.Infof("convert: %s", err)
	}

	ignore.Log = func(fileName string) {
		log.Infof("convert: ignoring %s", clean.Log(filepath.Base(fileName)))
	}

	err = godirwalk.Walk(dir, &godirwalk.Options{
		ErrorCallback: func(fileName string, err error) godirwalk.ErrorAction {
			return godirwalk.SkipNode
		},
		Callback: func(fileName string, info *godirwalk.Dirent) error {
			defer func() {
				if r := recover(); r != nil {
					log.Errorf("convert: %s (panic)\nstack: %s", r, debug.Stack())
				}
			}()

			if mutex.IndexWorker.Canceled() {
				return errors.New("canceled")
			}

			isDir, _ := info.IsDirOrSymlinkToDir()
			isSymlink := info.IsSymlink()

			// Skip file?
			if skip, result := fs.SkipWalk(fileName, isDir, isSymlink, done, ignore); skip {
				return result
			}

			// Process only supported file formats
			if !w.IsSupportedFormat(fileName) {
				return nil
			}

			f, err := NewMediaFile(fileName)

			if err != nil || f.Empty() || f.IsPreviewImage() || !f.IsMedia() {
				return nil
			}

			// Improved RAW file handling
			if f.IsRaw() {
				if err := w.handleRawFile(f); err != nil {
					log.Errorf("convert: error handling RAW file %s: %v", fileName, err)
					return nil
				}
			}

			done[fileName] = fs.Processed

			jobs <- ConvertJob{
				force:   force,
				file:    f,
				convert: w,
			}

			return nil
		},
		Unsorted:            false,
		FollowSymbolicLinks: true,
	})

	close(jobs)
	wg.Wait()

	return err
}
