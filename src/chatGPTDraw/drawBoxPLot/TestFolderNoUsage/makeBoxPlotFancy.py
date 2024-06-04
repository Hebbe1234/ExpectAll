import os
import json
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

# Define folder and file name variables
for i in range(1, 6):
    plt.clf()
    print(i)
    topology = "kanto11"
    topologyName = "kanto"
    folder_name1 = topologyName+"Ands"
    folder_name2 = topologyName+"EdgeTop"
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
    data_values1 = [item['all_times'][0] for item in data1]
    data_values2 = [item['all_times'][0] for item in data2]

    # Creating the boxplots with different positions and colors
    positions1 = range(1, len(data1) + 1)

    positions2 = [pos + 0.30 for pos in positions1]  # Further offset


    plt.figure(figsize=(14, 8))

    plt.boxplot(data_values1, positions=positions1, whis=(0,100), boxprops=dict(color="blue"), widths=0.23) #DtAnds
    plt.boxplot(data_values2, positions=positions2, whis=(0,100), boxprops=dict(color="red", linestyle='--'), widths=0.23)  #Dt EdgeTOp

    # Adding labels
    # Adding labels with increased fontsize
    plt.xlabel('demands', fontsize=26)
    plt.ylabel('query time[s]', fontsize=26)
    plt.title('Topology:'+topology, fontsize=32)

    # Setting x-axis ticks with increased fontsize
    plt.xticks(positions1, [item['demands'] for item in data1], fontsize=20)
    plt.yticks(fontsize=20)  # For y-axis ticks


    # Setting y-axis lower limit to 0
    plt.yscale("log"    )
    plt.axhline(y=0.05, color='gray', linestyle='--')
    plt.axhline(y=0.2, color='gray', linestyle='-.')

    # Creating custom legend
    legend_elements = [Line2D([0], [0], color='blue', lw=2, label='Path failure querying'),
                    Line2D([0], [0], color='red',linestyle='--', lw=2, label='Link failure querying')]

    plt.legend(handles=legend_elements, loc='upper left', fontsize=20)

    # Save the boxplot as a PNG file
    output_folder = "AAAA"
    output_file_path = os.path.join(os.getcwd(), output_folder, file_name.replace(".json", "_boxplot.png"))
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    plt.savefig(output_file_path, bbox_inches='tight')

