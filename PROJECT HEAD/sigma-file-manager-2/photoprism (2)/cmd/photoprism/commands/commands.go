package commands

import (
	"github.com/urfave/cli/v2"
)

// PhotoPrism CLI commands.
var GlobalCommands = []*cli.Command{
	StartCommand,
	StopCommand,
	StatusCommand,
	ConfigCommand,
	BackupCommand,
	RestoreCommand,
	ResetCommand,
	CleanupCommand,
	CopyCommand,
	IndexCommand,
	ImportCommand,
	PurgeCommand,
	MomentsCommand,
	ThumbsCommand,
	FacesCommand,
	PullCommand,
	PushCommand,
	ConvertCommand,
	BrainsCommand, // Added BRAINS command
}