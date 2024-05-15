import os
import json
import matplotlib.pyplot as plt

# Define folder and file name variables
for i in range(1,4): 
    plt.clf()
    print(i)
    folder_name = "json2"
    edgeFail = i
    file_name = "EdgeFailover_"+str(edgeFail)+".json"  # Change this to your desired file name

    # Path to the folder containing JSON files
    folder_path = os.path.join(os.getcwd(), folder_name)

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
    plt.boxplot(data_values, whis=(0,100))

    # Adding labels
    plt.xlabel('demands')
    plt.ylabel('query time[s]')
    plt.title('Boxplot of Data')

    # Setting x-axis ticks
    plt.xticks(range(1, len(data) + 1), [item['demands'] for item in data])

    # Setting y-axis lower limit to 0
    plt.ylim(bottom=0)

    # Save the boxplot as a PNG file
    output_folder = "kantoEdgeTop"
    output_file_path = os.path.join(os.getcwd(), output_folder, file_name.replace(".json", "_boxplot.png"))
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    plt.savefig(output_file_path)

