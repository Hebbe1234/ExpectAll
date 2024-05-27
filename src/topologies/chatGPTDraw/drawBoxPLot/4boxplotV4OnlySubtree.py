import os
import json
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import copy

def multer(data, multiplier):
    # Create a deep copy of the input list of lists
    data_copy = copy.deepcopy(data)
    
    # Multiply each element by the multiplier
    for i in range(len(data_copy)):
        for j in range(len(data_copy[i])):
            data_copy[i][j] = data_copy[i][j] * multiplier
            
    return data_copy


# Define folder and file name variables
topology2 = ["dt","kanto"]
things = ["all_times", "subtree_times"]
whatToShow = "subtree_times"
for topologyName in topology2: 
        
    for i in range(1, 6):
        plt.clf()
        print(i)
        folder_name1 = topologyName + "Ands"
        folder_name2 = topologyName + "EdgeTop"
        edgeFail = i
        file_name = "EdgeFailover_" + str(edgeFail) + ".json"  # Change this to your desired file name

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
        data_values1 = [item[whatToShow][0] for item in data1]
        data_values2 = [item[whatToShow][0] for item in data2]

        # data_values1 = multer(data_values1,1000)
        # data_values2 = multer(data_values2,1000)

        # Determine the maximum length of the datasets
        max_length = max(len(data1), len(data2))

        # Generate positions based on the maximum length
        positions1 = list(range(1, max_length + 1))
        positions2 = [pos + 0.30 for pos in positions1]
        positions3 = [(pos1+pos2)/2 for pos1,pos2 in zip(positions1,positions2)]


        plt.figure(figsize=(18, 8))

        # Create the boxplots, using only existing data positions
        plt.boxplot(data_values1, positions=positions1[:len(data1)], whis=(0, 100), boxprops=dict(color="blue"), whiskerprops=dict(color="blue", linestyle='-'), widths=0.23)
        plt.boxplot(data_values2, positions=positions2[:len(data2)], whis=(0, 100), boxprops=dict(color="red", linestyle='--'), whiskerprops=dict(color="red", linestyle='--'), widths=0.23)

        # Adding labels with increased fontsize
        plt.xlabel('Demands', fontsize=30)
        plt.ylabel('Pruning time[s]', fontsize=30)
        topologydislpayname = topologyName
        if topologydislpayname != "dt":
            topologydislpayname += "11"
        plt.title('Topology:' + topologydislpayname, fontsize=36)
        print("hsdfhsdf")

        # Set x-axis ticks only for the first dataset (assuming it's the main dataset)
        plt.xticks(positions3[:len(data1)], [item['demands'] for item in data1], fontsize=28)
        plt.yticks(fontsize=28)  # For y-axis ticks

        # Setting y-axis lower limit to 0
        plt.yscale("log")
        plt.axhline(y=50, color='gray', linestyle='--')
        plt.axhline(y=200, color='gray', linestyle='-.')

        # Creating custom legend
        legend_elements = [
            Line2D([0], [0], color='blue', lw=2, label='Deletion'),
            Line2D([0], [0], color='red', linestyle='--', lw=2, label='Pre-computation')]
        #CAN BE ADDED TO MAKE GRAPH SMALLER: 
        #plt.subplots_adjust(top=0.7)


        # Adjust layout to add more space at the bottom
        plt.subplots_adjust(bottom=0.00001)

        # Adjust legend position
        plt.legend(handles=legend_elements, loc='upper center', bbox_to_anchor=(0.5, -0.12), fontsize=26, ncol=3)

        # Save the boxplot as a PNG file
        output_folder = "ABABAB_"+topologyName+"_"+whatToShow
        output_file_path = os.path.join(os.getcwd(), output_folder, file_name.replace(".json", "_boxplot.png"))
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
        plt.savefig(output_file_path, bbox_inches='tight')
