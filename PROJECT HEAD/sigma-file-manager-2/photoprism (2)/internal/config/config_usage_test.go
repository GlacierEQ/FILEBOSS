package config

import (
	"testing"

	"github.com/stretchr/testify/assert"

	"github.com/photoprism/photoprism/pkg/fs/duf"
)

func TestConfig_Usage(t *testing.T) {
	c := TestConfig()

	c.options.UsageInfo = true
	result := c.Usage()
	assert.GreaterOrEqual(t, result.FilesUsed, uint64(60000000))

	t.Logf("Storage Used: %d MB (%d%%), Free: %d MB (%d%%), Total %d MB", result.FilesUsed/duf.MB, result.FilesUsedPct, result.FilesFree/duf.MB, result.FilesFreePct, result.FilesTotal/duf.MB)

	c.options.UsageInfo = false
	assert.Equal(t, c.Usage().FilesUsed, uint64(0))
}

func TestConfig_Quota(t *testing.T) {
	c := TestConfig()

	assert.Equal(t, uint64(0), c.FilesQuota())
	assert.Equal(t, 0, c.UsersQuota())
}
