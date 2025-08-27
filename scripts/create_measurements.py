#!/usr/bin/env python
#
#  Copyright 2023 The original authors
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#

# Based on https://github.com/gunnarmorling/1brc/blob/main/src/main/java/dev/morling/onebrc/CreateMeasurements.java

import os
import sys
import random
import time
import argparse
try:
    import pandas as pd
    import pyarrow as pa
    import pyarrow.parquet as pq
    PARQUET_AVAILABLE = True
except ImportError:
    PARQUET_AVAILABLE = False


def parse_args():
    """
    Parse command line arguments with support for output format selection
    """
    parser = argparse.ArgumentParser(
        description="Generate synthetic measurement data for the One Billion Row Challenge",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  create_measurements.py 1_000_000_000                    # Generate 1B rows in TXT format
  create_measurements.py 1_000_000_000 --format parquet   # Generate 1B rows in Parquet format
  create_measurements.py 1_000_000_000 --format both      # Generate both TXT and Parquet
        """
    )
    
    parser.add_argument('num_records', type=str, 
                       help='Number of records to create (supports underscore notation, e.g., 1_000_000_000)')
    
    parser.add_argument('--format', choices=['txt', 'parquet', 'both'], default='txt',
                       help='Output format: txt (default), parquet, or both')
    
    parser.add_argument('--batch-size', type=int, default=10000,
                       help='Batch size for processing (default: 10000)')
    
    args = parser.parse_args()
    
    # Validate num_records
    try:
        num_records = int(args.num_records.replace('_', ''))
        if num_records <= 0:
            raise ValueError()
    except ValueError:
        parser.error("Number of records must be a positive integer")
    
    # Check parquet availability if needed
    if args.format in ['parquet', 'both'] and not PARQUET_AVAILABLE:
        parser.error("Parquet format requires pandas and pyarrow. Install with: uv add pandas pyarrow")
    
    return args, num_records


def generate_station_names():
    """
    Generate synthetic station names for measurements
    """
    return [f"Station{i:04d}" for i in range(1, 1001)]


def convert_bytes(num):
    """
    Convert bytes to a human-readable format (e.g., KiB, MiB, GiB)
    """
    for x in ['bytes', 'KiB', 'MiB', 'GiB']:
        if num < 1024.0:
            return "%3.1f %s" % (num, x)
        num /= 1024.0


def format_elapsed_time(seconds):
    """
    Format elapsed time in a human-readable format
    """
    if seconds < 60:
        return f"{seconds:.3f} seconds"
    elif seconds < 3600:
        minutes, seconds = divmod(seconds, 60)
        return f"{int(minutes)} minutes {int(seconds)} seconds"
    else:
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        if minutes == 0:
            return f"{int(hours)} hours {int(seconds)} seconds"
        else:
            return f"{int(hours)} hours {int(minutes)} minutes {int(seconds)} seconds"


def estimate_file_size(num_rows_to_create):
    """
    Tries to estimate how large a file the test data will be
    """
    # Average station name length (Station0001 = 11 chars)
    avg_name_bytes = 11
    
    # Average temperature bytes (e.g., "-99.9" = 5 chars)
    avg_temp_bytes = 4.4

    # add 2 for separator and newline
    avg_line_length = avg_name_bytes + avg_temp_bytes + 2

    human_file_size = convert_bytes(num_rows_to_create * avg_line_length)

    return f"Estimated max file size is:  {human_file_size}."


def build_test_data_txt(num_rows_to_create, batch_size=10000):
    """
    Generates and writes test data to TXT file
    """
    start_time = time.time()
    coldest_temp = -99.9
    hottest_temp = 99.9
    station_names = generate_station_names()
    chunks = num_rows_to_create // batch_size
    print('Building TXT test data...')

    try:
        with open("../data/measurements.txt", 'w') as file:
            progress = 0
            for chunk in range(chunks):
                batch = random.choices(station_names, k=batch_size)
                prepped_deviated_batch = '\n'.join([f"{station};{random.uniform(coldest_temp, hottest_temp):.1f}" for station in batch])
                file.write(prepped_deviated_batch + '\n')
                
                # Update progress bar every 1%
                if (chunk + 1) * 100 // chunks != progress:
                    progress = (chunk + 1) * 100 // chunks
                    bars = '=' * (progress // 2)
                    sys.stdout.write(f"\r[{bars:<50}] {progress}%")
                    sys.stdout.flush()
        sys.stdout.write('\n')
        
        end_time = time.time()
        elapsed_time = end_time - start_time
        file_size = os.path.getsize("../data/measurements.txt")
        human_file_size = convert_bytes(file_size)
        
        print("Test data successfully written to data/measurements.txt")
        print(f"Actual file size:  {human_file_size}")
        print(f"Elapsed time: {format_elapsed_time(elapsed_time)}")
        
        return "../data/measurements.txt", elapsed_time, file_size
        
    except Exception as e:
        print("Something went wrong. Printing error info and exiting...")
        print(e)
        exit()


def build_test_data_parquet(num_rows_to_create, batch_size=10000):
    """
    Generates test data directly to Parquet format
    """
    start_time = time.time()
    coldest_temp = -99.9
    hottest_temp = 99.9
    station_names = generate_station_names()
    chunks = num_rows_to_create // batch_size
    
    print('Building Parquet test data...')
    
    # Define schema
    schema = pa.schema([
        ('station', pa.string()),
        ('temperature', pa.float32())
    ])
    
    try:
        parquet_writer = None
        rows_processed = 0
        
        for chunk in range(chunks):
            # Generate batch data
            batch_stations = random.choices(station_names, k=batch_size)
            batch_temperatures = [random.uniform(coldest_temp, hottest_temp) for _ in range(batch_size)]
            
            # Create DataFrame for this batch
            batch_df = pd.DataFrame({
                'station': batch_stations,
                'temperature': batch_temperatures
            })
            batch_df['temperature'] = batch_df['temperature'].astype('float32')
            
            # Convert to PyArrow table
            table = pa.Table.from_pandas(batch_df, schema=schema)
            
            # Initialize writer on first batch
            if parquet_writer is None:
                parquet_writer = pq.ParquetWriter(
                    "../data/measurements.parquet",
                    schema=schema,
                    compression='snappy',
                    use_dictionary=['station'],
                    write_statistics=True
                )
            
            # Write batch
            parquet_writer.write_table(table)
            rows_processed += batch_size
            
            # Progress reporting
            progress = ((chunk + 1) * 100) // chunks
            bars = '=' * (progress // 2)
            sys.stdout.write(f"\r[{bars:<50}] {progress}%")
            sys.stdout.flush()
        
        # Close writer
        if parquet_writer:
            parquet_writer.close()
            
        sys.stdout.write('\n')
        
        end_time = time.time()
        elapsed_time = end_time - start_time
        file_size = os.path.getsize("../data/measurements.parquet")
        human_file_size = convert_bytes(file_size)
        
        print("Test data successfully written to data/measurements.parquet")
        print(f"Actual file size:  {human_file_size}")
        print(f"Elapsed time: {format_elapsed_time(elapsed_time)}")
        
        return "../data/measurements.parquet", elapsed_time, file_size
        
    except Exception as e:
        print("Something went wrong. Printing error info and exiting...")
        print(e)
        exit()


def build_test_data(num_rows_to_create, output_format='txt', batch_size=10000):
    """
    Main function to generate test data in specified format(s)
    """
    results = {}
    
    if output_format in ['txt', 'both']:
        print("=== Generating TXT Format ===")
        txt_file, txt_time, txt_size = build_test_data_txt(num_rows_to_create, batch_size)
        results['txt'] = {'file': txt_file, 'time': txt_time, 'size': txt_size}
    
    if output_format in ['parquet', 'both']:
        print("=== Generating Parquet Format ===")
        parquet_file, parquet_time, parquet_size = build_test_data_parquet(num_rows_to_create, batch_size)
        results['parquet'] = {'file': parquet_file, 'time': parquet_time, 'size': parquet_size}
    
    # Show comparison if both formats generated
    if output_format == 'both':
        print("\n=== Format Comparison ===")
        compression_ratio = (1 - (results['parquet']['size'] / results['txt']['size'])) * 100
        speed_ratio = results['txt']['time'] / results['parquet']['time'] if results['parquet']['time'] > 0 else 0
        print(f"TXT file:     {convert_bytes(results['txt']['size'])} in {format_elapsed_time(results['txt']['time'])}")
        print(f"Parquet file: {convert_bytes(results['parquet']['size'])} in {format_elapsed_time(results['parquet']['time'])}")
        print(f"Compression:  {compression_ratio:.1f}% smaller")
        print(f"Speed:        Parquet was {speed_ratio:.1f}x {'faster' if speed_ratio > 1 else 'slower'}")
    
    return results


def main():
    """
    Main program function with support for multiple output formats
    """
    args, num_rows_to_create = parse_args()
    
    print(f"=== One Billion Row Challenge - Data Generator ===")
    print(f"Records to generate: {num_rows_to_create:,}")
    print(f"Output format: {args.format}")
    print(f"Batch size: {args.batch_size:,}")
    print()
    
    # Show size estimate for TXT format
    if args.format in ['txt', 'both']:
        print(estimate_file_size(num_rows_to_create))
    
    # Generate data in requested format(s)
    results = build_test_data(num_rows_to_create, args.format, args.batch_size)
    
    print("\n🎉 Data generation complete!")
    
    # Show final summary
    if 'parquet' in results:
        print(f"✅ Parquet file ready for Go 1BRC implementation: {results['parquet']['file']}")
    if 'txt' in results:
        print(f"✅ TXT file available: {results['txt']['file']}")
        
    print("\nYou can now run the One Billion Row Challenge with the generated data!")


if __name__ == "__main__":
    main()
exit()