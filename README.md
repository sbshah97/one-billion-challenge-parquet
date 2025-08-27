# One Billion Row Challenge with Parquet Files in Go

A comprehensive implementation of the One Billion Row Challenge optimized for Parquet file format, demonstrating progressive performance optimization techniques in Go.

## Project Overview

This project implements the famous One Billion Row Challenge using Go and Apache Parquet files instead of traditional CSV format. The challenge involves processing one billion temperature measurements from weather stations and calculating min, mean, and max temperatures for each station.

**Key Features:**
- Parquet file format for efficient columnar storage
- Progressive optimization methodology based on ByteSizeGo approach
- 7-stage optimization pipeline from baseline to highly optimized solution
- Comprehensive benchmarking and performance analysis
- Production-ready Go code with proper error handling

## Optimization Stages

Following the ByteSizeGo methodology, this project implements a systematic 7-stage optimization approach:

### Stage 0: Trivial Baseline Implementation ✅ IMPLEMENTED
- **Parquet-only processing** - loads ENTIRE file into memory at once
- Most naive approach possible: converts all data to Go slices, processes row by row
- Basic data structures (map[string]*StationStats) 
- Comprehensive metrics: processing time, memory usage, file load time
- **Current Performance (Parquet format):**
  - 10,000 records: 3ms total (1ms load, <1ms process) | Memory: 258 KiB used, 11.8 MiB peak
  - 1,000,000,000 records: *Ready for testing with 5.4 GiB Parquet file*
- Intentionally memory-intensive baseline for measuring optimization improvements

### Stage 1: Basic Concurrency (~4.5 minutes)
- Introduction of goroutines
- Basic parallelization of file processing
- Simple worker pool pattern
- Channel-based communication
- ~25% performance improvement

### Stage 2: Producer-Consumer Pattern (~3.7 minutes)
- Decoupled data production and consumption
- Buffered channels for better throughput
- Pipeline processing architecture
- Memory usage optimization
- ~18% additional improvement

### Stage 3: Int64 Optimization (~2.9 minutes)
- Integer-based temperature representation
- Elimination of floating-point arithmetic
- Custom parsing routines
- Reduced memory allocations
- ~22% additional improvement

### Stage 4: Efficient Data Structures (~1.6 minutes)
- Custom hash maps and data structures
- Memory pool patterns
- Reduced garbage collection pressure
- Optimized data layouts
- ~45% additional improvement

### Stage 5: Advanced Chunking (~28 seconds)
- Intelligent file chunking strategies
- SIMD-friendly data processing
- Cache-aware algorithms
- Parallel chunk processing
- ~70% additional improvement

### Stage 6: Parsing Optimization (~14 seconds)
- Hand-optimized parsing routines
- Byte-level operations
- Branch prediction optimization
- Memory prefetching techniques
- ~50% additional improvement

## Project Structure

```
one-billion-challenge-parquet/
├── README.md                   # This file
├── CLAUDE.md                   # Claude Code development notes
├── data/                       # Generated data files
│   ├── measurements_1000000000.txt     # 1B records TXT (16.2 GiB)
│   ├── measurements_1000000000.parquet # 1B records Parquet (5.4 GiB)
│   └── measurements_10000.parquet      # 10K test records (57 KiB)
├── scripts/                    # Data generation utilities
│   ├── create_measurements.py  # Unified data generator with dynamic filenames
│   ├── pyproject.toml         # Python dependencies
│   └── uv.lock               # Dependency lock file
├── cmd/                        # Command-line applications
│   └── main.go                # Main challenge CLI (Parquet-only)
├── internal/                   # Internal packages
│   ├── stage0/                # Trivial baseline (IMPLEMENTED)
│   ├── stage1/                # Basic concurrency (TODO)
│   ├── stage2/                # Producer-consumer (TODO)
│   ├── stage3/                # Int64 optimization (TODO)
│   ├── stage4/                # Efficient data structures (TODO)
│   ├── stage5/                # Advanced chunking (TODO)
│   └── stage6/                # Parsing optimization (TODO)
├── go.mod                     # Go module definition
└── go.sum                     # Go module checksums
```

## Usage Instructions

### Data Generation

Generate test data for the challenge using the Python script:

```bash
# Navigate to scripts directory
cd scripts/

# Generate 1 billion rows in TXT format (default)
python create_measurements.py 1_000_000_000

# Generate 1 billion rows in Parquet format
python create_measurements.py 1_000_000_000 --format parquet

# Generate both TXT and Parquet formats
python create_measurements.py 1_000_000_000 --format both

# Generate with custom batch size for memory efficiency
python create_measurements.py 1_000_000_000 --format parquet --batch-size 50000

# Generate smaller dataset for testing
python create_measurements.py 1_000_000 --format both
```

**Dependencies:** Install required Python packages:
```bash
cd scripts/
uv sync  # Install pandas and pyarrow dependencies
```

### Running Implementations

Execute different optimization stages:

```bash
# Run Stage 0 baseline implementation with TXT file
go run cmd/main.go -input data/measurements.txt

# Run Stage 0 with explicit format specification
go run cmd/main.go -input data/measurements.txt -format txt

# Show help and usage
go run cmd/main.go -help

# Run all stages for comparison (when available)
go run cmd/main.go -all -input data/measurements.txt

# Note: Only Stage 0 is currently implemented
# Stage 0 supports TXT format only (Parquet support coming in later stages)
```

**Current Status:**
- ✅ Stage 0: Implemented and tested (TXT format only)
- ⏳ Stages 1-6: Coming soon

**Performance Results (Stage 0 - Baseline):**
- 10,000 records: ~1ms
- 1,000,000 records: ~97ms
- 1,000,000,000 records: *Currently generating test data*

### Benchmarking

Run comprehensive benchmarks:

```bash
# Run all benchmarks
./scripts/benchmark.sh

# Run specific stage benchmark
go test -bench=BenchmarkStage6 ./internal/stage6/

# Generate performance reports
go test -bench=. -benchmem -cpuprofile=cpu.prof ./...
```

## Performance Targets

| Stage | Target Time | Improvement | Key Optimizations |
|-------|-------------|-------------|-------------------|
| 0     | ~6:00 min   | Baseline    | Sequential processing |
| 1     | ~4:30 min   | 25%         | Basic concurrency |
| 2     | ~3:42 min   | 18%         | Producer-consumer |
| 3     | ~2:54 min   | 22%         | Int64 operations |
| 4     | ~1:36 min   | 45%         | Efficient structures |
| 5     | ~0:28 sec   | 70%         | Advanced chunking |
| 6     | ~0:14 sec   | 50%         | Parsing optimization |

**Total improvement: ~25x faster than baseline**

## Development Workflow

### Prerequisites
- Go 1.21 or later
- Apache Arrow Go libraries
- Sufficient disk space for test data (>40GB for full dataset)
- Multi-core CPU for concurrency testing

### Development Process

1. **Setup Environment**
   ```bash
   git clone <repository-url>
   cd one-billion-challenge-parquet
   go mod download
   
   # Setup Python environment for data generation
   cd scripts/
   uv sync  # Install pandas and pyarrow
   ```

2. **Generate Test Data**
   ```bash
   cd scripts/
   python create_measurements.py 1_000_000 --format both  # Start small
   ```

3. **Implement Stage**
   - Create new package in `internal/stageN/`
   - Implement core algorithm
   - Add comprehensive tests
   - Benchmark against previous stage

4. **Validate Performance**
   ```bash
   go test -bench=. ./internal/stageN/
   go run cmd/challenge/main.go -stage N -input data/measurements.parquet
   ```

5. **Profile and Optimize**
   ```bash
   go test -bench=. -cpuprofile=cpu.prof ./internal/stageN/
   go tool pprof cpu.prof
   ```

### Contributing Guidelines

- Each stage should be self-contained
- Maintain backward compatibility
- Include comprehensive benchmarks
- Document optimization techniques used
- Follow Go best practices and idioms

## Technical Notes

- **Parquet Benefits**: Columnar storage, compression, and schema evolution
- **Memory Management**: Custom allocators and object pooling where beneficial
- **Concurrency**: Careful balance between parallelism and overhead
- **Profiling**: Continuous performance monitoring and optimization
- **Testing**: Comprehensive unit tests and integration tests for all stages

This project serves as both a learning resource for Go optimization techniques and a practical implementation of high-performance data processing patterns.