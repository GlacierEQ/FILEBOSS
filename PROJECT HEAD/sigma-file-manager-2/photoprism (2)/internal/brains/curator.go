package brains

import (
	"sort"
	"sync"
	"time"

	"github.com/photoprism/photoprism/internal/entity"
	"github.com/photoprism/photoprism/internal/form"
	"github.com/photoprism/photoprism/internal/query"
)

// CurationTheme defines a theme for automatic curation of photos
type CurationTheme struct {
	Name            string   `json:"name"`
	Description     string   `json:"description"`
	MinAesthetic    float32  `json:"min_aesthetic"`
	SceneTypes      []string `json:"scene_types,omitempty"`
	IndoorOutdoor   string   `json:"indoor_outdoor,omitempty"`
	TimesOfDay      []string `json:"times_of_day,omitempty"`
	Weather         []string `json:"weather,omitempty"`
	RequiredObjects []string `json:"required_objects,omitempty"`
	Keywords        []string `json:"keywords,omitempty"`
	EmotionTypes    []string `json:"emotion_types,omitempty"`
	MinObjects      int      `json:"min_objects"`
	MaxItems        int      `json:"max_items"`
}

// DefaultCurationThemes provides built-in themes for automatic curation
var DefaultCurationThemes = []CurationTheme{
	{
		Name:         "Best Aesthetics",
		Description:  "Photos with exceptional composition and color",
		MinAesthetic: 8.0,
		MaxItems:     50,
	},
	{
		Name:          "Beautiful Landscapes",
		Description:   "High-quality landscape photography",
		MinAesthetic:  7.0,
		SceneTypes:    []string{"landscape"},
		IndoorOutdoor: "outdoor",
		Weather:       []string{"sunny", "cloudy", "partly_cloudy"},
		MaxItems:      50,
	},
	{
		Name:           "Urban Life",
		Description:    "City scenes with architectural elements",
		MinAesthetic:   6.5,
		SceneTypes:     []string{"urban", "cityscape", "architecture"},
		RequiredObjects: []string{"building", "skyscraper", "street"},
		MaxItems:       50,
	},
	{
		Name:         "Peaceful Moments",
		Description:  "Serene images that evoke calm feelings",
		MinAesthetic: 7.0,
		EmotionTypes: []string{"peaceful", "calm", "serene"},
		MaxItems:     50,
	},
	{
		Name:         "Nature's Beauty",
		Description:  "Natural world showcased in vibrant detail",
		MinAesthetic: 7.0,
		Keywords:     []string{"nature", "forest", "mountain", "river", "lake", "ocean"},
		MaxItems:     50,
	},
	{
		Name:         "Golden Hour",
		Description:  "Photos taken during the magical golden hour",
		MinAesthetic: 7.0,
		TimesOfDay:   []string{"sunset", "sunrise"},
		MaxItems:     50,
	},
}

// Curator manages automatic collection creation based on BRAINS analysis
type Curator struct {
	db      *entity.Db
	query   *query.Query
	themes  []CurationTheme
	mutex   sync.RWMutex
}

// NewCurator creates a new collection curator
func NewCurator(db *entity.Db) *Curator {
	return &Curator{
		db:     db,
		query:  query.New(db),
		themes: DefaultCurationThemes,
	}
}

// AddTheme adds a new curation theme
func (c *Curator) AddTheme(theme CurationTheme) {
	c.mutex.Lock()
	defer c.mutex.Unlock()
	
	c.themes = append(c.themes, theme)
}

// GetThemes returns all available themes
func (c *Curator) GetThemes() []CurationTheme {
	c.mutex.RLock()
	defer c.mutex.RUnlock()
	
	return c.themes
}

// CurateCollection creates or updates a smart collection based on a theme
func (c *Curator) CurateCollection(theme CurationTheme) (*entity.Album, error) {
	// Check for existing collection with this theme name
	album := entity.FindAlbumByTitle(theme.Name)
	
	isNew := false
	if album == nil {
		// Create new album if it doesn't exist
		album = entity.NewAlbum(theme.Name, entity.AlbumManual)
		album.AlbumType = "auto" // Mark as automatically curated
		album.AlbumDescription = theme.Description
		isNew = true
	}
	
	// Set or update album details
	album.AlbumDescription = theme.Description
	album.AlbumCategory = "AI Curated"
	album.UpdatedAt = time.Now()
	
	// Save the album
	if err := album.Save(); err != nil {
		return nil, err
	}
	
	// Find photos that match this theme's criteria
	photos, err := c.findPhotosForTheme(theme)
	if err != nil {
		return nil, err
	}
	
	// If this is a new album, add all photos
	// For existing albums, we'll compare and only add/remove as needed
	if isNew {
		for _, photo := range photos {
			// Create album-photo link
			photoAlbum := entity.NewPhotoAlbum(photo.ID, album.ID)
			if err := photoAlbum.Create(); err != nil {
				Log.Warnf("curator: failed to add photo %s to album: %v", photo.ID, err)
			}
		}
	} else {
		// For existing albums, we need to sync the content
		if err := c.syncAlbumPhotos(album, photos); err != nil {
			return nil, err
		}
	}
	
	return album, nil
}

// CurateAllCollections creates or updates collections for all themes
func (c *Curator) CurateAllCollections() ([]*entity.Album, error) {
	c.mutex.RLock()
	defer c.mutex.RUnlock()
	
	var albums []*entity.Album
	
	for _, theme := range c.themes {
		album, err := c.CurateCollection(theme)
		if err != nil {
			Log.Warnf("curator: failed to curate collection %s: %v", theme.Name, err)
			continue
		}
		
		albums = append(albums, album)
	}
	
	return albums, nil
}

// findPhotosForTheme finds photos that match a theme's criteria
func (c *Curator) findPhotosForTheme(theme CurationTheme) (entity.Photos, error) {
	// This is a placeholder implementation
	// In a real implementation, we would use more sophisticated query building
	
	var foundPhotos entity.Photos
	var err error
	
	// Start with aesthetic search as the base
	if theme.MinAesthetic > 0 {
		brainsSearch := c.query.Brains()
		foundPhotos, err = brainsSearch.AestheticScore(theme.MinAesthetic, 10.0)
		if err != nil {
			return nil, err
		}
	} else {
		// If no aesthetic filter, start with all photos
		foundPhotos, err = c.query.Photos(5000)
		if err != nil {
			return nil, err
		}
	}
	
	// Filter by scene type if specified
	if len(theme.SceneTypes) > 0 {
		var sceneMatches entity.Photos
		
		for _, sceneType := range theme.SceneTypes {
			photos, err := c.query.Brains().SceneType(sceneType)
			if err != nil {
				continue
			}
			sceneMatches = append(sceneMatches, photos...)
		}
		
		foundPhotos = foundPhotos.Merge(sceneMatches)
	}
	
	// Filter by indoor/outdoor if specified
	if theme.IndoorOutdoor != "" {
		indoorOutdoorPhotos, err := c.query.Brains().IndoorOutdoor(theme.IndoorOutdoor)
		if err == nil {
			foundPhotos = foundPhotos.Intersection(indoorOutdoorPhotos)
		}
	}
	
	// Apply limits
	if theme.MaxItems > 0 && len(foundPhotos) > theme.MaxItems {
		// Sort by aesthetic score if available
		sort.Slice(foundPhotos, func(i, j int) bool {
			scoreI := getAestheticScore(foundPhotos[i].ID)
			scoreJ := getAestheticScore(foundPhotos[j].ID)
			return scoreI > scoreJ
		})
		
		// Limit to max items
		foundPhotos = foundPhotos[:theme.MaxItems]
	}
	
	return foundPhotos, nil
}

// getAestheticScore gets the aesthetic score for a photo from the database
func getAestheticScore(photoID string) float32 {
	result, err := entity.FindBrainsResult(photoID)
	if err != nil {
		return 0
	}
	return result.AestheticScore
}

// syncAlbumPhotos synchronizes the photos in an album with a new set of photos
func (c *Curator) syncAlbumPhotos(album *entity.Album, photos entity.Photos) error {
	// Get current photos in album
	currentLinks, err := entity.FindPhotoAlbums(form.PhotoAlbumSearch{
		AlbumUID: album.AlbumUID,
	})
	
	if err != nil {
		return err
	}
	
	// Build maps for efficient lookups
	currentPhotoIDs := make(map[string]bool)
	newPhotoIDs := make(map[string]bool)
	
	for _, link := range currentLinks {
		currentPhotoIDs[link.PhotoID] = true
	}
	
	for _, photo := range photos {
		newPhotoIDs[photo.ID] = true
	}
	
	// Add new photos
	for _, photo := range photos {
		if !currentPhotoIDs[photo.ID] {
			// Create album-photo link
			photoAlbum := entity.NewPhotoAlbum(photo.ID, album.ID)
			if err := photoAlbum.Create(); err != nil {
				Log.Warnf("curator: failed to add photo %s to album: %v", photo.ID, err)
			}
		}
	}
	
	// Remove photos no longer matching the theme
	for _, link := range currentLinks {
		if !newPhotoIDs[link.PhotoID] {
			if err := link.Delete(); err != nil {
				Log.Warnf("curator: failed to remove photo %s from album: %v", link.PhotoID, err)
			}
		}
	}
	
	return nil
}
