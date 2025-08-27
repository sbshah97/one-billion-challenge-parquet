// Package utils provides utility functions for the One Billion Challenge.
// This package contains helper functions and common utilities used across stages.
package utils

import (
	"time"
)

// Timer provides timing utilities for performance measurement.
type Timer struct {
	start time.Time
}

// NewTimer creates a new Timer instance.
func NewTimer() *Timer {
	return &Timer{
		start: time.Now(),
	}
}

// Start starts or restarts the timer.
func (t *Timer) Start() {
	t.start = time.Now()
}

// ElapsedMs returns the elapsed time in milliseconds.
func (t *Timer) ElapsedMs() int64 {
	return time.Since(t.start).Nanoseconds() / 1e6
}

// FileInfo represents file information and statistics.
type FileInfo struct {
	Path      string
	Size      int64
	LineCount int64
}

// GetFileInfo returns information about a file.
func GetFileInfo(filepath string) (*FileInfo, error) {
	// TODO: Implement file info gathering
	return nil, nil
}

// FormatBytes formats byte counts in human-readable format.
func FormatBytes(bytes int64) string {
	// TODO: Implement byte formatting
	return ""
}

// FormatDuration formats duration in human-readable format.
func FormatDuration(ms int64) string {
	// TODO: Implement duration formatting
	return ""
}