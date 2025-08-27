package main

import (
	"flag"
	"fmt"
	"log"
	"os"
	"path/filepath"
	"strings"

	"github.com/sbshah97/one-billion-challenge-parquet/internal/stage0"
)

func main() {
	var (
		stage = flag.Int("stage", 0, "Stage to run (0-6)")
		input = flag.String("input", "", "Input Parquet file path")
		all   = flag.Bool("all", false, "Run all stages for comparison")
		help  = flag.Bool("help", false, "Show help message")
	)
	flag.Parse()

	if *help {
		showHelp()
		return
	}

	if *input == "" {
		fmt.Fprintf(os.Stderr, "Error: Input Parquet file is required\n")
		flag.Usage()
		os.Exit(1)
	}

	// Validate that input is a Parquet file
	ext := strings.ToLower(filepath.Ext(*input))
	if ext != ".parquet" {
		fmt.Fprintf(os.Stderr, "Error: Only Parquet files are supported. File extension: %s\n", ext)
		os.Exit(1)
	}

	// Check if file exists
	if _, err := os.Stat(*input); os.IsNotExist(err) {
		fmt.Fprintf(os.Stderr, "Error: Input file '%s' does not exist\n", *input)
		os.Exit(1)
	}

	fmt.Printf("One Billion Row Challenge - Go Implementation (Parquet-Only)\n")
	fmt.Printf("=============================================================\n")
	fmt.Printf("Input file: %s\n", *input)
	fmt.Printf("Stage: %d (Trivial Baseline - loads entire file into memory)\n", *stage)
	fmt.Printf("\n")

	if *all {
		fmt.Printf("Running all stages for comparison...\n")
		// For now, only Stage 0 is implemented
		runStage(0, *input)
	} else {
		if *stage < 0 || *stage > 6 {
			fmt.Fprintf(os.Stderr, "Error: Invalid stage %d. Valid stages: 0-6\n", *stage)
			os.Exit(1)
		}
		
		if *stage > 0 {
			fmt.Fprintf(os.Stderr, "Error: Stage %d is not yet implemented. Only Stage 0 is available.\n", *stage)
			os.Exit(1)
		}
		
		runStage(*stage, *input)
	}
}

func runStage(stageNum int, inputFile string) {
	switch stageNum {
	case 0:
		runStage0(inputFile)
	default:
		fmt.Fprintf(os.Stderr, "Stage %d is not yet implemented\n", stageNum)
		os.Exit(1)
	}
}

func runStage0(inputFile string) {
	fmt.Printf("Running Stage 0 (Trivial Baseline - Load Everything Into Memory)...\n")
	fmt.Printf("====================================================================\n")

	processor := stage0.NewStage0(inputFile)
	
	result, err := processor.Process()
	if err != nil {
		log.Fatalf("Stage 0 processing failed: %v", err)
	}

	fmt.Print(processor.FormatResult(result))
}

func showHelp() {
	fmt.Printf(`One Billion Row Challenge - Go Implementation (Parquet-Only)

A progressive implementation of the One Billion Row Challenge using Go and Apache Parquet files.
This implementation focuses exclusively on Parquet format for optimal columnar processing.

Usage:
  %s [options]

Options:
  -stage int     Stage to run (0-6, default: 0)
  -input string  Input Parquet file path (required, must be .parquet)
  -all           Run all stages for comparison (currently only Stage 0)
  -help          Show this help message

Examples:
  # Run Stage 0 with Parquet file (trivial baseline)
  %s -input data/measurements.parquet

  # Run all implemented stages
  %s -input data/measurements.parquet -all

Stages:
  Stage 0: Trivial baseline - loads ENTIRE file into memory, processes row by row
           This is intentionally slow and memory-heavy to establish baseline
  Stage 1-6: Coming soon with progressive optimizations

Performance Notes:
  - Stage 0 loads entire 1B record file into memory (~40GB+ RAM required)
  - Measures both time and memory usage for accurate baseline metrics
  - Expect several minutes processing time for 1B records

For more information, see README.md
`, os.Args[0], os.Args[0], os.Args[0])
}