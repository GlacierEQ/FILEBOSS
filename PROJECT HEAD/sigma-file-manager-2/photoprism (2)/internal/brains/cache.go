package brains

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"sync"
	"time"

	"github.com/photoprism/photoprism/pkg/fs"
)

// Cache represents a caching system for BRAINS processing results.
type Cache struct {
	cachePath string
	mutex     sync.RWMutex
	maxAge    time.Duration
}

// NewCache returns a new BRAINS cache.
func NewCache(cachePath string) *Cache {
	// Ensure cache directory exists
	if !fs.DirectoryExists(cachePath) {
		if err := os.MkdirAll(cachePath, os.ModePerm); err != nil {
			Log.Errorf("brains: failed to create cache directory: %v", err)
		}
	}

	return &Cache{
		cachePath: cachePath,
		maxAge:    24 * time.Hour, // Default cache expiration of 1 day
	}
}

// Key generates a cache key for a file.
func (c *Cache) Key(filename string) string {
	return filepath.Base(filename)
}

// Path returns the full cache file path for a key.
func (c *Cache) Path(key string) string {
	return filepath.Join(c.cachePath, key+".json")
}

// Get retrieves cached results for a file.
func (c *Cache) Get(filename string) (*ProcessingResults, bool) {
	c.mutex.RLock()
	defer c.mutex.RUnlock()

	key := c.Key(filename)
	cachePath := c.Path(key)

	// Check if cache file exists and is not expired
	info, err := os.Stat(cachePath)
	if err != nil {
		return nil, false
	}

	// Check if cache is expired
	if time.Since(info.ModTime()) > c.maxAge {
		return nil, false
	}

	// Read and parse cache file
	data, err := os.ReadFile(cachePath)
	if err != nil {
		Log.Warnf("brains: error reading cache file: %v", err)
		return nil, false
	}

	var results ProcessingResults
	if err := json.Unmarshal(data, &results); err != nil {
		Log.Warnf("brains: error unmarshalling cache: %v", err)
		return nil, false
	}

	return &results, true
}

// Set caches results for a file.
func (c *Cache) Set(filename string, results *ProcessingResults) error {
	c.mutex.Lock()
	defer c.mutex.Unlock()

	key := c.Key(filename)
	cachePath := c.Path(key)

	// Convert to JSON
	data, err := json.MarshalIndent(results, "", "  ")
	if err != nil {
		return fmt.Errorf("error marshalling results: %v", err)
	}

	// Write to cache file
	if err := os.WriteFile(cachePath, data, 0644); err != nil {
		return fmt.Errorf("error writing cache file: %v", err)
	}

	return nil
}

// Clear removes cache entries for the given files.
func (c *Cache) Clear(filenames []string) error {
	c.mutex.Lock()
	defer c.mutex.Unlock()

	for _, filename := range filenames {
		key := c.Key(filename)
		cachePath := c.Path(key)

		if fs.FileExists(cachePath) {
			if err := os.Remove(cachePath); err != nil {
				Log.Warnf("brains: error removing cache file: %v", err)
			}
		}
	}

	return nil
}

// ClearAll removes all cache entries.
func (c *Cache) ClearAll() error {
	c.mutex.Lock()
	defer c.mutex.Unlock()

	entries, err := os.ReadDir(c.cachePath)
	if err != nil {
		return fmt.Errorf("error reading cache directory: %v", err)
	}

	for _, entry := range entries {
		if entry.IsDir() {
			continue
		}
		
		if filepath.Ext(entry.Name()) == ".json" {
			fullPath := filepath.Join(c.cachePath, entry.Name())
			if err := os.Remove(fullPath); err != nil {
				Log.Warnf("brains: error removing cache file: %v", err)
			}
		}
	}

	return nil
}
