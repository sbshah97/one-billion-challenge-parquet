# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a One Billion Row Challenge implementation focused on processing weather station data using Parquet files in Go. The repository is part of the 1BRC (One Billion Row Challenge) which involves processing large datasets of temperature measurements from weather stations worldwide.

## Repository Structure

- `data/` - Contains generated data files
  - `measurements.txt` - Generated measurement data in text format (StationName;Temperature)
  - `measurements.parquet` - Generated measurement data in Parquet format (columnar)
- `scripts/` - Data generation utilities
  - `create_measurements.py` - Unified Python script to generate test data in TXT and/or Parquet formats
  - `pyproject.toml` - Python project configuration with dependencies (pandas, pyarrow)
  - `uv.lock` - Dependency lock file for reproducible builds

## Data Generation

The unified data generation script is located at `scripts/create_measurements.py`. This script:

- Generates synthetic weather station names (Station0001-Station1000)
- Creates synthetic temperature measurements between -99.9°C and 99.9°C
- Supports multiple output formats:
  - TXT format: `{station_name};{temperature}` (one per line) → `data/measurements.txt`
  - Parquet format: Columnar storage with proper schema → `data/measurements.parquet`
  - Both formats simultaneously for comparison
- Supports generating datasets of any size (including 1 billion rows)
- Uses efficient batch processing with configurable batch sizes
- Provides progress tracking and performance metrics

### Running Data Generation

```bash
cd scripts/

# Generate 1 billion rows in TXT format (default)
python create_measurements.py 1_000_000_000

# Generate 1 billion rows in Parquet format
python create_measurements.py 1_000_000_000 --format parquet

# Generate both TXT and Parquet formats for comparison
python create_measurements.py 1_000_000_000 --format both

# Generate with custom batch size (useful for memory management)
python create_measurements.py 1_000_000_000 --format parquet --batch-size 50000

# Generate smaller dataset for testing
python create_measurements.py 1_000_000 --format both
```

The script accepts underscore notation for large numbers and provides:
- Real-time progress tracking with progress bars
- Performance metrics (elapsed time, file sizes, processing rates)
- Format comparison statistics when generating both formats
- Memory-efficient batch processing

## Development Notes

- The project is based on the original Java implementation from https://github.com/gunnarmorling/1brc
- Uses synthetic weather station names (Station0001-Station1000) instead of real city names for simplicity
- The Python script uses configurable batch processing (default 10,000 records per batch) for efficient file I/O
- Dependencies managed with `uv` (Python package manager): pandas for data processing, pyarrow for Parquet support
- Parquet format provides significant compression benefits (~70-80% smaller than TXT) with faster read performance for columnar operations

## File Path References

When referencing locations in this codebase:
- Main data generation script: `scripts/create_measurements.py`
- TXT format generation logic: `scripts/create_measurements.py:128-170`
- Parquet format generation logic: `scripts/create_measurements.py:172-250`
- Command-line argument parsing: `scripts/create_measurements.py:34-72`
- Temperature range configuration: `scripts/create_measurements.py:133-134` (TXT) and `scripts/create_measurements.py:177-178` (Parquet)
- Project dependencies: `scripts/pyproject.toml`