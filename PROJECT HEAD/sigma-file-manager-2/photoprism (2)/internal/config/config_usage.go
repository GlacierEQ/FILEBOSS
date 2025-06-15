package config

import (
	"math"
	"time"

	gc "github.com/patrickmn/go-cache"

	"github.com/photoprism/photoprism/pkg/fs"
	"github.com/photoprism/photoprism/pkg/fs/duf"
)

var usageCache = gc.New(5*time.Minute, 5*time.Minute)

// FlushUsageCache resets the usage information cache.
func FlushUsageCache() {
	usageCache.Flush()
}

// Usage represents storage usage information.
type Usage struct {
	FilesUsed    uint64 `json:"filesUsed"`
	FilesUsedPct int    `json:"filesUsedPct"`
	FilesFree    uint64 `json:"filesFree"`
	FilesFreePct int    `json:"filesFreePct"`
	FilesTotal   uint64 `json:"filesTotal"`
}

// Usage returns the used, free and total storage size in bytes and caches the result.
func (c *Config) Usage() Usage {
	// Return nil if feature is not enabled.
	if !c.UsageInfo() {
		return Usage{}
	}

	originalsPath := c.OriginalsPath()

	if cached, hit := usageCache.Get(originalsPath); hit && cached != nil {
		return cached.(Usage)
	}

	info := Usage{}

	if err := c.Db().Unscoped().
		Table("files").
		Select("SUM(file_size) AS files_used").
		Where("deleted_at IS NULL").
		Take(&info).Error; err != nil {
		log.Warnf("config: failed to calculate indexed file usage (%s)", err.Error())
	}

	quotaTotal := c.FilesQuotaBytes()

	if m, err := duf.PathInfo(originalsPath); err == nil {
		info.FilesFree = m.Free
		info.FilesTotal = info.FilesUsed + m.Free
	} else {
		log.Debugf("config: failed to detect filesystem usage (%s)", err.Error())
	}

	if quotaTotal > 0 && quotaTotal < info.FilesTotal {
		info.FilesTotal = quotaTotal
	}

	if info.FilesTotal > 0 {
		info.FilesUsedPct = int(math.RoundToEven(float64(info.FilesUsed) / float64(info.FilesTotal) * 100))
	}

	if info.FilesUsed > 0 && info.FilesUsedPct <= 0 {
		info.FilesUsedPct = 1
	}

	info.FilesFreePct = 100 - info.FilesUsedPct

	usageCache.SetDefault(originalsPath, info)

	return info
}

// UsageInfo returns true if resource usage information should be displayed in the user interface.
func (c *Config) UsageInfo() bool {
	return c.options.UsageInfo || c.options.FilesQuota > 0
}

// FilesQuota returns the maximum aggregated size of all indexed files in megabytes, or 0 if no quota exists.
func (c *Config) FilesQuota() uint64 {
	if c.options.FilesQuota <= 0 {
		return 0
	}

	return c.options.FilesQuota
}

// FilesQuotaBytes returns the maximum aggregated size of all indexed files in bytes, or 0 if no quota exists.
func (c *Config) FilesQuotaBytes() uint64 {
	if c.options.FilesQuota <= 0 {
		return 0
	}

	return c.options.FilesQuota * fs.MB
}

// FilesQuotaReached checks if the filesystem usage has been reached or exceeded.
func (c *Config) FilesQuotaReached() bool {
	return c.Usage().FilesUsedPct >= 100
}

// UsersQuota returns the maximum number of registered user accounts, or 0 if no quota exists.
func (c *Config) UsersQuota() int {
	if c.options.UsersQuota <= 0 {
		return 0
	}

	return c.options.UsersQuota
}
