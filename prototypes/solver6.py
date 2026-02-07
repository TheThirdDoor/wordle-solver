from math import log
import re
import sys
import argparse
import multiprocessing
from functools import partial

def load_word_list(file_path):
    with open(file_path, 'r') as file:
        return [line.strip() for line in file.readlines()]

# Load word lists
all_words = load_word_list('lists/combined.txt')

def get_word_score_for_answer(guess: str, answer: str) -> str:
    # Initialize the result with all 'B's (default to not in word)
    result = ['B'] * len(guess)
    
    # Convert to lists for easier manipulation
    guess_chars = list(guess)
    answer_chars = list(answer)
    
    # First pass: mark correct positions (G)
    for i in range(len(guess_chars)):
        if i < len(answer_chars) and guess_chars[i] == answer_chars[i]:
            result[i] = 'G'
            # Mark as used by setting to None
            answer_chars[i] = None
            guess_chars[i] = None
    
    # Second pass: mark correct letters in wrong positions (Y)
    for i in range(len(guess_chars)):
        if guess_chars[i] is not None and guess_chars[i] in answer_chars:
            result[i] = 'Y'
            # Remove the first occurrence from answer_chars to handle duplicates
            answer_chars[answer_chars.index(guess_chars[i])] = None
    
    return ''.join(result)

def get_bucket_count(guess : str, possible_answers : list[str]):
    results = dict[str, int]()

    for answer in possible_answers:
        score = get_word_score_for_answer(guess, answer)
        if score not in results:
            results[score] = 0
        results[score] += 1
    
    score = 0.0

    for result in results.keys():
        score += 1 / (log(results[result]) + 0.1)

    if guess in possible_answers:
        score += 1
    
    #print(f"Bucket count for {guess} = {len(results)}")
    return (score, guess)

def get_best_guess(possible_guesses : list[str], possible_answers : list[str]) -> str:
    if len(possible_answers) == 0:
        print("No possible answers")
        exit()

    if len(possible_answers) == 1:
        return possible_answers[0]

    worker_func = partial(get_bucket_count, possible_answers=possible_answers)

    with multiprocessing.Pool(processes = 8) as pool:
        results = pool.map(worker_func, possible_guesses)

    # Find the guess with the maximum bucket count
    bucket_count, best_guess = max(results)
    return best_guess

def check_answers_against_guess(guess: str, possible_answers: list[str]) -> dict[str, list[str]]:
    results = {}
    for answer in possible_answers:
        score = get_word_score_for_answer(guess, answer)
        if score not in results:
            results[score] = []
        results[score].append(answer)
    return results

def recursive_check():
    layers : list[dict[str, list[str]]] = []
    solved_data = [0] * (maxdepth + 1)  # Initialize with zeros for each depth
    for i in range(maxdepth + 1):
        layers.append({})
    layers[0][""] = answers

    for d in range(maxdepth):
        for group in layers[d].keys():
            best_guess = get_best_guess(all_words, layers[d][group])
            next_layer = check_answers_against_guess(best_guess, layers[d][group])
            for result in next_layer.keys():
                if result == "GGGGG":
                    print(f"Solution for {next_layer[result][0]}:{group} {best_guess}")
                    solved_data[d] += 1
                    continue
                key = f"{group} {best_guess} {result}"
                layers[d+1][key] = next_layer[result]
    
    # Calculate statistics
    total_solved = sum(solved_data)
    total_answers = total_solved + (sum(len(group) for group in layers[maxdepth].values()) if maxdepth < len(layers) - 1 else 0)
    
    print("\n=== Solver Statistics ===")
    print(f"Total answers: {total_answers}")
    print(f"Total solved: {total_solved} ({total_solved/total_answers*100:.2f}%)")
    
    # Calculate and print average depth
    depth_sum = sum(depth * count for depth, count in enumerate(solved_data, 1))
    avg_depth = depth_sum / total_solved if total_solved > 0 else 0
    print(f"Average depth: {avg_depth:.2f}")
    
    # Print solved by depth
    print("\nSolved by depth:")
    print("Depth | Count  | % of Total | % of Solved | Cumul. %")
    print("------|--------|------------|-------------|----------")
    cumulative_solved = 0
    for depth in range(1, maxdepth + 1):
        count = solved_data[depth - 1] if depth - 1 < len(solved_data) else 0
        cumulative_solved += count
        print(f"{depth:5d} | {count:6d} | {count/total_answers*100:9.2f}% | {count/total_solved*100:10.2f}% | {cumulative_solved/total_answers*100:7.2f}%")
    
    if len(layers[maxdepth]) > 0:
        unsolved_answers = 0
        print("Unsolved answers:")
        for key in layers[maxdepth + 1].keys():
            for answer in layers[maxdepth + 1][key]:
                print(f"  {key}: {answer}")
                unsolved_answers += 1
        print(f"Total unsolved answers: {unsolved_answers}")
    
    print("=" * 50 + "\n")

def parse_arguments():
    parser = argparse.ArgumentParser(description='Wordle Solver')
    parser.add_argument('-depth', type=int, default=6,
                      help='Maximum depth for the solver (default: 6)')
    parser.add_argument('-test', '--test-answers', dest='test_answers_file',
                      help='File containing test answers to override the default answers list')
    parser.add_argument('-solved', '--solved-answers', dest='solved_answers_file',
                      help='File containing already solved answers to remove from the answers list')
    
    # Handle both -test-answers and -testanswers formats
    args, unknown = parser.parse_known_args()
    for arg in unknown:
        if arg.startswith('-testanswers='):
            args.test_answers_file = arg.split('=', 1)[1]
        elif arg.startswith('-solvedanswers='):
            args.solved_answers_file = arg.split('=', 1)[1]
    
    return args

# Parse command line arguments
args = parse_arguments()

# Set max depth from arguments
maxdepth = args.depth
if maxdepth <= 0:
    print("Error: Depth must be a positive integer")
    sys.exit(1)

# Load word lists
all_words = load_word_list('lists/combined.txt')
answers = load_word_list('lists/answers.txt')

# Override answers with test answers if specified
if args.test_answers_file:
    try:
        answers = load_word_list(args.test_answers_file)
        print(f"Loaded {len(answers)} test answers from {args.test_answers_file}")
    except Exception as e:
        print(f"Error loading test answers file: {e}")
        sys.exit(1)

# Remove solved answers if specified
if args.solved_answers_file:
    try:
        solved = set(load_word_list(args.solved_answers_file))
        answers = [word for word in answers if word not in solved]
        print(f"Removed {len(solved)} solved answers. Remaining: {len(answers)}")
    except Exception as e:
        print(f"Error loading solved answers file: {e}")
        sys.exit(1)

# Print the number of words in the combined list
print(f"Number of words in combined.txt: {len(all_words)}")
print(f"Number of answer words: {len(answers)}")

def run():
    recursive_check()
    #best_guess = get_best_guess(all_words, answers)
    #print(f"Best guess: {best_guess}")

if __name__ == "__main__":
    run()