import pandas as pd
import os
import matplotlib.pyplot as plt

# Function to read CSV files and calculate averages
def calculate_averages(csv_files):
    data = {}
    for file in csv_files:
        df = pd.read_csv(file)
        for demand_value, group in df.groupby('demands'):
            avg_solve_time = group['solve time'].mean()
            avg_constraint_time = group['constraint time'].mean()
            avg_all_time = group['all time'].mean()
            demand_value = int(demand_value)
            if demand_value not in data:
                data[demand_value] = {
                    'solve time': [],
                    'constraint time': [],
                    'all time': [],
                    'file_count': 0
                }
            data[demand_value]['solve time'].append(avg_solve_time)
            data[demand_value]['constraint time'].append(avg_constraint_time)
            data[demand_value]['all time'].append(avg_all_time)
            data[demand_value]['file_count'] += 1

    return data

# Function to create aggregate CSV file
def create_aggregate_csv(data, output_file):
    headers = ['demand', 'avg_solve_time', 'avg_constraint_time', 'avg_all_time', 'file_count']
    with open(output_file, 'w') as f:
        f.write(','.join(headers) + '\n')
        for demand, stats in data.items():
            avg_solve_time = sum(stats['solve time']) / stats['file_count']
            avg_constraint_time = sum(stats['constraint time']) / stats['file_count']
            avg_all_time = sum(stats['all time']) / stats['file_count']
            file_count = stats['file_count']
            f.write(f"{demand},{avg_solve_time},{avg_constraint_time},{avg_all_time},{file_count}\n")

# Function to create graph
def create_graph(data, output_file):
    demands = list(data.keys())
    avg_all_times = [data[d]['all time'][0] for d in demands]
    
    plt.figure(figsize=(10, 6))
    plt.plot(demands, avg_all_times, marker='o', linestyle='-')
    plt.xlabel('Demands')
    plt.ylabel('Average All Time')
    plt.title('Average All Time vs. Demands')
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
