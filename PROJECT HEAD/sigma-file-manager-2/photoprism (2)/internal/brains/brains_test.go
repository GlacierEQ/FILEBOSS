package brains

import (
	"os"
	"path/filepath"
	"testing"

	"github.com/photoprism/photoprism/internal/config"
	"github.com/photoprism/photoprism/pkg/fs"
	"github.com/stretchr/testify/assert"
)

func TestNew(t *testing.T) {
	c := config.TestConfig()
	b := New(c)

	assert.IsType(t, &Brains{}, b)
	assert.NotNil(t, b.conf)
	assert.Equal(t, filepath.Join(c.AssetsPath(), "brains"), b.modelPath)
	assert.False(t, b.initialized)
	assert.NotZero(t, b.batchSize)
}

func TestCalculateOptimalBatchSize(t *testing.T) {
	result := calculateOptimalBatchSize()
	
	// Test if result is reasonable based on system specs
	assert.GreaterOrEqual(t, result, 8)
	assert.LessOrEqual(t, result, 32)
}

func TestBrains_Init(t *testing.T) {
	c := config.TestConfig()
	
	// Create test model directory
	modelPath := filepath.Join(c.AssetsPath(), "brains")
	if err := os.MkdirAll(modelPath, os.ModePerm); err != nil {
		t.Fatal(err)
	}
	defer os.RemoveAll(modelPath)
	
	// Create mock model files
	modelFiles := []string{
		filepath.Join(modelPath, "object-detection.pb"),
		filepath.Join(modelPath, "aesthetic-scoring.pb"),
		filepath.Join(modelPath, "scene-understanding.pb"),
	}
	
	for _, file := range modelFiles {
		if err := os.WriteFile(file, []byte("mock model data"), os.ModePerm); err != nil {
			t.Fatal(err)
		}
	}
	
	b := New(c)
	
	// Test initialization
	err := b.Init()
	assert.NoError(t, err)
	assert.True(t, b.initialized)
	
	// Test processors
	assert.Len(t, b.processors, 3)
	assert.Len(t, b.capabilities, 3)
	
	// Test capabilities
	assert.True(t, b.HasCapability("object_detection"))
	assert.True(t, b.HasCapability("aesthetic_scoring"))
	assert.True(t, b.HasCapability("scene_understanding"))
	
	// Test double initialization (should be idempotent)
	err = b.Init()
	assert.NoError(t, err)
}

func TestBrains_ProcessFiles(t *testing.T) {
	c := config.TestConfig()
	
	// Create test model directory
	modelPath := filepath.Join(c.AssetsPath(), "brains")
	if err := os.MkdirAll(modelPath, os.ModePerm); err != nil {
		t.Fatal(err)
	}
	defer os.RemoveAll(modelPath)
	
	// Create mock model files
	modelFiles := []string{
		filepath.Join(modelPath, "object-detection.pb"),
		filepath.Join(modelPath, "aesthetic-scoring.pb"),
		filepath.Join(modelPath, "scene-understanding.pb"),
	}
	
	for _, file := range modelFiles {
		if err := os.WriteFile(file, []byte("mock model data"), os.ModePerm); err != nil {
			t.Fatal(err)
		}
	}
	
	// Create test images
	testDir := filepath.Join(c.StoragePath(), "testdata", "brains")
	if err := os.MkdirAll(testDir, os.ModePerm); err != nil {
		t.Fatal(err)
	}
	defer os.RemoveAll(testDir)
	
	imageFiles := []string{
		filepath.Join(testDir, "test1.jpg"),
		filepath.Join(testDir, "test2.jpg"),
		filepath.Join(testDir, "test3.jpg"),
	}
	
	for _, file := range imageFiles {
		if err := os.WriteFile(file, []byte("mock image data"), os.ModePerm); err != nil {
			t.Fatal(err)
		}
	}
	
	b := New(c)
	err := b.Init()
	assert.NoError(t, err)
	
	// Test processing files
	results, err := b.ProcessFiles(imageFiles)
	assert.NoError(t, err)
	assert.NotNil(t, results)
	assert.Len(t, results.Files, 3)
	
	// Test saving results
	outputFile := filepath.Join(testDir, "results.json")
	err = results.SaveToFile(outputFile)
	assert.NoError(t, err)
	assert.True(t, fs.FileExists(outputFile))
}
