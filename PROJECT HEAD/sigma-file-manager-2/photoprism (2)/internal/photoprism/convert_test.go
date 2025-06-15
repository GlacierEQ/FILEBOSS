package photoprism

import (
	"os"
	"path/filepath"
	"testing"

	"github.com/photoprism/photoprism/internal/config"
	"github.com/stretchr/testify/assert"
)

func TestNewConvert(t *testing.T) {
	c := config.TestConfig()
	convert := NewConvert(c)

	assert.IsType(t, &Convert{}, convert)
	assert.NotNil(t, convert.conf)
	assert.NotNil(t, convert.supportedFormats)
}

func TestConvert_IsSupportedFormat(t *testing.T) {
	c := config.TestConfig()
	convert := NewConvert(c)

	assert.True(t, convert.IsSupportedFormat("test.jpg"))
	assert.True(t, convert.IsSupportedFormat("test.JPG"))
	assert.True(t, convert.IsSupportedFormat("test.raw"))
	assert.False(t, convert.IsSupportedFormat("test.txt"))
}

func TestConvert_ConvertToJpeg(t *testing.T) {
	c := config.TestConfig()
	convert := NewConvert(c)

	// Create a temporary RAW file
	tempDir, _ := os.MkdirTemp("", "photoprism_test")
	defer os.RemoveAll(tempDir)
	rawFilePath := filepath.Join(tempDir, "test.raw")
	os.WriteFile(rawFilePath, []byte("dummy raw data"), 0644)

	mediaFile, err := NewMediaFile(rawFilePath)
	assert.NoError(t, err)

	err = convert.ConvertToJpeg(mediaFile)
	assert.NoError(t, err)

	// Check if JPEG file was created
	jpegFilePath := rawFilePath + ".jpg"
	_, err = os.Stat(jpegFilePath)
	assert.NoError(t, err)
}

func TestConvert_CreateSidecarJson(t *testing.T) {
	c := config.TestConfig()
	convert := NewConvert(c)

	// Create a temporary media file
	tempDir, _ := os.MkdirTemp("", "photoprism_test")
	defer os.RemoveAll(tempDir)
	mediaFilePath := filepath.Join(tempDir, "test.jpg")
	os.WriteFile(mediaFilePath, []byte("dummy jpg data"), 0644)

	mediaFile, err := NewMediaFile(mediaFilePath)
	assert.NoError(t, err)

	err = convert.CreateSidecarJson(mediaFile)
	assert.NoError(t, err)

	// Check if JSON sidecar file was created
	jsonFilePath := mediaFilePath + ".json"
	_, err = os.Stat(jsonFilePath)
	assert.NoError(t, err)
}

func TestCalculateOptimalWorkers(t *testing.T) {
	tests := []struct {
		name       string
		maxWorkers int
		expected   int
	}{
		{"LowMaxWorkers", 2, 2},
		{"HighMaxWorkers", 100, 100},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := CalculateOptimalWorkers(tt.maxWorkers)
			assert.LessOrEqual(t, result, tt.expected)
			assert.Greater(t, result, 0)
		})
	}
}
