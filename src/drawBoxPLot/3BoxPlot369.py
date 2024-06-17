import os
import json
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import copy

from matplotlib.ticker import MaxNLocator

def multer(data, multiplier):
    # Create a deep copy of the input list of lists
    data_copy = copy.deepcopy(data)
    
    # Multiply each element by the multiplier
    for i in range(len(data_copy)):
        for j in range(len(data_copy[i])):
            data_copy[i][j] = data_copy[i][j] * multiplier
            
    return data_copy

# Define folder and file name variables
topologies = ["dt","kanto"]
source_dirs = ["../../out/Reproduceability/EXPERIMENT_FAILOVER_MIP_FINAL_RUN_1"]

whatToShow = "all_times"
for source_dir in source_dirs:
    for topologyName in topologies: 
        data_for_plotting_dict = {}

        for kkk in range(0,9): 
                
            data_for_plotting = []

            for i in range(1, 6):
                plt.clf()
                folder_name = source_dir+"_"+topologyName 
                edgeFail = i
                file_name = "EdgeFailover_" + str(edgeFail) + ".json"  # Change this to your desired file name

                # Path to the folder containing JSON files
                folder_path3 = os.path.join(os.getcwd(), folder_name)

                # Path to the selected JSON file
                file_path3 = os.path.join(folder_path3, file_name)

                # Open the JSON file and load the data
                with open(file_path3, 'r') as file:
                    data3 = json.load(file)

                # Sort data based on the "demands" value
                data = data3[kkk]["all_times"][0]  #Find the alltimes for demand 5. 
                data_for_plotting.append(data)

            data_for_plotting_dict[kkk] = data_for_plotting

            # Extracting the data into a list of lists
        print(len(data_for_plotting_dict))
        data_values1 = data_for_plotting_dict[2]
        data_values2 = data_for_plotting_dict[5]
        data_values3 =  data_for_plotting_dict[8]

        # Determine the maximum length of the datasets
        max_length = max(len(data_values1), len(data_values2), len(data_values3))
        posser = 0.22
        # Generate positions based on the maximum length
        positions1 = list(range(1, max_length + 1))
        positions2 = [pos + posser for pos in positions1]
        positions3 = [pos + posser for pos in positions2]


        plt.figure(figsize=(16, 7))
        width =0.16
        # Create the boxplots, using only existing data positions
        plt.boxplot(data_values1, positions=positions1[:len(data_values1)], whis=(0, 100), boxprops=dict(color="blue"), whiskerprops=dict(color="blue", linestyle='-'), widths=width)
        plt.boxplot(data_values2, positions=positions2[:len(data_values2)], whis=(0, 100), boxprops=dict(color="red", linestyle='--'), whiskerprops=dict(color="red", linestyle='--'), widths=width)
        plt.boxplot(data_values3, positions=positions3[:len(data_values3)], whis=(0, 100), boxprops=dict(color="green", linestyle='-.'), whiskerprops=dict(color="green", linestyle='-.'), widths=width)

        # Adding labels with increased fontsize
        plt.xlabel('Link failures', fontsize=16*2)
        plt.ylabel('Query time[s]', fontsize=16*2)

        # Set x-axis ticks only for the first dataset (assuming it's the main dataset)
        plt.xticks(positions2[:len(data_values2)], [str(i) for i in range(1, len(data_values2) + 1)], fontsize=16*2)  # Adjusted xticks to match positions2
        plt.yticks(fontsize=16*2)  # For y-axis ticks

        # Setting y-axis lower limit to 0
        # plt.yscale("log")
        plt.axhline(y=0.05, color='gray', linestyle='--')
        plt.axhline(y=0.2, color='gray', linestyle='-.')

        # # Creating custom legend
        legend_elements = [
            Line2D([0], [0], color='blue', lw=2, label='3 Demands'),
            Line2D([0], [0], color='red', linestyle='--', lw=2, label='6 Demands'),
            Line2D([0], [0], color='green', linestyle='-.', lw=2, label='9 Demands')
        ]
        # plt.subplots_adjust(top=1.3)
        # Adjust layout to add more space at the bottom
        plt.subplots_adjust(bottom=0.00001)

        # Adjust legend position
        plt.legend(handles=legend_elements, loc='upper center', bbox_to_anchor=(0.5, -0.18), fontsize=16*2, ncol=3)
        plt.gca().yaxis.set_major_locator(MaxNLocator(integer=True))  # 
        plt.gca().set_ylim(bottom=0, top=4.5)

        # Save the boxplot as a PNG file
        output_folder = "Single369"+topologyName+"_"+whatToShow
        output_file_path = os.path.join(os.getcwd(), output_folder, topologyName+"_boxplot.png")
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
        plt.savefig(output_file_path, bbox_inches='tight')

