import matplotlib.pyplot as plt
import csv

# Function to read CSV file and extract data
def read_csv(filename):
    times = []
    demands = []
    with open(filename, 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            times.append(float(row['all time']))
            demands.append(int(row['demands']))
    return times, demands

# Main function to create plot
def create_plot(filename):
    times, demands = read_csv(filename)
    
    # Sort demands and corresponding times
    demands, times = zip(*sorted(zip(demands, times)))
    
    # Create plot
    plt.figure(figsize=(10, 6))
    plt.plot(demands, times, marker='o', linestyle='-')
    plt.title('All Time vs Demands')
    plt.xlabel('Demands')
    plt.ylabel('All Time')
    plt.grid(True)
    plt.show()
# Call the main function with the filename
create_plot('mip_limited_n_demands_dt_2_paths5.csv')  # Replace 'your_csv_file.csv' with the actual filename
