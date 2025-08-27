// Package models defines data models for the One Billion Challenge.
// This package contains structures and types used across the application.
package models

// Measurement represents a single temperature measurement.
type Measurement struct {
	Station     string  `json:"station" parquet:"station"`
	Temperature float64 `json:"temperature" parquet:"temperature"`
}

// StationStats represents aggregated statistics for a weather station.
type StationStats struct {
	Station string  `json:"station" parquet:"station"`
	Min     float64 `json:"min" parquet:"min"`
	Max     float64 `json:"max" parquet:"max"`
	Mean    float64 `json:"mean" parquet:"mean"`
	Count   int64   `json:"count" parquet:"count"`
}

// ProcessingResult represents the final result of processing measurements.
type ProcessingResult struct {
	TotalMeasurements int64                    `json:"total_measurements"`
	StationCount      int                      `json:"station_count"`
	StationStats      map[string]*StationStats `json:"station_stats"`
	ProcessingTimeMs  int64                    `json:"processing_time_ms"`
}

// Config represents application configuration.
type Config struct {
	InputFile    string `json:"input_file"`
	OutputFile   string `json:"output_file"`
	WorkerCount  int    `json:"worker_count"`
	BufferSize   int    `json:"buffer_size"`
	EnableSIMD   bool   `json:"enable_simd"`
	UseParquet   bool   `json:"use_parquet"`
}