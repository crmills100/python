# print lines from input file randomly

import random


# read lines into array
def read_lines_into_array(filename):
    lines = []
    # open file
    with open(filename, 'r', encoding='utf-8') as file:
        for line in file:
            lines.append(line.strip())  # Strip removes any extra whitespace including '\n'
    return lines

# randomly swap elements of list
def shuffle_array(arr):
    random.shuffle(arr)
    return arr




# Main:
filename = 'prompts.txt'  # file to read
lines = read_lines_into_array(filename)
shuffle_array(lines)


# print out lines
print("Lines read from", filename, ":")
for line in lines:
    print(line)