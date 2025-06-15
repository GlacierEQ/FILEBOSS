package duf

import (
	"testing"

	"github.com/stretchr/testify/assert"
)

func TestMounts(t *testing.T) {
	t.Run("Success", func(t *testing.T) {
		// Get slice of mounted file systems.
		results, warnings, err := Mounts()

		// No warnings or errors are expected.
		assert.NoError(t, err)
		assert.Empty(t, warnings)

		// At least one mount returned?
		if len(results) < 1 {
			t.Error("at least one result expected")
		} else {
			// If so, check the first mount for plausibility.
			result := results[0]
			assert.NotEmpty(t, result.Device)
			assert.Equal(t, "local", result.DeviceType)
			assert.Equal(t, "/", result.Mountpoint)
			assert.NotEmpty(t, result.Fstype)
			assert.NotEmpty(t, result.Opts)
			assert.NotEmpty(t, result.Total)
			assert.NotEmpty(t, result.Used)
			assert.NotEmpty(t, result.Free)
			assert.NotEmpty(t, result.Inodes)
			assert.NotEmpty(t, result.InodesFree)
			assert.NotEmpty(t, result.InodesUsed)
			assert.NotEmpty(t, result.Blocks)
			assert.NotEmpty(t, result.BlockSize)
			assert.NotEmpty(t, result.Metadata)
		}
	})
}

func TestPathInfo(t *testing.T) {
	t.Run("Success", func(t *testing.T) {
		// Get slice of mounted file systems.
		result, err := PathInfo("/photoprism/originals")

		// No warnings or errors are expected.
		assert.NoError(t, err)

		// Check result for plausibility.
		assert.NotEmpty(t, result.Device)
		assert.Equal(t, "local", result.DeviceType)
		assert.Equal(t, "/photoprism", result.Mountpoint)
		assert.NotEmpty(t, result.Fstype)
		assert.NotEmpty(t, result.Opts)
		assert.NotEmpty(t, result.Total)
		assert.NotEmpty(t, result.Used)
		assert.NotEmpty(t, result.Free)
		assert.NotEmpty(t, result.Inodes)
		assert.NotEmpty(t, result.InodesFree)
		assert.NotEmpty(t, result.InodesUsed)
		assert.NotEmpty(t, result.Blocks)
		assert.NotEmpty(t, result.BlockSize)
		assert.NotEmpty(t, result.Metadata)
	})
}

func TestFindByPath(t *testing.T) {
	t.Run("Success", func(t *testing.T) {
		// Get slice of mounted file systems.
		results, warnings, err := FindByPath("/photoprism/originals")

		// No warnings or errors are expected.
		assert.NoError(t, err)
		assert.Empty(t, warnings)

		// At least one mount returned?
		if len(results) < 1 {
			t.Error("at least one result expected")
		} else {
			// If so, check the first mount for plausibility.
			result := results[0]
			assert.NotEmpty(t, result.Device)
			assert.Equal(t, "local", result.DeviceType)
			assert.Equal(t, "/photoprism", result.Mountpoint)
			assert.NotEmpty(t, result.Fstype)
			assert.NotEmpty(t, result.Opts)
			assert.NotEmpty(t, result.Total)
			assert.NotEmpty(t, result.Used)
			assert.NotEmpty(t, result.Free)
			assert.NotEmpty(t, result.Inodes)
			assert.NotEmpty(t, result.InodesFree)
			assert.NotEmpty(t, result.InodesUsed)
			assert.NotEmpty(t, result.Blocks)
			assert.NotEmpty(t, result.BlockSize)
			assert.NotEmpty(t, result.Metadata)
		}
	})
}
