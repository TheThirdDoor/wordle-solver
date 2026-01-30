#!/usr/bin/env python3
import sys
import os
import re
from collections import defaultdict

def analyze_log_file(file_path):
    total_guesses = 0
    solved_count = 0
    failed_words = []
    guess_distribution = defaultdict(int)
    
    try:
        with open(file_path, 'r') as file:
            for line in file:
                line = line.strip()
                # Check for successful solutions
                solution_match = re.match(r'Found solution for (\w+) in (\d+) guesses: \[([^\]]+)\]', line)
                if solution_match:
                    guess_count = int(solution_match.group(2))
                    total_guesses += guess_count
                    solved_count += 1
                    guess_distribution[guess_count] += 1
                
                # Check for failed solutions
                failed_match = re.match(r'Could not find solution for (\w+)', line)
                if failed_match:
                    failed_words.append(failed_match.group(1))
        
        # Calculate and display statistics
        if solved_count > 0:
            avg_guesses = total_guesses / solved_count
            print(f"\n--- Solution Statistics ---")
            print(f"Average guesses per solution: {avg_guesses:.2f}")
            print("\nGuess distribution:")
            for guess_count in sorted(guess_distribution.keys()):
                print(f"  {guess_count} guesses: {guess_distribution[guess_count]} words")
        else:
            print("No successful solutions found in the log file.")
        
        if failed_words:
            print(f"\nFailed to find solutions for {len(failed_words)} words:")
            print(", ".join(failed_words))
        
        print(f"\n--- Summary ---")
        print(f"Total words processed: {solved_count + len(failed_words)}")
        print(f"Successfully solved: {solved_count}")
        print(f"Failed to solve: {len(failed_words)}")
        
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
        sys.exit(1)

def main():
    # Use provided log file or default to 'log.txt' in script directory
    if len(sys.argv) > 1:
        log_file = sys.argv[1]
    else:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        log_file = os.path.join(script_dir, 'log.txt')
    
    print(f"Analyzing log file: {log_file}")
    analyze_log_file(log_file)

if __name__ == "__main__":
    main()