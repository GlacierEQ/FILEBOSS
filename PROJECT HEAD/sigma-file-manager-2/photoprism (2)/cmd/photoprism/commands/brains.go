package commands

import (
	"fmt"
	"path/filepath"
	"strings"

	"github.com/photoprism/photoprism/internal/brains"
	"github.com/photoprism/photoprism/internal/config"
	"github.com/photoprism/photoprism/internal/query"
	"github.com/photoprism/photoprism/pkg/fs"
	"github.com/urfave/cli/v2"
)

// BrainsCommand registers the 'brains' CLI command for advanced neural network analysis.
var BrainsCommand = &cli.Command{
	Name:   "brains",
	Usage:  "Advanced neural network analysis",
	Flags:  brainsFlags,
	Subcommands: []*cli.Command{
		{
			Name:   "analyze",
			Usage:  "Analyze photos with BRAINS neural network",
			Action: brainsAnalyzeAction,
			Flags: []cli.Flag{
				&cli.StringFlag{
					Name:    "path",
					Aliases: []string{"p"},
					Usage:   "path to specific photo or directory",
				},
				&cli.StringFlag{
					Name:    "type",
					Aliases: []string{"t"},
					Usage:   "analysis type (object, aesthetic, scene, all)",
					Value:   "all",
				},
				&cli.BoolFlag{
					Name:    "force",
					Aliases: []string{"f"},
					Usage:   "re-analyze already processed photos",
					Value:   false,
				},
			},
		},
		{
			Name:   "download",
			Usage:  "Download BRAINS neural network models",
			Action: brainsDownloadAction,
		},
		{
			Name:   "status",
			Usage:  "Show BRAINS status information",
			Action: brainsStatusAction,
		},
	},
}

// brainsFlags defines the flags for the brains command.
var brainsFlags = []cli.Flag{
	&cli.BoolFlag{
		Name:    "verbose",
		Aliases: []string{"v"},
		Usage:   "show more details",
		Value:   false,
	},
}

// brainsStatusAction shows status information about BRAINS.
func brainsStatusAction(ctx *cli.Context) error {
	conf, err := InitConfig(ctx)
	
	if err != nil {
		return err
	}

	// Initialize BRAINS
	b := brains.New(conf)
	if err := b.Init(); err != nil {
		return fmt.Errorf("failed to initialize BRAINS: %v", err)
	}

	// Show enabled capabilities
	fmt.Println("BRAINS Status")
	fmt.Println("-------------")
	fmt.Printf("BRAINS Enabled: %t\n", conf.BrainsEnabled())
	
	capabilities := conf.BrainsCapabilities()
	fmt.Println("Capabilities:")
	fmt.Printf("  Object Detection: %t\n", capabilities["object_detection"])
	fmt.Printf("  Aesthetic Scoring: %t\n", capabilities["aesthetic_scoring"])
	fmt.Printf("  Scene Understanding: %t\n", capabilities["scene_understanding"])

	// Check model availability
	fmt.Printf("Models Downloaded: %t\n", conf.BrainsModelsDownloaded())
	fmt.Printf("Models Path: %s\n", conf.BrainsPath())

	return nil
}

// brainsDownloadAction downloads BRAINS models.
func brainsDownloadAction(ctx *cli.Context) error {
	conf, err := InitConfig(ctx)
	
	if err != nil {
		return err
	}

	fmt.Println("Downloading BRAINS neural network models...")
	
	scriptPath := filepath.Join(conf.AppPath(), "scripts", "download-brains.sh")
	if !fs.FileExists(scriptPath) {
		return fmt.Errorf("download script not found: %s", scriptPath)
	}
	
	if err := fs.Shell("bash", scriptPath); err != nil {
		return fmt.Errorf("failed to download BRAINS models: %v", err)
	}
	
	fmt.Println("BRAINS models successfully downloaded!")
	return nil
}

// brainsAnalyzeAction runs advanced neural analysis on photos.
func brainsAnalyzeAction(ctx *cli.Context) error {
	conf, err := InitConfig(ctx)
	
	if err != nil {
		return err
	}
	
	if !conf.BrainsEnabled() {
		return fmt.Errorf("BRAINS is not enabled in configuration")
	}
	
	if !conf.BrainsModelsDownloaded() {
		fmt.Println("BRAINS models are not downloaded. Please run 'photoprism brains download' first.")
		return fmt.Errorf("missing BRAINS models")
	}

	// Initialize BRAINS
	b := brains.New(conf)
	if err := b.Init(); err != nil {
		return fmt.Errorf("failed to initialize BRAINS: %v", err)
	}

	// Get path parameter
	path := ctx.String("path")
	analysisType := strings.ToLower(ctx.String("type"))
	force := ctx.Bool("force")
	
	// Get database connection
	db := conf.Db()
	
	// Create query client
	q := query.New(db)
	
	var files []string
	
	if path != "" {
		// Analyze a specific file or directory
		if fs.FileExists(path) {
			files = []string{path}
		} else if fs.DirectoryExists(path) {
			foundFiles, err := fs.FindFiles(path, fs.ImageJPEG)
			if err != nil {
				return fmt.Errorf("error finding files: %v", err)
			}
			files = foundFiles
		} else {
			return fmt.Errorf("path not found: %s", path)
		}
	} else {
		// No path specified, fetch indexed photos from database
		photos, err := q.Photos(1000)
		if err != nil {
			return fmt.Errorf("failed to fetch photos from database: %v", err)
		}
		
		for _, photo := range photos {
			if filename := photo.FileName(); filename != "" {
				files = append(files, filepath.Join(conf.OriginalsPath(), filename))
			}
		}
	}
	
	fmt.Printf("Found %d files for analysis\n", len(files))
	
	// Run BRAINS processing
	results, err := b.ProcessFiles(files)
	if err != nil {
		return fmt.Errorf("analysis failed: %v", err)
	}
	
	// Save results to a JSON file
	outputFile := filepath.Join(conf.StoragePath(), "brains-results.json")
	if err := results.SaveToFile(outputFile); err != nil {
		return fmt.Errorf("failed to save results to %s: %v", outputFile, err)
	}
	
	fmt.Printf("Successfully analyzed %d files\n", len(results.Files))
	fmt.Printf("Results saved to %s\n", outputFile)
	
	return nil
}
```
