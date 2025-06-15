package brains

import (
	"fmt"
	"io/ioutil"
	"os"
	"path/filepath"
	"runtime"
	"sync"

	tf "github.com/tensorflow/tensorflow/tensorflow/go"
	"github.com/tensorflow/tensorflow/tensorflow/go/op"
)

// TensorFlowModel represents a loaded TensorFlow model ready for inference.
type TensorFlowModel struct {
	model     *tf.SavedModel
	modelPath string
	modelType string
	version   string
	mutex     sync.RWMutex
	inputName string
	outputName string
	loaded    bool
}

// NewTensorFlowModel creates a new TensorFlow model instance.
func NewTensorFlowModel(modelPath, modelType string) *TensorFlowModel {
	return &TensorFlowModel{
		modelPath:  modelPath,
		modelType:  modelType,
		inputName:  "input:0",
		outputName: "output:0",
		loaded:     false,
	}
}

// Load loads the TensorFlow model from disk.
func (m *TensorFlowModel) Load() error {
	m.mutex.Lock()
	defer m.mutex.Unlock()

	if m.loaded {
		return nil
	}

	Log.Debugf("tensorflow: loading %s model from %s", m.modelType, m.modelPath)

	// Load version information
	versionFile := filepath.Join(filepath.Dir(m.modelPath), "version.txt")
	if versionData, err := ioutil.ReadFile(versionFile); err == nil {
		m.version = string(versionData)
	} else {
		m.version = "unknown"
	}

	// Check if model file exists
	if _, err := os.Stat(m.modelPath); os.IsNotExist(err) {
		return fmt.Errorf("tensorflow: model file not found: %s", m.modelPath)
	}

	// Load the saved model
	model, err := tf.LoadSavedModel(m.modelPath, []string{"serve"}, nil)
	if err != nil {
		return fmt.Errorf("tensorflow: failed to load model: %v", err)
	}

	m.model = model
	m.loaded = true

	// Output memory statistics in debug mode
	var stats runtime.MemStats
	runtime.ReadMemStats(&stats)
	Log.Debugf("tensorflow: model loaded, using %d MB memory", stats.Alloc/1024/1024)

	return nil
}

// Close releases the TensorFlow model resources.
func (m *TensorFlowModel) Close() error {
	m.mutex.Lock()
	defer m.mutex.Unlock()

	if !m.loaded || m.model == nil {
		return nil
	}

	// In a real implementation, we'd explicitly free TensorFlow resources
	// For now, just set to nil for garbage collection
	m.model = nil
	m.loaded = false

	return nil
}

// Predict runs inference using the loaded model.
func (m *TensorFlowModel) Predict(inputTensor *tf.Tensor) (*tf.Tensor, error) {
	m.mutex.RLock()
	defer m.mutex.RUnlock()

	if !m.loaded {
		return nil, fmt.Errorf("tensorflow: model not loaded")
	}

	// Create a session for inference
	session := m.model.Session

	// Run prediction
	output, err := session.Run(
		map[tf.Output]*tf.Tensor{
			m.model.Graph.Operation(m.inputName).Output(0): inputTensor,
		},
		[]tf.Output{
			m.model.Graph.Operation(m.outputName).Output(0),
		},
		nil,
	)
	if err != nil {
		return nil, fmt.Errorf("tensorflow: failed to run inference: %v", err)
	}

	if len(output) == 0 {
		return nil, fmt.Errorf("tensorflow: no output produced")
	}

	return output[0], nil
}

// PreprocessImage converts an image file to a tensor suitable for TensorFlow input.
func PreprocessImage(imagePath string, width, height int) (*tf.Tensor, error) {
	// Read file contents
	imageData, err := ioutil.ReadFile(imagePath)
	if err != nil {
		return nil, err
	}

	// Construct a graph to normalize the image
	graph, input, output, err := constructGraphToNormalizeImage(width, height)
	if err != nil {
		return nil, err
	}

	// Execute the graph to normalize the image
	session, err := tf.NewSession(graph, nil)
	if err != nil {
		return nil, err
	}
	defer session.Close()

	tensor, err := tf.NewTensor(string(imageData))
	if err != nil {
		return nil, err
	}

	normalized, err := session.Run(
		map[tf.Output]*tf.Tensor{input: tensor},
		[]tf.Output{output},
		nil,
	)
	if err != nil {
		return nil, err
	}

	return normalized[0], nil
}

// constructGraphToNormalizeImage creates a TensorFlow graph for image preprocessing.
func constructGraphToNormalizeImage(width, height int) (*tf.Graph, tf.Output, tf.Output, error) {
	graph := tf.NewGraph()
	s := op.NewScope()

	// Create placeholders
	input := op.Placeholder(s, tf.String)
	
	// Decode PNG or JPEG
	decoded := op.DecodeImage(s, input, op.DecodeImageChannels(3))
	
	// Cast to float32
	cast := op.Cast(s, decoded, tf.Float)
	
	// Resize to expected dimensions
	resized := op.ResizeBilinear(s, cast, op.Const(s.SubScope("size"), []int32{int32(height), int32(width)}))
	
	// Scale to [0, 1]
	scaled := op.Div(s, resized, op.Const(s.SubScope("scale"), float32(255.0)))
	
	// Expand dimensions to [1, height, width, 3]
	expanded := op.ExpandDims(s, scaled, op.Const(s.SubScope("batch"), int32(0)))

	// Build the graph
	graph, err := s.Finalize()
	if err != nil {
		return nil, tf.Output{}, tf.Output{}, err
	}

	return graph, input, expanded, nil
}

// ModelManager handles the loading and lifecycle of TensorFlow models.
type ModelManager struct {
	models map[string]*TensorFlowModel
	mutex  sync.RWMutex
}

// NewModelManager creates a new model manager.
func NewModelManager() *ModelManager {
	return &ModelManager{
		models: make(map[string]*TensorFlowModel),
	}
}

// GetModel returns a loaded model by type, loading it if necessary.
func (mm *ModelManager) GetModel(modelPath, modelType string) (*TensorFlowModel, error) {
	mm.mutex.Lock()
	defer mm.mutex.Unlock()

	key := modelType
	model, exists := mm.models[key]
	
	if !exists {
		model = NewTensorFlowModel(modelPath, modelType)
		mm.models[key] = model
	}
	
	if !model.loaded {
		if err := model.Load(); err != nil {
			delete(mm.models, key)
			return nil, err
		}
	}
	
	return model, nil
}

// CloseAll closes all loaded models.
func (mm *ModelManager) CloseAll() {
	mm.mutex.Lock()
	defer mm.mutex.Unlock()

	for key, model := range mm.models {
		if err := model.Close(); err != nil {
			Log.Warnf("tensorflow: failed to close %s model: %v", key, err)
		}
		delete(mm.models, key)
	}
}
