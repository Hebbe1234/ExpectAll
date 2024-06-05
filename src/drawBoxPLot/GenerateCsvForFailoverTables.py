import json
import csv

# Manipulate data as needed
def manipulate_data(json_data):
    # Example manipulation: Extract specific fields
    manipulated_data = []
    for item in json_data:
        manipulated_item = {
            'field1': item['field1'],
            'field2': item['field2'],
            # Add more fields or manipulate existing ones
        }
        manipulated_data.append(manipulated_item)
    return manipulated_data

# Save data as CSV
def save_as_csv(data, csv_file):
    with open(csv_file, 'w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
# Example usage
import json
import os
import json
import os
import csv

def load_json(file_path):
    """Load JSON data from a file."""
    with open(file_path, 'r') as file:
        data = json.load(file)
    return data

if __name__ == "__main__":
    graphs = ["table_data_dt", "table_data_kanto"]
    names = ["EdgeTop"]
    json_extension = ".json"

    for graph in graphs:
        graphFolderName = graph + "_Percentage"
        # Make folder if not exist
        if not os.path.exists(graphFolderName):
            os.makedirs(graphFolderName)

        for name in names:
            data = load_json(graph + name + json_extension)
            StringArrayThing = []
            for data_for_single_demand in data:
                
                demand = data_for_single_demand["demands"]
                infeasible_count = data_for_single_demand["infeasable_count"]
                no_change_query_solved_counts = data_for_single_demand["no_change_query_solved_counts"]
                no_change_query_not_solved_but_feasible_counts = data_for_single_demand["no_change_query_not_solved_but_feasible_counts"]
                solve_percentage = []
                feasible_percentage = []
                for edge_fail_i in range(0, 5):
                    feasible_percentage2 = ((1000 - infeasible_count[edge_fail_i]) / 1000) * 100
                    feasible_percentage.append(feasible_percentage2)
                    success_percentage = (no_change_query_solved_counts[edge_fail_i] / 1000) * 100
                    solve_percentage.append(success_percentage)

                EntryForCsv = ["D" + str(demand)]
                for edge_fail_i in range(0, 5):
                    EntryForCsv.append(f"{solve_percentage[edge_fail_i]:.0f} / {feasible_percentage[edge_fail_i]:.0f}")
                
                StringArrayThing.append(EntryForCsv)

            fileName = "AllStuffAsCSV"
            # Store as a CSV
            with open(os.path.join(graphFolderName, graphFolderName + ".csv"), 'w', newline='') as result_file:
                writer = csv.writer(result_file)
                writer.writerow(["Demand", "FOne", "FTwo", "FThree", "FFour", "FFive"])
                for row in StringArrayThing:
                    writer.writerow(row)

