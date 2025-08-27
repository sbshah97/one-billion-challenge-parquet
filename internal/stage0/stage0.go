// Package stage0 implements the initial baseline approach for the One Billion Challenge.
// This stage focuses on establishing a basic processing pipeline without optimizations.
// It loads the ENTIRE Parquet file into memory and processes it row by row with a simple for loop.
package stage0

import (
	"context"
	"fmt"
	"runtime"
	"sort"
	"strconv"
	"strings"
	"time"

	"github.com/apache/arrow/go/v15/arrow/array"
	"github.com/apache/arrow/go/v15/parquet/file"
	"github.com/apache/arrow/go/v15/parquet/pqarrow"
)

// StationStats represents the statistics for a weather station.
type StationStats struct {
	Min   float64
	Max   float64
	Sum   float64
	Count int64
}

// Mean calculates the mean temperature for the station.
func (s *StationStats) Mean() float64 {
	if s.Count == 0 {
		return 0
	}
	return s.Sum / float64(s.Count)
}

// ProcessingResult represents the final result of processing measurements.
type ProcessingResult struct {
	TotalMeasurements int64
	StationCount      int
	StationStats      map[string]*StationStats
	ProcessingTimeMs  int64
	// Memory usage tracking
	MemoryUsedBytes   int64
	PeakMemoryBytes   int64
	FileLoadTimeMs    int64
	ProcessTimeMs     int64
}

// Stage0 represents the baseline implementation structure.
type Stage0 struct {
	inputFile string
}

// NewStage0 creates a new instance of Stage0 processor.
func NewStage0(inputFile string) *Stage0 {
	return &Stage0{
		inputFile: inputFile,
	}
}

// Process implements the main processing logic for stage0.
// This is the most trivial implementation - load entire file into memory and process row by row.
func (s *Stage0) Process() (*ProcessingResult, error) {
	startTime := time.Now()
	
	// Force garbage collection before starting to get accurate memory baseline
	runtime.GC()
	var memStatsBefore runtime.MemStats
	runtime.ReadMemStats(&memStatsBefore)
	
	result, err := s.processParquetFile()
	if err != nil {
		return nil, err
	}
	
	// Measure final memory usage
	runtime.GC()
	var memStatsAfter runtime.MemStats
	runtime.ReadMemStats(&memStatsAfter)
	
	result.ProcessingTimeMs = time.Since(startTime).Milliseconds()
	result.MemoryUsedBytes = int64(memStatsAfter.Alloc - memStatsBefore.Alloc)
	result.PeakMemoryBytes = int64(memStatsAfter.Sys)
	
	return result, nil
}

// processParquetFile processes measurements from a Parquet file using the most trivial approach possible.
// It loads the ENTIRE file into memory and processes it row by row with a simple for loop.
func (s *Stage0) processParquetFile() (*ProcessingResult, error) {
	fileLoadStart := time.Now()
	
	// Open the Parquet file
	reader, err := file.OpenParquetFile(s.inputFile, false)
	if err != nil {
		return nil, fmt.Errorf("failed to open parquet file: %w", err)
	}
	defer reader.Close()
	
	// Create Arrow reader to read entire file into memory
	arrowReader, err := pqarrow.NewFileReader(reader, pqarrow.ArrowReadProperties{}, nil)
	if err != nil {
		return nil, fmt.Errorf("failed to create arrow reader: %w", err)
	}
	
	// Read the ENTIRE table into memory at once - most naive approach possible
	ctx := context.Background()
	table, err := arrowReader.ReadTable(ctx)
	if err != nil {
		return nil, fmt.Errorf("failed to read table: %w", err)
	}
	defer table.Release()
	
	fileLoadTime := time.Since(fileLoadStart).Milliseconds()
	processStart := time.Now()
	
	// Convert to simple Go slices - load everything into memory
	stationCol := table.Column(0).Data().Chunk(0).(*array.String)
	tempCol := table.Column(1).Data().Chunk(0).(*array.Float32)
	
	numRows := int(table.NumRows())
	
	// Most trivial approach: convert everything to Go slices
	stationNames := make([]string, numRows)
	temperatures := make([]float64, numRows)
	
	// Simple for loop to copy all data into memory
	for i := 0; i < numRows; i++ {
		stationNames[i] = stationCol.Value(i)
		temperatures[i] = float64(tempCol.Value(i))
	}
	
	// Now process with the most basic approach - single for loop
	stations := make(map[string]*StationStats)
	
	for i := 0; i < numRows; i++ {
		stationName := stationNames[i]
		temperature := temperatures[i]
		
		// Update station statistics - most basic approach
		if station, exists := stations[stationName]; exists {
			station.Count++
			station.Sum += temperature
			if temperature < station.Min {
				station.Min = temperature
			}
			if temperature > station.Max {
				station.Max = temperature
			}
		} else {
			stations[stationName] = &StationStats{
				Min:   temperature,
				Max:   temperature,
				Sum:   temperature,
				Count: 1,
			}
		}
	}
	
	processTime := time.Since(processStart).Milliseconds()
	
	return &ProcessingResult{
		TotalMeasurements: int64(numRows),
		StationCount:      len(stations),
		StationStats:      stations,
		FileLoadTimeMs:    fileLoadTime,
		ProcessTimeMs:     processTime,
	}, nil
}

// FormatResult formats the processing result for display.
func (s *Stage0) FormatResult(result *ProcessingResult) string {
	var output strings.Builder
	
	// Sort station names for consistent output
	stationNames := make([]string, 0, len(result.StationStats))
	for name := range result.StationStats {
		stationNames = append(stationNames, name)
	}
	sort.Strings(stationNames)

	output.WriteString("One Billion Row Challenge - Stage 0 Results\n")
	output.WriteString("==========================================\n\n")

	// Show first 10 stations for sample output
	displayCount := 10
	if len(stationNames) < displayCount {
		displayCount = len(stationNames)
	}

	output.WriteString("Sample Results (first 10 stations):\n")
	for i := 0; i < displayCount; i++ {
		name := stationNames[i]
		stats := result.StationStats[name]
		output.WriteString(fmt.Sprintf("%s: min=%.1f, mean=%.1f, max=%.1f\n", 
			name, stats.Min, stats.Mean(), stats.Max))
	}

	output.WriteString("\n")
	output.WriteString(fmt.Sprintf("Summary:\n"))
	output.WriteString(fmt.Sprintf("Total stations: %d\n", result.StationCount))
	output.WriteString(fmt.Sprintf("Total measurements: %s\n", formatNumber(result.TotalMeasurements)))
	output.WriteString(fmt.Sprintf("Total processing time: %s\n", formatDuration(result.ProcessingTimeMs)))
	output.WriteString(fmt.Sprintf("File load time: %s\n", formatDuration(result.FileLoadTimeMs)))
	output.WriteString(fmt.Sprintf("Data process time: %s\n", formatDuration(result.ProcessTimeMs)))
	output.WriteString(fmt.Sprintf("Memory used: %s\n", formatBytes(result.MemoryUsedBytes)))
	output.WriteString(fmt.Sprintf("Peak memory: %s\n", formatBytes(result.PeakMemoryBytes)))

	return output.String()
}

// formatNumber formats large numbers with commas.
func formatNumber(n int64) string {
	str := strconv.FormatInt(n, 10)
	if len(str) <= 3 {
		return str
	}

	var result strings.Builder
	for i, digit := range str {
		if i > 0 && (len(str)-i)%3 == 0 {
			result.WriteString(",")
		}
		result.WriteRune(digit)
	}
	return result.String()
}

// formatDuration formats duration in a human-readable format.
func formatDuration(ms int64) string {
	seconds := ms / 1000
	minutes := seconds / 60
	hours := minutes / 60

	if hours > 0 {
		remainingMinutes := minutes % 60
		remainingSeconds := seconds % 60
		return fmt.Sprintf("%dh%dm%ds", hours, remainingMinutes, remainingSeconds)
	} else if minutes > 0 {
		remainingSeconds := seconds % 60
		return fmt.Sprintf("%dm%ds", minutes, remainingSeconds)
	} else {
		remainingMs := ms % 1000
		return fmt.Sprintf("%d.%03ds", seconds, remainingMs)
	}
}

// formatBytes formats byte counts in human-readable format.
func formatBytes(bytes int64) string {
	const unit = 1024
	if bytes < unit {
		return fmt.Sprintf("%d B", bytes)
	}
	div, exp := int64(unit), 0
	for n := bytes / unit; n >= unit; n /= unit {
		div *= unit
		exp++
	}
	return fmt.Sprintf("%.1f %ciB", float64(bytes)/float64(div), "KMGTPE"[exp])
}