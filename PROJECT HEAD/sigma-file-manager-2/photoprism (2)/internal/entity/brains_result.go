package entity

import (
	"database/sql"
	"fmt"
	"time"

	"github.com/jinzhu/gorm"
	"github.com/photoprism/photoprism/pkg/rnd"
)

// BrainsResult represents BRAINS analysis results in the database.
type BrainsResult struct {
	ID              string         `gorm:"type:VARBINARY(42);primary_key;" json:"ID" yaml:"-"`
	PhotoID         string         `gorm:"type:VARBINARY(42);index;default:'';" json:"PhotoID" yaml:"-"`
	ObjectResults   string         `gorm:"type:LONGTEXT;" json:"-" yaml:"-"`
	AestheticScore  float32        `gorm:"type:FLOAT;index;" json:"AestheticScore" yaml:"AestheticScore"`
	Composition     float32        `gorm:"type:FLOAT;" json:"Composition" yaml:"Composition"`
	Contrast        float32        `gorm:"type:FLOAT;" json:"Contrast" yaml:"Contrast"`
	Exposure        float32        `gorm:"type:FLOAT;" json:"Exposure" yaml:"Exposure"`
	ColorHarmony    float32        `gorm:"type:FLOAT;" json:"ColorHarmony" yaml:"ColorHarmony"`
	SceneType       string         `gorm:"type:VARCHAR(64);index;" json:"SceneType" yaml:"SceneType"`
	IndoorOutdoor   string         `gorm:"type:VARCHAR(8);index;" json:"IndoorOutdoor" yaml:"IndoorOutdoor"`
	TimeOfDay       string         `gorm:"type:VARCHAR(16);index;" json:"TimeOfDay" yaml:"TimeOfDay"`
	Weather         string         `gorm:"type:VARCHAR(16);" json:"Weather" yaml:"Weather"`
	Keywords        string         `gorm:"type:VARCHAR(1024);" json:"-" yaml:"-"`
	KeywordsSorted  string         `gorm:"type:VARCHAR(1024);" json:"-" yaml:"-"`
	Emotions        string         `gorm:"type:JSON;" json:"-" yaml:"-"`
	Embedding       string         `gorm:"type:BLOB;" json:"-" yaml:"-"`
	ProcessedAt     sql.NullTime   `gorm:"index;" json:"ProcessedAt" yaml:"-"`
	CreatedAt       time.Time      `json:"CreatedAt" yaml:"-"`
	UpdatedAt       time.Time      `json:"UpdatedAt" yaml:"-"`
	DeletedAt       *gorm.DeletedAt `json:"DeletedAt,omitempty" sql:"index" yaml:"-"`
}

// NewBrainsResult creates a new BRAINS result entity.
func NewBrainsResult(photoID string) *BrainsResult {
	result := &BrainsResult{
		ID:             rnd.GenerateUID('r'),
		PhotoID:        photoID,
		ProcessedAt:    sql.NullTime{Time: time.Now(), Valid: true},
	}

	return result
}

// TableName returns the entity table name.
func (BrainsResult) TableName() string {
	return "brains_results"
}

// BeforeCreate creates a random UID if needed.
func (m *BrainsResult) BeforeCreate(scope *gorm.Scope) error {
	if m.ID == "" {
		m.ID = rnd.GenerateUID('r')
		return scope.SetColumn("ID", m.ID)
	}

	return nil
}

// FindBrainsResult finds brains results by photo ID.
func FindBrainsResult(photoID string) (*BrainsResult, error) {
	result := BrainsResult{}

	if err := Db().Where("photo_id = ?", photoID).First(&result).Error; err != nil {
		return nil, err
	}

	return &result, nil
}

// GetOrCreateBrainsResult returns existing brains results or creates new ones.
func GetOrCreateBrainsResult(photoID string) (*BrainsResult, error) {
	if photoID == "" {
		return nil, fmt.Errorf("photo ID is missing")
	}

	result, err := FindBrainsResult(photoID)

	if err == nil {
		return result, err
	} else if err != gorm.ErrRecordNotFound {
		return nil, err
	}

	// Create new result.
	result = NewBrainsResult(photoID)

	// Save result in database.
	if err := result.Save(); err != nil {
		return nil, err
	}

	return result, nil
}

// Save updates the record in the database or creates a new record if it does not already exist.
func (m *BrainsResult) Save() error {
	if m.ID == "" {
		m.ID = rnd.GenerateUID('r')
	}

	return Db().Save(m).Error
}
