package search

import (
	"fmt"
	"strings"

	"github.com/photoprism/photoprism/internal/entity"
	"github.com/photoprism/photoprism/internal/form"
	"github.com/photoprism/photoprism/pkg/txt"
)

// BrainsSearch represents a search for photos based on BRAINS analysis results.
type BrainsSearch struct {
	Query *Query
}

// NewBrainsSearch returns a new BrainsSearch.
func NewBrainsSearch(query *Query) *BrainsSearch {
	return &BrainsSearch{Query: query}
}

// AestheticScore searches for photos based on aesthetic score range.
func (s *BrainsSearch) AestheticScore(min, max float32) (results PhotoResults, err error) {
	if min < 0 || min > 10 {
		min = 0
	}

	if max < 0 || max > 10 {
		max = 10
	}

	// Search query
	q := s.Query.db.Table("photos").
		Select("photos.*").
		Joins("JOIN brains_results ON brains_results.photo_id = photos.id").
		Where("brains_results.aesthetic_score BETWEEN ? AND ?", min, max)

	// Apply standard filters
	if err = s.Query.Filters(q); err != nil {
		return results, err
	}

	// Fetch results
	if err = q.Scan(&results).Error; err != nil {
		return results, err
	}

	return results, nil
}

// SceneType searches for photos based on scene type.
func (s *BrainsSearch) SceneType(sceneType string) (results PhotoResults, err error) {
	if sceneType == "" {
		return results, fmt.Errorf("scene type cannot be empty")
	}

	sceneType = strings.ToLower(strings.TrimSpace(sceneType))

	// Search query
	q := s.Query.db.Table("photos").
		Select("photos.*").
		Joins("JOIN brains_results ON brains_results.photo_id = photos.id").
		Where("LOWER(brains_results.scene_type) = ?", sceneType)

	// Apply standard filters
	if err = s.Query.Filters(q); err != nil {
		return results, err
	}

	// Fetch results
	if err = q.Scan(&results).Error; err != nil {
		return results, err
	}

	return results, nil
}

// IndoorOutdoor searches for photos based on indoor/outdoor classification.
func (s *BrainsSearch) IndoorOutdoor(setting string) (results PhotoResults, err error) {
	setting = strings.ToLower(strings.TrimSpace(setting))

	if setting != "indoor" && setting != "outdoor" {
		return results, fmt.Errorf("setting must be 'indoor' or 'outdoor'")
	}

	// Search query
	q := s.Query.db.Table("photos").
		Select("photos.*").
		Joins("JOIN brains_results ON brains_results.photo_id = photos.id").
		Where("LOWER(brains_results.indoor_outdoor) = ?", setting)

	// Apply standard filters
	if err = s.Query.Filters(q); err != nil {
		return results, err
	}

	// Fetch results
	if err = q.Scan(&results).Error; err != nil {
		return results, err
	}

	return results, nil
}

// TimeOfDay searches for photos based on time of day analysis.
func (s *BrainsSearch) TimeOfDay(timeOfDay string) (results PhotoResults, err error) {
	timeOfDay = strings.ToLower(strings.TrimSpace(timeOfDay))

	if timeOfDay == "" {
		return results, fmt.Errorf("time of day cannot be empty")
	}

	// Search query
	q := s.Query.db.Table("photos").
		Select("photos.*").
		Joins("JOIN brains_results ON brains_results.photo_id = photos.id").
		Where("LOWER(brains_results.time_of_day) = ?", timeOfDay)

	// Apply standard filters
	if err = s.Query.Filters(q); err != nil {
		return results, err
	}

	// Fetch results
	if err = q.Scan(&results).Error; err != nil {
		return results, err
	}

	return results, nil
}

// Weather searches for photos based on weather analysis.
func (s *BrainsSearch) Weather(weather string) (results PhotoResults, err error) {
	weather = strings.ToLower(strings.TrimSpace(weather))

	if weather == "" {
		return results, fmt.Errorf("weather cannot be empty")
	}

	// Search query
	q := s.Query.db.Table("photos").
		Select("photos.*").
		Joins("JOIN brains_results ON brains_results.photo_id = photos.id").
		Where("LOWER(brains_results.weather) = ?", weather)

	// Apply standard filters
	if err = s.Query.Filters(q); err != nil {
		return results, err
	}

	// Fetch results
	if err = q.Scan(&results).Error; err != nil {
		return results, err
	}

	return results, nil
}

// Keyword searches for photos based on BRAINS-extracted keywords.
func (s *BrainsSearch) Keyword(keyword string) (results PhotoResults, err error) {
	if keyword == "" {
		return results, fmt.Errorf("keyword cannot be empty")
	}

	keyword = strings.ToLower(strings.TrimSpace(keyword))
	
	// Search query - use LIKE for substring search
	q := s.Query.db.Table("photos").
		Select("photos.*").
		Joins("JOIN brains_results ON brains_results.photo_id = photos.id").
		Where("brains_results.keywords LIKE ?", "%"+keyword+"%")

	// Apply standard filters
	if err = s.Query.Filters(q); err != nil {
		return results, err
	}

	// Fetch results
	if err = q.Scan(&results).Error; err != nil {
		return results, err
	}

	return results, nil
}

// Object searches for photos based on detected objects.
func (s *BrainsSearch) Object(objectName string) (results PhotoResults, err error) {
	if objectName == "" {
		return results, fmt.Errorf("object name cannot be empty")
	}

	objectName = strings.ToLower(strings.TrimSpace(objectName))
	
	// Search query - use JSON-style LIKE search for object detection results
	q := s.Query.db.Table("photos").
		Select("photos.*").
		Joins("JOIN brains_results ON brains_results.photo_id = photos.id").
		Where("brains_results.object_results LIKE ?", "%\"label\":\""+objectName+"\"%")

	// Apply standard filters
	if err = s.Query.Filters(q); err != nil {
		return results, err
	}

	// Fetch results
	if err = q.Scan(&results).Error; err != nil {
		return results, err
	}

	return results, nil
}

// BestAesthetic returns photos with the highest aesthetic scores.
func (s *BrainsSearch) BestAesthetic(limit int) (results PhotoResults, err error) {
	if limit <= 0 {
		limit = 20
	} else if limit > 1000 {
		limit = 1000
	}

	// Search query
	q := s.Query.db.Table("photos").
		Select("photos.*").
		Joins("JOIN brains_results ON brains_results.photo_id = photos.id").
		Where("brains_results.aesthetic_score > 0").
		Order("brains_results.aesthetic_score DESC").
		Limit(limit)

	// Apply standard filters
	if err = s.Query.Filters(q); err != nil {
		return results, err
	}

	// Fetch results
	if err = q.Scan(&results).Error; err != nil {
		return results, err
	}

	return results, nil
}
