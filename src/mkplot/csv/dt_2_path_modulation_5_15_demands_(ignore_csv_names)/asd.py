import pandas as pd
import os
import matplotlib.pyplot as plt
#This is mostly AI generated :)
#if you get error remove the csv, and png file. 

# Function to read CSV files and calculate averages
def calculate_averages(csv_files):
    data = {}
    for file in csv_files:
        df = pd.read_csv(file)
        for demand_value, group in df.groupby('demands'):
            avg_solve_time = group['solve time'].mean()
            avg_all_time = group['all time'].mean()
            demand_value = int(demand_value)
            if demand_value not in data:
                data[demand_value] = {
                    'solve time': [],
                    'all time': [],
                    'file_count': 0
                }
            data[demand_value]['solve time'].append(avg_solve_time)
            data[demand_value]['all time'].append(avg_all_time)
            data[demand_value]['file_count'] += 1

    return data

# Function to create aggregate CSV file
def create_aggregate_csv(data, output_file):
    headers = ['demand', 'avg_solve_time', 'avg_all_time', 'file_count']
    with open(output_file, 'w') as f:
        f.write(','.join(headers) + '\n')
        for demand, stats in data.items():
            avg_solve_time = sum(stats['solve time']) / stats['file_count']
            avg_all_time = sum(stats['all time']) / stats['file_count']
            file_count = stats['file_count']
            f.write(f"{demand},{avg_solve_time},{avg_all_time},{file_count}\n")
# Function to create graph
def create_graph(data, output_file):
    demands = sorted(list(data.keys()))  # Sort demands
    avg_all_times = [data[d]['all time'][0] for d in demands]
    file_counts = [data[d]['file_count'] for d in demands]

    fig, ax1 = plt.subplots(figsize=(10, 6))

    ax1.plot(demands, avg_all_times, marker='o', linestyle='-', color='b')
    ax1.set_xlabel('Demands')
    ax1.set_ylabel('Average All Time', color='b')
    ax1.tick_params('y', colors='b')

    ax2 = ax1.twinx()
    ax2.bar(demands, file_counts, color='orange', alpha=0.5)
    ax2.set_ylabel('File Count', color='orange')
    ax2.tick_params('y', colors='orange')

    plt.title('Average All Time and File Count vs. Demands')
    plt.grid(True)
    plt.savefig(output_file)
    plt.close()

# Main function
def main():
    csv_files = [file for file in os.listdir('.') if file.endswith('.csv')]
    data = calculate_averages(csv_files)
    create_aggregate_csv(data, 'aggregate.csv')
    create_graph(data, 'graph.png')

if __name__ == "__main__":
    main()
