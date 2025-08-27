#!/usr/bin/env python
import os
import sys
import time
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq


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


def check_args():
    """
    Sanity checks for input arguments
    """
    if len(sys.argv) < 2:
        print("Usage: txt_to_parquet.py <input_txt_file> [output_parquet_file] [--batch-size N]")
        print("       Converts semicolon-separated measurements file to Parquet format")
        print("       If output file not specified, uses input filename with .parquet extension")
        print("       Default batch size is 1,000,000 rows for memory efficiency")
        print("")
        print("Example: txt_to_parquet.py data/measurements.txt data/measurements.parquet")
        print("         txt_to_parquet.py data/measurements.txt --batch-size 500000")
        exit(1)


def get_args():
    """
    Parse command line arguments
    """
    input_file = sys.argv[1]
    
    # Default output file
    base_name = os.path.splitext(input_file)[0]
    output_file = f"{base_name}.parquet"
    
    # Default batch size
    batch_size = 1_000_000
    
    # Parse optional arguments
    i = 2
    while i < len(sys.argv):
        if sys.argv[i] == '--batch-size' and i + 1 < len(sys.argv):
            try:
                batch_size = int(sys.argv[i + 1])
                i += 2
            except ValueError:
                print(f"Invalid batch size: {sys.argv[i + 1]}")
                exit(1)
        elif not sys.argv[i].startswith('--'):
            # Assume it's the output filename
            output_file = sys.argv[i]
            i += 1
        else:
            i += 1
    
    return input_file, output_file, batch_size


def estimate_file_info(input_file):
    """
    Get information about the input TXT file
    """
    try:
        file_size = os.path.getsize(input_file)
        print(f"Input TXT file size: {convert_bytes(file_size)}")
        
        # Count lines efficiently
        with open(input_file, 'r', encoding='utf-8') as f:
            line_count = sum(1 for _ in f)
        print(f"Total rows to convert: {line_count:,}")
        
        return file_size, line_count
    except FileNotFoundError:
        print(f"Error: Input file '{input_file}' not found")
        exit(1)
    except Exception as e:
        print(f"Error reading input file: {e}")
        exit(1)


def convert_txt_to_parquet(input_file, output_file, batch_size=1_000_000):
    """
    Convert semicolon-separated TXT file to Parquet format with proper headers
    Expected input format: StationName;Temperature
    Output schema: station (string), temperature (float32)
    """
    print(f"Converting '{input_file}' to '{output_file}'...")
    print(f"Using batch size: {batch_size:,} rows")
    
    start_time = time.time()
    
    # Define schema for the 1BRC measurements
    schema = pa.schema([
        ('station', pa.string()),
        ('temperature', pa.float32())
    ])
    
    # Get file info
    file_size, total_rows = estimate_file_info(input_file)
    
    try:
        # Create Parquet writer
        parquet_writer = None
        rows_processed = 0
        batch_count = 0
        
        # Read TXT file in chunks
        chunk_reader = pd.read_csv(
            input_file, 
            sep=';', 
            names=['station', 'temperature'],  # Add proper column names
            dtype={'station': 'string', 'temperature': 'float32'},
            chunksize=batch_size,
            engine='c',  # Use C engine for better performance
            encoding='utf-8',
            header=None  # No header in the original file
        )
        
        for chunk in chunk_reader:
            batch_count += 1
            rows_in_batch = len(chunk)
            rows_processed += rows_in_batch
            
            # Convert to PyArrow table with proper schema
            table = pa.Table.from_pandas(chunk, schema=schema)
            
            # Initialize writer on first batch
            if parquet_writer is None:
                parquet_writer = pq.ParquetWriter(
                    output_file, 
                    schema=schema,
                    compression='snappy',  # Good balance of compression and speed
                    use_dictionary=['station'],  # Use dictionary encoding for station names (huge space savings)
                    compression_level=None,
                    write_statistics=True,
                    use_deprecated_int96_timestamps=False
                )
            
            # Write batch to Parquet file
            parquet_writer.write_table(table)
            
            # Progress reporting every batch
            progress = (rows_processed / total_rows) * 100 if total_rows > 0 else 0
            print(f"Batch {batch_count}: Processed {rows_processed:,}/{total_rows:,} rows ({progress:.1f}%)")
        
        # Close the writer
        if parquet_writer:
            parquet_writer.close()
        
        end_time = time.time()
        elapsed_time = end_time - start_time
        
        # Get output file info
        output_size = os.path.getsize(output_file)
        compression_ratio = (1 - (output_size / file_size)) * 100 if file_size > 0 else 0
        
        print(f"\nConversion completed successfully!")
        print(f"Input file size:  {convert_bytes(file_size)}")
        print(f"Output file size: {convert_bytes(output_size)}")
        print(f"Compression ratio: {compression_ratio:.1f}% smaller")
        print(f"Rows converted: {rows_processed:,}")
        print(f"Elapsed time: {format_elapsed_time(elapsed_time)}")
        if elapsed_time > 0:
            print(f"Processing rate: {rows_processed/elapsed_time:,.0f} rows/second")
        
        return True
        
    except Exception as e:
        print(f"Error during conversion: {e}")
        # Clean up partial file on error
        if os.path.exists(output_file):
            os.remove(output_file)
            print(f"Cleaned up partial output file: {output_file}")
        exit(1)


def verify_parquet_file(parquet_file, sample_size=10):
    """
    Verify the converted Parquet file by reading a sample and showing metadata
    """
    try:
        print(f"\nVerifying Parquet file '{parquet_file}'...")
        
        # Read metadata
        parquet_file_obj = pq.ParquetFile(parquet_file)
        print(f"Schema: {parquet_file_obj.schema}")
        print(f"Number of row groups: {parquet_file_obj.num_row_groups}")
        print(f"Total rows: {parquet_file_obj.metadata.num_rows:,}")
        
        # Show compression info
        for i in range(parquet_file_obj.num_row_groups):
            rg = parquet_file_obj.metadata.row_group(i)
            for j in range(rg.num_columns):
                col = rg.column(j)
                print(f"Row group {i}, Column '{parquet_file_obj.schema.names[j]}': {col.compression}")
                break  # Just show first column compression
            break  # Just show first row group info
        
        # Read a small sample
        sample_df = pd.read_parquet(parquet_file, nrows=sample_size)
        print(f"\nSample data (first {sample_size} rows):")
        print(sample_df.head(sample_size))
        
        print(f"\nData types:")
        print(sample_df.dtypes)
        
        # Show some statistics
        print(f"\nData summary:")
        print(f"Unique stations: {sample_df['station'].nunique():,}")
        print(f"Temperature range: {sample_df['temperature'].min():.1f}°C to {sample_df['temperature'].max():.1f}°C")
        print(f"Average temperature: {sample_df['temperature'].mean():.1f}°C")
        
        return True
        
    except Exception as e:
        print(f"Error verifying Parquet file: {e}")
        return False


def main():
    """
    Main function to orchestrate TXT to Parquet conversion
    """
    check_args()
    input_file, output_file, batch_size = get_args()
    
    print("=== One Billion Row Challenge - TXT to Parquet Converter ===")
    print(f"Input: {input_file}")
    print(f"Output: {output_file}")
    print("")
    
    # Perform conversion
    success = convert_txt_to_parquet(input_file, output_file, batch_size)
    
    if success:
        # Verify the result
        verify_parquet_file(output_file)
        print(f"\n🎉 Conversion complete: '{input_file}' -> '{output_file}'")
        print("The Parquet file is now ready for the One Billion Row Challenge in Go!")
    else:
        print("❌ Conversion failed")
        exit(1)


if __name__ == "__main__":
    main()