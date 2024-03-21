import csv
import matplotlib.pyplot as plt

# Read data from CSV file
file_path = "kanto_2_path.csv"  # File path to your CSV file
demands = []
all_time = []

with open(file_path, newline='') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        demands.append(int(row['demands']))
        all_time.append(float(row['all time']))

# Create the plot
plt.plot(demands, all_time, marker='o', linestyle='-')

# Add labels and title
plt.xlabel('Demands')
plt.ylabel('All Time')
plt.title('All Time vs Demands')

# Display the plot
plt.grid(True)
plt.tight_layout()

# Save the plot as a PNG file
plt.savefig('kanto_2_path.png')

# Show the plot (optional)
plt.show()
