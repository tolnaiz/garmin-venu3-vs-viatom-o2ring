import pandas as pd
import matplotlib.pyplot as plt
import argparse
from datetime import datetime
import seaborn as sns
import numpy as np

def load_data(file_path):
    """
    Load the merged CSV file and parse the timestamp index
    """
    df = pd.read_csv(file_path)
    df['timestamp'] = pd.to_datetime(df.iloc[:, 0])  # First column is the timestamp
    df.set_index('timestamp', inplace=True)
    return df

def plot_data(df, output_path=None):
    """
    Create plots from the merged data
    """
    # Set the style
    sns.set_style("whitegrid")
    plt.style.use('default')

    # Create a figure with subplots
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10), height_ratios=[1, 1])
    fig.suptitle('Garmin venu 3 vs O2Ring Measurements', fontsize=16)

    # Function to add motion background to plots
    def add_motion_background(ax):
        motion = df['o2ring_motion']
        if not motion.empty:
            # Normalize motion values to [0, 1] for alpha
            motion_norm = motion / motion.max()
            # Create spans for each time point
            for i in range(len(df)-1):
                ax.axvspan(df.index[i], df.index[i+1],
                          color='yellow', alpha=motion_norm.iloc[i] * 0.3)

    # Plot 1: SpO2 Comparison
    add_motion_background(ax1)
    sns.lineplot(data=df, x=df.index, y='garmin_spo2', ax=ax1, label='Garmin SpO2', alpha=0.7, color='blue')
    sns.lineplot(data=df, x=df.index, y='o2ring_spo2', ax=ax1, label='O2Ring SpO2', alpha=0.7, color='red')

    # Add scatter plots for each confidence level
    confidence_levels = df['garmin_confidence'].dropna().unique()
    colors = plt.cm.viridis(np.linspace(0, 1, len(confidence_levels)))

    for level, color in zip(confidence_levels, colors):
        mask = df['garmin_confidence'] == level
        ax1.scatter(df[mask].index, df[mask]['garmin_spo2'],
                   c=[color], s=20, alpha=0.7,
                   label=f'Confidence Level {level}')

    ax1.set_ylabel('SpO2 (%)')
    ax1.set_title('SpO2 Measurements Comparison')
    ax1.legend(bbox_to_anchor=(1.05, 1), loc='upper left')

    # Plot 2: Heart Rate Comparison
    add_motion_background(ax2)
    sns.lineplot(data=df, x=df.index, y='heart_rate', ax=ax2, label='Garmin HR', alpha=0.7, color='blue')
    sns.lineplot(data=df, x=df.index, y='o2ring_pulse', ax=ax2, label='O2Ring HR', alpha=0.7, color='red')
    ax2.set_ylabel('Heart Rate (bpm)')
    ax2.set_xlabel('Time')
    ax2.set_title('Heart Rate Measurements Comparison')
    ax2.legend()

    # Format x-axis for both plots
    for ax in [ax1, ax2]:
        # Set 10-minute intervals
        interval = pd.Timedelta(minutes=10)
        start_time = df.index.min().floor('10min')
        end_time = df.index.max().ceil('10min')
        xticks = pd.date_range(start=start_time, end=end_time, freq='10min')
        ax.set_xticks(xticks)
        # Format timestamps as HH:MM
        ax.xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter('%H:%M'))
        # Rotate labels for better readability
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')

    # Add motion level information to legend
    motion = df['o2ring_motion']
    if not motion.empty:
        # Add motion statistics as text
        motion_stats = motion.agg(['mean', 'max']).round(2)
        stats_text = f'Motion Level (mean/max): {motion_stats["mean"]}/{motion_stats["max"]}'
        fig.text(0.02, 0.02, stats_text, fontsize=8)

    # Adjust layout to accommodate the legend and rotated labels
    plt.tight_layout()

    # Save or show the plot
    if output_path:
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"Plot saved to: {output_path}")
    else:
        plt.show()

    # Print confidence level statistics
    print("\nGarmin SpO2 Confidence Level Statistics:")
    confidence_stats = df.groupby('garmin_confidence')['garmin_spo2'].agg(['count', 'mean', 'std']).round(2)
    print(confidence_stats)

    # Print motion statistics
    if not motion.empty:
        print("\nMotion Level Statistics:")
        motion_stats = motion.agg(['count', 'mean', 'std', 'max']).round(2)
        print(f"Total measurements: {motion_stats['count']}")
        print(f"Mean motion level: {motion_stats['mean']}")
        print(f"Max motion level: {motion_stats['max']}")
        print(f"Motion std dev: {motion_stats['std']}")

def main():
    parser = argparse.ArgumentParser(description='Plot merged Garmin and O2Ring data')
    parser.add_argument('input_file', type=str, help='Input CSV file with merged data')
    parser.add_argument('--output', type=str, help='Output image file (optional)')

    args = parser.parse_args()

    # Load the data
    print(f"Loading data from {args.input_file}...")
    df = load_data(args.input_file)

    # Create plots
    print("Creating plots...")
    plot_data(df, args.output)

    # Print some basic statistics
    print("\nData Summary:")
    print(f"Time range: {df.index.min()} to {df.index.max()}")
    print("\nMean values:")
    print(f"Garmin SpO2: {df['garmin_spo2'].mean():.1f}%")
    print(f"O2Ring SpO2: {df['o2ring_spo2'].mean():.1f}%")
    print(f"Garmin HR: {df['heart_rate'].mean():.1f} bpm")
    print(f"O2Ring HR: {df['o2ring_pulse'].mean():.1f} bpm")

if __name__ == "__main__":
    main()