# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a One Billion Row Challenge implementation focused on processing weather station data using Parquet files in Go. The repository is part of the 1BRC (One Billion Row Challenge) which involves processing large datasets of temperature measurements from weather stations worldwide.

## Repository Structure

- `data/` - Contains input data files
  - `weather_stations.csv` - List of weather station names and coordinates (413 cities worldwide)
  - `measurements.txt` - Generated measurement data file (created by the Python script)
- `scripts/` - Data generation utilities
  - `create_measurements.py` - Python script to generate test measurement data

## Data Generation

The main data generation script is located at `scripts/create_measurements.py`. This script:

- Reads weather station names from `data/weather_stations.csv` 
- Generates synthetic temperature measurements between -99.9°C and 99.9°C
- Outputs data in the format: `{station_name};{temperature}` (one per line)
- Supports generating datasets of any size (including 1 billion rows)
- Writes output to `data/measurements.txt`

### Running Data Generation

```bash
cd scripts/
python create_measurements.py <number_of_records>
# Example: python create_measurements.py 1_000_000_000
```

The script accepts underscore notation for large numbers and provides progress feedback during generation.

## Development Notes

- The project is based on the original Java implementation from https://github.com/gunnarmorling/1brc
- Weather station data is adapted from SimpleMaps world cities dataset (Creative Commons Attribution 4.0)
- The Python script uses batch processing (10,000 records per batch) for efficient file I/O
- No additional package dependencies are required for the data generation script (uses only Python standard library)

## File Path References

When referencing locations in this codebase:
- Data generation logic: `scripts/create_measurements.py:101-142`
- Weather station data parsing: `scripts/create_measurements.py:40-52`
- Temperature range configuration: `scripts/create_measurements.py:106-107`