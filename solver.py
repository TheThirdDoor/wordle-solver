import re
import multiprocessing
from functools import partial

def load_word_list(file_path):
    with open(file_path, 'r') as file:
        return [line.strip() for line in file.readlines()]

# Load all words from combined.txt
all_words = load_word_list('lists/combined.txt')

# Load answer words from answers.txt
answers = load_word_list('lists/answers.txt')

# Load test answer words from test_answers.txt
test_answers = load_word_list('lists/test_answers.txt')

# Load solved answers from solved_answers.txt
solved_answers = load_word_list('lists/solved_answers.txt')

# Print the number of words in each list
print(f"Number of words in combined.txt: {len(all_words)}")
print(f"Number of words in answers.txt: {len(answers)}")

def get_word_score_for_answer(word : str, answer : str):
    correct_positions = ["", "", "", "", ""]
    incorrect_positions = ["", "", "", "", ""]
    wrong_letters = ""
    
    # Create a list to track which positions we've already processed
    processed_positions = [False] * len(word)
    answer_letters = list(answer)
    
    # First pass: mark correct positions
    for i in range(len(word)):
        if word[i] == answer[i]:
            correct_positions[i] = word[i]
            processed_positions[i] = True
            # Remove this letter from answer_letters to handle duplicates
            answer_letters.remove(word[i])
    
    # Second pass: handle incorrect positions and wrong letters
    for i in range(len(word)):
        if not processed_positions[i]:
            if word[i] in answer_letters:
                # The letter is in the answer but in wrong position
                incorrect_positions[i] = word[i]
                # Remove this occurrence from answer_letters to handle duplicates
                answer_letters.remove(word[i])
            elif word[i] not in answer:
                wrong_letters += word[i]
    
    return correct_positions, incorrect_positions, wrong_letters

def get_valid_answers(valid_answers : list[str], correct_positions : list[str], 
                        incorrect_positions : list[str], wrong_letters : str) -> list[str]:
    possible_answers = []
    
    # Create a regex pattern for correct positions
    pattern = []
    for i in range(5):
        if correct_positions[i]:  # If we know a letter at this position
            pattern.append(correct_positions[i])
        else:  # If position is unknown
            # Exclude wrong letters and letters that are known to be in wrong positions at this index
            excluded = set(wrong_letters)
            if incorrect_positions[i]:
                excluded.add(incorrect_positions[i])
            if excluded:
                pattern.append(f'[^{"".join(excluded)}]')
            else:
                pattern.append('.')
    
    # Get all letters that must be in the word (from incorrect positions)
    required_letters = {letter for letter in incorrect_positions if letter}
    
    # Filter answers
    for word in valid_answers:
        # Check if word matches the pattern
        if not re.match('^' + ''.join(pattern) + '$', word):
            continue
            
        # Check if all required letters are in the word
        if not all(letter in word for letter in required_letters):
            continue
            
        # Check that incorrect positions don't have those letters
        valid = True
        for i, letter in enumerate(incorrect_positions):
            if letter and word[i] == letter:
                valid = False
                break
                
        if valid:
            possible_answers.append(word)
    
    return possible_answers

def get_average_score(word : str, possible_answers : list[str]) -> float:
    #print(f"Checking word {word}", flush=True)
    score = 0
    for answer in possible_answers:
        score += len(get_valid_answers(possible_answers, *get_word_score_for_answer(word, answer)))
    return (score, word)

def get_best_guess(possible_guesses : list[str], possible_answers : list[str]) -> list[str]:
    
    if len(possible_answers) == 0:
        print("No possible answers")
        exit()

    if len(possible_answers) == 1:
        return possible_answers[0]

    worker_func = partial(get_average_score, possible_answers=possible_answers)

    with multiprocessing.Pool(processes = 8) as pool:
        # map() blocks until all results are ready
        results = pool.map(worker_func, possible_guesses)

    best_answer_score, best_answer = min(results)

    return best_answer
    
def check_against_answer(guess : str, answer : str, wrong_letters : str, possible_guesses : list[str], possible_answers : list[str]):
    correct_positions, incorrect_positions, new_wrong_letters = get_word_score_for_answer(guess, answer)
    new_possible_answers = get_valid_answers(possible_answers, correct_positions, incorrect_positions, wrong_letters)

    wrong_letters = wrong_letters + new_wrong_letters

    filter_string = "^"

    for i in range(len(answer)):
        filter_string += "[^" + wrong_letters + "]"

    filter_string += "$"

    new_possible_guesses = [word for word in possible_guesses if re.match(filter_string, word)]

    return new_possible_guesses, new_possible_answers, wrong_letters

def recursive_check(possible_guesses : list[str], possible_answers : list[str]) -> str:

    first_guess = get_best_guess(possible_guesses, possible_answers)
    #first_guess = "roate"
    print(f"Best first guess is: {first_guess}")

    for line in solved_answers:
        print(line)
    
    answers_to_skip = get_solved_words()

    for answer in possible_answers[1:]:
        if answer in answers_to_skip:
            continue
        result = [first_guess]
        wrong_letters = ""
        depth = 1 #0 is the first_guess
        temp_answers = possible_answers
        temp_guesses = possible_guesses

        while result[-1] != answer and depth < 6:
            temp_guesses, temp_answers, wrong_letters = check_against_answer(result[-1], answer, wrong_letters, temp_guesses,temp_answers)
            result = result + [get_best_guess(temp_guesses, temp_answers)]
            depth += 1

        if result[-1] != answer:
            print(f"Could not find solution for {answer}, best guess was {result}")
            continue

        print(f"Found solution for {answer} in {depth} guesses: {result}")

# get solved words from solved_answers.txt
# answers are stored in this format Found solution for abbot in 2 guesses: ['roate', 'aboil', 'abbot']
# TODO

def get_solved_words():
    fourth_words = []
    for line in solved_answers:
        words = line.split()
        if len(words) >= 4:  # Ensure there are at least 4 words in the line
            fourth_words.append(words[3])
    return fourth_words


def run():
    #best_guess = get_best_guess_for_answer(all_words, test_answers, "fight")
    #print(f"Best guess: {best_guess}")
    #get_best_guess_for_answer([best_guess], test_answers, "fight")

    
    recursive_check(all_words, answers)


run()