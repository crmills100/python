import random
import sys

def print_file_lines_random_order(filename):
    # Read all lines from the file
    with open(filename, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Shuffle the lines
    random.shuffle(lines)
    
    # Print each line without adding extra newlines
    for line in lines:
        print(line.rstrip())

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <file_path>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    print_file_lines_random_order(file_path)