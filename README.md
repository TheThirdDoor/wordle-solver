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

Finds the word that will split each possible answer into the most buckets possible.
Repeat for each bucket till every bucket has only one answer.

## 📉 Performance
Running against the standard Wordle answer set, the current algorithm achieves:

Average Guesses: 3.43

Success Rate: 100% (Solves within 6 guesses)

Speed Optimization: Takes 1 minute.

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

## ❤️ Support
If you found this tool useful, consider checking out my Patreon.

## 📄 License (GNU AGPL)
[Read the License](LICENSE)