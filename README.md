# wordle-solver
wordle-solver is a logic-based algorithm built from scratch to solve Wordle puzzles with high efficiency. It was built as part of a "Project a Week" coding challenge.

## 🧩 The Challenge
Wordle seems simple, but playing optimally requires complex probability management. Humans often make guesses based on intuition or vocabulary recall. To solve the game mathematically, a program needs to manage two distinct datasets:

Valid Guesses: The ~13,000 words the game accepts as input.

Valid Solutions: The ~2,300 words that can actually be the answer.

The goal is to navigate this search space to find the answer in the fewest moves possible, regardless of the starting conditions.

## 🛠️ The Solution
This solver utilizes an information-reduction strategy. It does not simply guess random words; at every stage, it calculates which word will statistically eliminate the most incorrect answers based on the potential feedback (Green, Yellow, Grey).

How it works:

Initialization: The solver starts with the optimal first guess: roate (pre-calculated to save runtime).

Feedback Loop: It submits a guess and processes the result (e.g., matching characters, wrong positions).

Pruning: It filters the list of Valid Solutions to keep only those that match the feedback history.

Selection: It analyzes the remaining possibilities and selects the next guess that will narrow down the list the fastest.

## 📉 Performance
Running against the standard Wordle answer set, the current algorithm achieves:

Average Guesses: 4.08

Success Rate: 99.8% (Solves within 6 guesses)

Speed Optimization: The initial state calculation is cached, making the first move instant.

## 🔮 Future Roadmap
This project is currently in Phase 1 (Greedy Strategy). Planned improvements for Phase 2 include:

Breadth-First Search (BFS): Moving away from greedy local optimization to a BFS approach to find globally optimal paths.

Decision Tree Integration: Implementing a lookahead system. This will include the rest of the decision tree in each guess—specifically, if an answer is on another branch of the tree, it will be ignored from the current guess calculation even if the current branch hasn't strictly excluded it yet.

## 📋 Prerequisites
Python 3.x

A text file containing valid guesses including solutions (included as combined.txt)

A text file containing valid solutions (included as answers.txt)

## 📥 Installation
Clone the repository:

```Bash
git clone https://github.com/YourUsername/wordle-solver.git
cd wordle-solver
```
## 🚀 Usage
Run the solver script from your terminal:

```Bash

python solver.py
```
Note: Depending on how your script is set up, you might want to add instructions here on whether it plays automatically or asks the user to input the colors/feedback.

## ❤️ Support
If you found this tool useful, consider checking out my Patreon.

## 📄 License (GNU AGPL)
[Read the License](LICENSE)