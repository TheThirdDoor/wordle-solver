import re
import sys
import argparse
import multiprocessing
from functools import partial
import math

def load_word_list(file_path):
    with open(file_path, 'r') as file:
        return [line.strip() for line in file.readlines()]

# Load word lists
all_words = load_word_list('lists/combined.txt')
strategy1cutoff = 2400
strategy2cutoff = 200
strategy3cutoff = 2
smart_space_words = 5

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

def get_bucket_score(guess: str, possible_answers: list[str]):
    results = {}
    
    # 1. Build Buckets
    for answer in possible_answers:
        pattern = get_word_score_for_answer(guess, answer)
        if pattern not in results:
            results[pattern] = 0
        results[pattern] += 1
    
    score = 0
    
    for count in results.values():
        score += 1
        if count == 1:
            score += 1.5

    if guess in possible_answers:
        score += 2.0

    return (score, guess)

def get_buckets(guess: str, possible_answers: list[str]) -> dict:
    buckets = {}
    for answer in possible_answers:
        pattern = get_word_score_for_answer(guess, answer)
        if pattern not in buckets:
            buckets[pattern] = []
        buckets[pattern].append(answer)
    return buckets

def get_smart_search_space(possible_answers: list[str]) -> list[str]:
    """
    Finds words that are most likely to distinguish between the remaining answers.
    """
    # 1. Identify letters that are present in ALL answers (Useless)
    # 2. Identify letters that are present in SOME answers (Discriminators)
    
    # Start with set of letters from first word, then intersect with rest
    common_letters = set(possible_answers[0])
    all_letters = set(possible_answers[0])
    
    for word in possible_answers[1:]:
        word_set = set(word)
        common_letters &= word_set # Intersection: Letters in ALL words
        all_letters |= word_set    # Union: Letters in ANY word
        
    # Discriminators are letters that exist, but not in every single word
    discriminators = all_letters - common_letters
    
    # If no discriminators exist (rare edge case of identical anagrams), 
    # fall back to possible_answers
    if not discriminators:
        return possible_answers

    # 3. Score ALL words based on how many discriminators they hit
    scored_guesses = []
    
    # We scan all_words (global list)
    for word in all_words:
        # Optimization: Don't check words that are definitely not the answer
        # if we already have the answer in our grasp, unless they are GREAT splitters.
        
        # Calculate overlap with discriminators
        # We use set intersection size as the score
        score = len(set(word) & discriminators)
        
        # Only keep words that hit at least 1 discriminator
        if score > 0:
            scored_guesses.append((score, word))

    # 4. Sort by score (descending) and take top K
    # We prioritize words that hit the MOST unique differentiating letters.
    scored_guesses.sort(key=lambda x: x[0], reverse=True)
    
    # Extract just the words
    best_burners = [x[1] for x in scored_guesses[:smart_space_words]]
    
    # ALWAYS include the actual possible answers in the search space
    # (The optimal move might be to just guess the answer!)
    final_list = set(possible_answers + best_burners)
    
    return list(final_list)

def strategy_entropy(guess: str, possible_answers: list[str]):
    results = {}
    for answer in possible_answers:
        pattern = get_word_score_for_answer(guess, answer)
        if pattern not in results:
            results[pattern] = 0
        results[pattern] += 1

    total_count = len(possible_answers)
    entropy = 0.0
    for count in results.values():
        p = count / total_count
        entropy += p * -math.log2(p)

    # Small bias for valid words (tie-breaker)
    if guess in possible_answers:
        entropy += 0.01

    # Return (Score, Guess). Higher is Better.
    return (entropy, guess)

def strategy_recursive_exact(possible_answers: list[str]):
    # This runs locally (no multiprocessing needed for N<8)
    memo = {}
    
    def get_min_total_turns(candidates):
        key = tuple(sorted(candidates))
        if key in memo: return memo[key]
        if len(candidates) == 1: return 1
        if len(candidates) == 2: return 3

        best_total = float('inf')
        
        # In endgame, we only check valid candidates to avoid "Burner Traps"
        # UNLESS we are stuck in a trap (e.g. SHA_E), then we need full search.
        # For speed, we stick to candidates first.
        search_space = candidates 

        for guess in search_space:
            current_total = len(candidates) # Cost of this guess
            buckets = {}
            # Local bucket logic for recursion speed
            for answer in candidates:
                p = get_word_score_for_answer(guess, answer)
                if p not in buckets: buckets[p] = []
                buckets[p].append(answer)

            for bucket in buckets.values():
                if guess in bucket: continue
                current_total += get_min_total_turns(bucket)

            if current_total < best_total:
                best_total = current_total
        
        memo[key] = best_total
        return best_total

    # Driver for the recursive strategy
    best_word = possible_answers[0]
    min_total = float('inf')

    # Note: For the top-level of endgame, we can check all_words 
    # if N is extremely small (e.g. < 5) to find burners.
    search_space = get_smart_search_space(possible_answers) 
    
    for guess in search_space:
        turns = len(possible_answers)
        buckets = {} 
        # ... (Same bucket logic as above) ...
        for answer in possible_answers:
            p = get_word_score_for_answer(guess, answer)
            if p not in buckets: buckets[p] = []
            buckets[p].append(answer)

        for bucket in buckets.values():
            if guess in bucket: continue
            turns += get_min_total_turns(bucket)
            
        if turns < min_total:
            min_total = turns
            best_word = guess
            
    return best_word

def strategy_weighted_buckets(guess: str, possible_answers: list[str]):
    results = {}
    for answer in possible_answers:
        pattern = get_word_score_for_answer(guess, answer)
        if pattern not in results:
            results[pattern] = 0
        results[pattern] += 1

    total_buckets = 0
    ones_count = 0
    
    for count in results.values():
        total_buckets += 1
        if count == 1:
            ones_count += 1
            
    # The 3.57 Formula: Prioritize Singles, then total buckets
    score = total_buckets + ones_count

    # Strong Candidate Bias: If we can win now, try it.
    if guess in possible_answers:
        score += 2.0

    # Return (Score, Guess). Higher is Better.
    return (score, guess)

def get_best_guess(possible_answers: list[str]) -> str:
    n = len(possible_answers)
    
    if n == 0: exit()
    if n == 1: return possible_answers[0]
    if n <= strategy3cutoff: return possible_answers[0]

    # --- LAYER 3: ENDGAME (Exact Solver) ---
    # When N is small, stop guessing and start solving.
    if n <= strategy2cutoff:
        worker_func = partial(get_bucket_score, possible_answers=possible_answers)

    # --- SELECT STRATEGY BASED ON GAME STATE ---
    # If it's the very first guess (or huge list), use Entropy
    if n > strategy1cutoff:
        print("Using Strategy: Entropy (Opener)")
        worker_func = partial(get_bucket_score, possible_answers=possible_answers)
    else:
        # For everything else, use your best-performing Aggressive logic
        # print("Using Strategy: Weighted Aggression")
        worker_func = partial(strategy_weighted_buckets, possible_answers=possible_answers)

    # --- EXECUTE PARALLEL SCAN ---
    with multiprocessing.Pool(processes=8) as pool:
        results = pool.map(worker_func, all_words)

    # Both Entropy and Weighted Buckets use "Higher is Better"
    best_score_tuple = max(results)
    
    # The guess is the last item in the tuple
    return best_score_tuple[-1]

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
        print(f"Working on guess {d + 1}")
        for group in layers[d].keys():
            best_guess = get_best_guess(layers[d][group])
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
    print("Depth | Count  | % of Total | Cumul. Count | Cumul. %")
    print("------|--------|------------|--------------|----------")
    cumulative_solved = 0
    for depth in range(1, maxdepth + 1):
        count = solved_data[depth - 1] if depth - 1 < len(solved_data) else 0
        cumulative_solved += count
        print(f"{depth:5d} | {count:6d} | {cumulative_solved:9d} | {count/total_solved*100:10.2f}% | {cumulative_solved/total_answers*100:7.2f}%")
    
    if len(layers[maxdepth]) > 0:
        unsolved_answers = 0
        print("Unsolved answers:")
        for key in layers[maxdepth].keys():
            for answer in layers[maxdepth][key]:
                print(f"  {key}: {answer}")
                unsolved_answers += 1
        print(f"Total unsolved answers: {unsolved_answers}")
    
    print("=" * 53 + "\n")

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