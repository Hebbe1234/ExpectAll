import matplotlib.pyplot as plt

# Create the main figure with constrained layout
fig = plt.figure(constrained_layout=True,  figsize=(18, 6))

# Create subfigures grid based on the number of different values for the changing parameters
subfigs = fig.subfigures(1, 3)

# Iterate over subfigures for changing parameters as columns
for col, value_of_parameter2 in enumerate(["SHORTEST", "DISJOINT", "DEFAULT"]):
    # Create subplots grid for the original plots with changing parameters as rows
    axs = subfigs[col].subplots(2, 1)
    
    # Iterate over subplots for original plots with changing parameters as rows
    for row, value_of_parameter1 in enumerate([1, 2]):
        # Extract subset data (dummy data for this example)
        subset_data = {1: [1, 2, 3], 2: [1, 4, 9]}
        
        # Plot run time data for each seed on the subplot
        for seed in [1, 2]:
            # Extract run time data for the current seed
            run_times = subset_data[seed]
            
            # Plot run time data on the subplot
            axs[row].plot([1, 2, 3], run_times, label=f"Seed {seed}")
        
        # Set labels and title for the subplot
        axs[row].set_xlabel("Number of Demands")
        axs[row].set_ylabel("Run Time")
        axs[row].set_title(f"Number of Paths: {value_of_parameter1}, Path Type: {value_of_parameter2}")
        
        # Add legend (optional)
        axs[row].legend()

# Show or save plot
plt.show()
