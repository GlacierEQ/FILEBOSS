package brains

import (
	"testing"
	"path/filepath"
	"os"
	
	"github.com/photoprism/photoprism/internal/config"
	"github.com/photoprism/photoprism/internal/entity"
	"github.com/photoprism/photoprism/pkg/fs"
	"github.com/stretchr/testify/assert"
)

// TestCompleteIntegration verifies the full integration chain from file analysis to database storage
func TestCompleteIntegration(t *testing.T) {
	// Create test config
	c := config.TestConfig()
	
	// Ensure the database is initialized
	entity.SetupTestDB(t)
	
	// Create a test image file
	testDir := filepath.Join(c.StoragePath(), "testdata", "brains")
	if err := os.MkdirAll(testDir, os.ModePerm); err != nil {
		t.Fatal(err)
	}
	defer os.RemoveAll(testDir)
	
	testImagePath := filepath.Join(testDir, "integration_test.jpg")
	if err := fs.Copy("testdata/test.jpg", testImagePath); err != nil {
		t.Fatalf("failed to copy test image: %v", err)
	}
	
	// Create test photo entity
	photo := entity.NewPhoto(false)
	photo.PhotoName = "Integration Test"
	photo.PhotoPath = "testdata/brains"
	photo.PhotoUID = "pxbrtestuiq"
	assert.NoError(t, photo.Create())
	
	// Initialize BRAINS
	b := New(c)
	assert.NoError(t, b.Init())
	
	// Process the test image
	result, err := b.ProcessFile(testImagePath)
	assert.NoError(t, err)
	assert.NotNil(t, result)
	
	// Verify database record was created
	dbResult, err := entity.FindBrainsResult(photo.ID)
	assert.NoError(t, err)
	assert.NotNil(t, dbResult)
	
	// Verify content of analysis
	assert.Greater(t, dbResult.AestheticScore, float32(0))
	assert.NotEmpty(t, dbResult.SceneType)
	
	// Verify search functionality
	searchResults, err := c.Query().Brains().AestheticScore(0, 10)
	assert.NoError(t, err)
	assert.NotEmpty(t, searchResults)
}
