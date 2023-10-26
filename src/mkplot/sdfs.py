import os
import json

# Initialize a dictionary to store the data

data = {}

# Set the directory path where your data is located
data_directory = "../../out/mip"

text_file_count = 0
for root, dirs, files in os.walk(data_directory):
    for directory in dirs:
        directory_path = os.path.join(root, directory)
        
        # Iterate through files in the subdirectory
        for filename in os.listdir(directory_path):
            if filename.endswith(".txt"):
                number_of_demands = filename.split("output")[1].split(".txt")[0]
                data[str(number_of_demands)] = {"stats":{}}
        break
    break
    

# Function to parse the content of a text file
def parse_txt_file(file_path):
    print(file_path)
    with open(file_path, "r") as file:
        lines = file.readlines()

    if len(lines) >= 2:
        solve_time, all_time, solvable = map(str.strip, lines[1].split(","))
        return {
            "status": True,
            "rtime": float(solve_time),
            "mempeak": "1 KiB"
        }
    else:
        return None

# Recursively walk through the directory and its subdirectories
for root, dirs, files in os.walk(data_directory):
    instanceNumber = 0
    for directory in dirs:
        instanceNumber += 1
        directory_path = os.path.join(root, directory)
        for filename in os.listdir(directory_path):
            file_path = os.path.join(directory_path,filename)

            number_of_demands = filename.split("output")[1].split(".txt")[0]

            # Use the file name (without extension) as the dictionary key
            instance_name = os.path.splitext("instance"+str(instanceNumber))[0]
            # Parse the content of the text file
            instance_data = parse_txt_file(file_path)

            print("h")
            if instance_data is not None:
                data[str(number_of_demands)]["stats"][instance_name] = instance_data


# Convert the data dictionary to a JSON object
json_data = json.dumps(data, indent=4)



# Print or save the JSON data as needed
print(json_data)


# Define the preamble information


# Iterate through your data dictionary and update each section with the preamble
for key, section in data.items():
    preamble_info = {
    "preamble": {
        "benchmark": "ttt" ,
        "prog_args": None,
        "program": "another-good-tool",
        "prog_alias": "number of demands :)" + str(key)
    }
}
    section.update(preamble_info)

    # Create a JSON file for each section
    file_name = f"plots{key}.json"
    with open(file_name, "w") as json_file:
        json.dump(section, json_file, indent=4)