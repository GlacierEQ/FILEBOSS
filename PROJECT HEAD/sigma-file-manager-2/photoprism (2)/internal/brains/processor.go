package brains

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"

	"github.com/photoprism/photoprism/internal/config"
)

// ProcessingResults represents the combined results from BRAINS processing.
type ProcessingResults struct {
	Files []*FileResult `json:"files"`
}

// FileResult contains all processing results for a single file.
type FileResult struct {
	Path    string                     `json:"path"`
	Results map[string]ProcessorResult `json:"results"`
}

// ProcessorResult is the interface for all processor-specific results.
type ProcessorResult interface {
	Type() string
}

// NewProcessingResults creates a new empty results container.
func NewProcessingResults() *ProcessingResults {
	return &ProcessingResults{
		Files: make([]*FileResult, 0),
	}
}

// NewFileResult creates a new file result container.
func NewFileResult(path string) *FileResult {
	return &FileResult{
		Path:    path,
		Results: make(map[string]ProcessorResult),
	}
}

// Merge combines another results object into this one.
func (r *ProcessingResults) Merge(other *ProcessingResults) {
	if other == nil {
		return
	}
	
	r.Files = append(r.Files, other.Files...)
}

// SaveToFile saves processing results to a JSON file.
func (r *ProcessingResults) SaveToFile(filename string) error {
	data, err := json.MarshalIndent(r, "", "  ")
	if err != nil {
		return err
	}
	
	return os.WriteFile(filename, data, 0644)
}

// Processor defines the interface for all BRAINS processors.
type Processor interface {
	Process(filename string) (ProcessorResult, error)
	Name() string
}

// BaseProcessor contains functionality shared by all processors.
type BaseProcessor struct {
	conf      *config.Config
	modelPath string
	modelFile string
	name      string
}

// NewBaseProcessor creates a new base processor.
func NewBaseProcessor(conf *config.Config, modelPath, name string) *BaseProcessor {
	return &BaseProcessor{
		conf:      conf,
		modelPath: modelPath,
		name:      name,
	}
}

// Name returns the processor's name.
func (p *BaseProcessor) Name() string {
	return p.name
}

// ObjectProcessor detects objects in images.
type ObjectProcessor struct {
	*BaseProcessor
}

// NewObjectProcessor creates a new object detection processor.
func NewObjectProcessor(conf *config.Config, modelPath string) (*ObjectProcessor, error) {
	base := NewBaseProcessor(conf, modelPath, "object")
	base.modelFile = filepath.Join(modelPath, "object-detection.pb")
	
	// Check if model exists
	if _, err := os.Stat(base.modelFile); os.IsNotExist(err) {
		return nil, fmt.Errorf("object detection model not found at %s", base.modelFile)
	}
	
	return &ObjectProcessor{BaseProcessor: base}, nil
}

// ObjectResult contains object detection results.
type ObjectResult struct {
	Objects []DetectedObject `json:"objects"`
}

// DetectedObject represents a detected object.
type DetectedObject struct {
	Label       string  `json:"label"`
	Confidence  float32 `json:"confidence"`
	X           int     `json:"x"`
	Y           int     `json:"y"`
	Width       int     `json:"width"`
	Height      int     `json:"height"`
}

// Type returns the result type.
func (r ObjectResult) Type() string {
	return "object"
}

// Process processes an image file to detect objects.
func (p *ObjectProcessor) Process(filename string) (ProcessorResult, error) {
	// In a real implementation, this would use the neural network model
	// For now, we're just creating a stub result
	result := ObjectResult{
		Objects: []DetectedObject{
			{
				Label:      "person",
				Confidence: 0.92,
				X:          120,
				Y:          80,
				Width:      200,
				Height:     400,
			},
			{
				Label:      "car",
				Confidence: 0.85,
				X:          300,
				Y:          200,
				Width:      150,
				Height:     100,
			},
		},
	}
	
	return result, nil
}

// AestheticProcessor analyzes image aesthetics.
type AestheticProcessor struct {
	*BaseProcessor
}

// NewAestheticProcessor creates a new aesthetic scoring processor.
func NewAestheticProcessor(conf *config.Config, modelPath string) (*AestheticProcessor, error) {
	base := NewBaseProcessor(conf, modelPath, "aesthetic")
	base.modelFile = filepath.Join(modelPath, "aesthetic-scoring.pb")
	
	// Check if model exists
	if _, err := os.Stat(base.modelFile); os.IsNotExist(err) {
		return nil, fmt.Errorf("aesthetic model not found at %s", base.modelFile)
	}
	
	return &AestheticProcessor{BaseProcessor: base}, nil
}

// AestheticResult contains aesthetic scoring results.
type AestheticResult struct {
	Score           float32            `json:"score"`
	Composition     float32            `json:"composition"`
	Contrast        float32            `json:"contrast"`
	Exposure        float32            `json:"exposure"`
	ColorHarmony    float32            `json:"color_harmony"`
	Recommendations []string           `json:"recommendations"`
}

// Type returns the result type.
func (r AestheticResult) Type() string {
	return "aesthetic"
}

// Process processes an image file for aesthetic scoring.
func (p *AestheticProcessor) Process(filename string) (ProcessorResult, error) {
	// In a real implementation, this would use the neural network model
	// For now, we're just creating a stub result
	result := AestheticResult{
		Score:        8.2,
		Composition:  7.9,
		Contrast:     8.5,
		Exposure:     9.0,
		ColorHarmony: 8.4,
		Recommendations: []string{
			"Slightly improve composition by following rule of thirds",
			"Colors look well balanced",
		},
	}
	
	return result, nil
}

// SceneProcessor analyzes scene content.
type SceneProcessor struct {
	*BaseProcessor
}

// NewSceneProcessor creates a new scene understanding processor.
func NewSceneProcessor(conf *config.Config, modelPath string) (*SceneProcessor, error) {
	base := NewBaseProcessor(conf, modelPath, "scene")
	base.modelFile = filepath.Join(modelPath, "scene-understanding.pb")
	
	// Check if model exists
	if _, err := os.Stat(base.modelFile); os.IsNotExist(err) {
		return nil, fmt.Errorf("scene model not found at %s", base.modelFile)
	}
	
	return &SceneProcessor{BaseProcessor: base}, nil
}

// SceneResult contains scene analysis results.
type SceneResult struct {
	SceneType       string             `json:"scene_type"`
	IndoorOutdoor   string             `json:"indoor_outdoor"`
	TimeOfDay       string             `json:"time_of_day"`
	Weather         string             `json:"weather,omitempty"`
	Keywords        []string           `json:"keywords"`
	Emotions        map[string]float32 `json:"emotions,omitempty"`
}

// Type returns the result type.
func (r SceneResult) Type() string {
	return "scene"
}

// Process processes an image file for scene understanding.
func (p *SceneProcessor) Process(filename string) (ProcessorResult, error) {
	// In a real implementation, this would use the neural network model
	// For now, we're just creating a stub result
	result := SceneResult{
		SceneType:     "landscape",
		IndoorOutdoor: "outdoor",
		TimeOfDay:     "daytime",
		Weather:       "sunny",
		Keywords:      []string{"nature", "mountains", "trees", "sky", "clouds"},
		Emotions: map[string]float32{
			"peaceful": 0.85,
			"awe":      0.72,
			"happy":    0.65,
		},
	}
	
	return result, nil
}
