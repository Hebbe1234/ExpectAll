import os
import json
import matplotlib.pyplot as plt

# Define folder and file name variables
for i in range(1,4): 
    plt.clf()
    print(i)
    folder_name1 = "json1"
    folder_name2 = "json2"
    edgeFail = i
    file_name = "EdgeFailover_"+str(edgeFail)+".json"  # Change this to your desired file name

    # Path to the folder containing JSON files
    folder_path1 = os.path.join(os.getcwd(), folder_name1)
    folder_path2 = os.path.join(os.getcwd(), folder_name2)

    # Path to the selected JSON file
    file_path1 = os.path.join(folder_path1, file_name)
    file_path2 = os.path.join(folder_path2, file_name)

    # Open the JSON file and load the data
    with open(file_path1, 'r') as file:
        data1 = json.load(file)
    with open(file_path2, 'r') as file:
        data2 = json.load(file)

    # Sort data based on the "demands" value
    data1.sort(key=lambda x: x['demands'])
    data2.sort(key=lambda x: x['demands'])

    # Extracting the data into a list of lists
    data_values1 = [item['all_times'][0] for item in data1]
    data_values2 = [item['all_times'][0] for item in data2]

    # Creating the boxplot
    plt.boxplot(data_values1, whis=(0,100))
    plt.boxplot(data_values2, whis=(0,100))

    # Adding labels
    plt.xlabel('demands')
    plt.ylabel('query time[s]')
    plt.title('Boxplot of Data')

    # Setting x-axis ticks
    plt.xticks(range(1, len(data1) + 1), [item['demands'] for item in data1])

    # Setting y-axis lower limit to 0

    # Save the boxplot as a PNG file
    output_folder = "AAAA"
    output_file_path = os.path.join(os.getcwd(), output_folder, file_name.replace(".json", "_boxplot.png"))
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    plt.savefig(output_file_path)

