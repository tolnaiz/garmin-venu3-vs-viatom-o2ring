import argparse
import glob
import json
import os
import pandas as pd
from datetime import datetime, timedelta

def find_files(directory):
    """
    Find the required files in the given directory.
    Returns the first matching file for each type.
    """
    pulse_file = glob.glob(os.path.join(directory, "garmin*-pulse.json"))[0]
    spo2_file = glob.glob(os.path.join(directory, "garmin*-spo2.json"))[0]
    o2ring_file = glob.glob(os.path.join(directory, "O2Ring _*.csv"))[0]

    return pulse_file, spo2_file, o2ring_file

def parse_garmin_pulse(file_path):
    """
    Parse Garmin pulse JSON file and convert to 1-minute resolution DataFrame
    """
    with open(file_path, 'r') as f:
        data = json.load(f)

    # Create DataFrame with timestamp and heart rate
    records = []
    for item in data:
        timestamp = datetime.fromtimestamp(item['startGMT'] / 1000.0)  # Convert milliseconds to seconds
        records.append({
            'timestamp': timestamp,
            'heart_rate': item['value']
        })

    df = pd.DataFrame(records)
    df.set_index('timestamp', inplace=True)

    # Resample to 1-minute intervals using linear interpolation
    return df.resample('min').mean().interpolate(method='linear')

def parse_garmin_spo2(file_path):
    """
    Parse Garmin SpO2 JSON file and convert to 1-minute resolution DataFrame
    """
    with open(file_path, 'r') as f:
        data = json.load(f)

    records = []
    for item in data:
        timestamp = datetime.strptime(item['epochTimestamp'], "%Y-%m-%dT%H:%M:%S.%f")
        records.append({
            'timestamp': timestamp,
            'garmin_spo2': item['spo2Reading'],
            'garmin_confidence': item['readingConfidence']
        })

    df = pd.DataFrame(records)
    df.set_index('timestamp', inplace=True)

    # Resample to 1-minute intervals using mean, without filling missing values
    return df.resample('min').mean()

def parse_o2ring_csv(file_path):
    """
    Parse O2Ring CSV file and convert to 1-minute resolution DataFrame
    """
    # Read CSV file with specific data types
    df = pd.read_csv(file_path)

    # Convert timestamp column
    df['timestamp'] = pd.to_datetime(df['Time'], format='%H:%M:%S %b %d %Y')
    df.set_index('timestamp', inplace=True)

    # Convert columns to numeric, dropping the original Time column
    numeric_columns = {
        'Oxygen Level': 'o2ring_spo2',
        'Pulse Rate': 'o2ring_pulse',
        'Motion': 'o2ring_motion'
    }

    # Create a new DataFrame with only the columns we want
    new_df = pd.DataFrame()
    for old_col, new_col in numeric_columns.items():
        new_df[new_col] = pd.to_numeric(df[old_col], errors='coerce')

    # Resample to 1-minute intervals by taking the mean
    return new_df.resample('min').mean()

def merge_data(pulse_df, spo2_df, o2ring_df):
    """
    Merge all dataframes into a single dataframe with 1-minute resolution
    """
    # Find the common time range
    start_time = max(pulse_df.index.min(), spo2_df.index.min(), o2ring_df.index.min())
    end_time = min(pulse_df.index.max(), spo2_df.index.max(), o2ring_df.index.max())

    # Trim all dataframes to the common time range
    pulse_df = pulse_df[start_time:end_time]
    spo2_df = spo2_df[start_time:end_time]
    o2ring_df = o2ring_df[start_time:end_time]

    # Merge all dataframes
    merged_df = pd.concat([pulse_df, spo2_df, o2ring_df], axis=1)

    return merged_df

def main():
    parser = argparse.ArgumentParser(description='Parse Garmin and O2Ring files from a directory')
    parser.add_argument('directory', type=str, help='Directory containing the files to parse')
    parser.add_argument('--output', type=str, default='merged_data.csv',
                      help='Output CSV file name (default: merged_data.csv)')

    args = parser.parse_args()

    try:
        # Find the files
        pulse_file, spo2_file, o2ring_file = find_files(args.directory)

        # Parse each file
        print("Parsing files...")
        pulse_df = parse_garmin_pulse(pulse_file)
        print(f"Parsed pulse file: {pulse_file}")

        spo2_df = parse_garmin_spo2(spo2_file)
        print(f"Parsed SpO2 file: {spo2_file}")

        o2ring_df = parse_o2ring_csv(o2ring_file)
        print(f"Parsed O2Ring file: {o2ring_file}")

        # Merge the data
        print("Merging data...")
        merged_df = merge_data(pulse_df, spo2_df, o2ring_df)

        # Save to CSV
        output_path = os.path.join(args.directory, args.output)
        merged_df.to_csv(output_path)
        print(f"Saved merged data to: {output_path}")

        # Print some statistics
        print("\nData Summary:")
        print(f"Time range: {merged_df.index.min()} to {merged_df.index.max()}")
        print(f"Total records: {len(merged_df)}")
        print("\nColumns in merged data:")
        for col in merged_df.columns:
            print(f"- {col}")

    except IndexError:
        print("Error: Could not find all required files in the directory.")
        print("Please ensure the directory contains:")
        print("- One Garmin pulse file (garmin*-pulse.json)")
        print("- One Garmin SpO2 file (garmin*-spo2.json)")
        print("- One O2Ring file (O2Ring_*.csv)")
        exit(1)

if __name__ == "__main__":
    main()
