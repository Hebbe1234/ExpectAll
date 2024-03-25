import copy
import matplotlib.pyplot as plt

def extend_lists(input_list):
    max_value = max(input_list) + 1
    result = []
    for i in range(max_value+1):
        new_list = copy.deepcopy(input_list)
        new_list.append(i)
        result.append(new_list)
    return result
    
    
def keep_going(input):
    new_list = []
    for l in input: 
        new_list.extend(extend_lists(l))
    return new_list
    

def main():
    s_lengths = []  # List to store lengths of s
    s = [[0]]
    for i in range(0, 10):
        s = keep_going(s)
        s_lengths.append(len(s))  # Append length of s for each iteration
        print(len(s))

    # Plotting
    plt.plot(range(10), s_lengths, marker='o')  # Plotting i vs length of s
    plt.xlabel('i')
    plt.ylabel('Length of s')
    plt.title('Length of s vs i')
    plt.grid(True)
    plt.show()

if __name__ == "__main__":
    main()