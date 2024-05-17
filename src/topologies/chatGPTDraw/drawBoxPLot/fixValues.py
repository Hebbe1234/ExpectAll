import json

# Read the JSON file
for i in range(1,4):
    fileTinh = "json2/EdgeFailover_"+str(i)+".json"
    with open(fileTinh, 'r') as file:
        data = json.load(file)

    # Iterate over each object in the JSON data
    for obj in data:
        # Iterate over each list of values in the "all_times" attribute
        for times_list in obj['all_times']:
            prev_value = times_list[0]  # Get the first value as the previous value
            # Iterate starting from the second value
            for i in range(1, len(times_list)):
                # Calculate the difference between the current value and the previous value
                times_list[i] -= prev_value
                prev_value += times_list[i]  # Update previous value for the next iteration

    # Write the modified data back to the JSON file
    with open(fileTinh, 'w') as file:
        json.dump(data, file, indent=4)
