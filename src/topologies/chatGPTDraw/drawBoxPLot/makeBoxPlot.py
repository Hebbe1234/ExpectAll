import os
import json
import matplotlib.pyplot as plt

# Path to the folder containing JSON files
folder_path = "json2"

# List all files in the folder
files = os.listdir(folder_path)

# Choose a file from the list
file_name = files[0]  # You can change this to select a different file if needed

# Path to the selected JSON file
file_path = os.path.join(folder_path, file_name)

# Open the JSON file and load the data
with open(file_path, 'r') as file:
    data = json.load(file)

# Sort data based on the "demands" value
data.sort(key=lambda x: x['demands'])

# Extracting the data into a list of lists
data_values = [item['all_times'][0] for item in data]

# Creating the boxplot
plt.boxplot(data_values)

# Adding labels
plt.xlabel('demands')
plt.ylabel('query time[s]')
plt.title('Boxplot of Data')

# Setting x-axis ticks
plt.xticks(range(1, len(data) + 1), [item['demands'] for item in data])

# Setting y-axis lower limit to 0
plt.ylim(bottom=0)

# Displaying the plot
plt.show()
