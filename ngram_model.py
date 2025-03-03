# -*- coding: utf-8 -*-
"""NGRAM MODEL.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/18-c_oyjwlzgA_-kEpvavDfkOnDmzNSGD
"""

from pygments.lexers.jvm import JavaLexer
from pygments.token import Token
from collections import defaultdict, Counter
import math
import json
import random
import re

import sys


def tokenize_java_code(code):
    """Tokenizes Java code using Pygments."""
    lexer = JavaLexer()
    return [t[1] for t in lexer.get_tokens(code) if t[0] not in Token.Text]


def build_ngram_model(corpus, n):
    """Builds an N-gram model from tokenized Java methods."""
    ngram_counts = defaultdict(int)
    context_counts = defaultdict(int)

    for method in corpus:
        tokens = tokenize_java_code(method)
        for i in range(len(tokens) - n + 1):
            ngram = tuple(tokens[i:i + n])
            context = tuple(tokens[i:i + n - 1])
            ngram_counts[ngram] += 1
            context_counts[context] += 1

    print(f"Number of N-grams: {len(ngram_counts)}")
    return ngram_counts, context_counts


def compute_probabilities(ngram_counts, context_counts):
    """Computes conditional probabilities for N-grams."""
    probabilities = {}
    for ngram, count in ngram_counts.items():
        context = ngram[:-1]
        probabilities[ngram] = count / context_counts[context]
    return probabilities


def perplexity(test_corpus, probabilities, n):
    """Computes perplexity for the N-gram model on a test set."""
    log_prob_sum = 0
    N = 0

    for method in test_corpus:
        tokens = tokenize_java_code(method)
        for i in range(len(tokens) - n + 1):
            ngram = tuple(tokens[i:i + n])
            prob = probabilities.get(ngram, 1e-6)  # Smoothing for unseen cases
            log_prob_sum += math.log2(prob)
            N += 1

    return 2 ** (-log_prob_sum / N)


def iterative_prediction_x(probabilities, context, n):
    """Predicts the next token iteratively given a starting context."""
    predictions = []

    for _ in range(10):  # Limit predictions to avoid infinite loops
        candidates = {ngram[-1]: prob for ngram, prob in probabilities.items() if ngram[:-1] == context}

        if not candidates:
            break  # Stop if no valid prediction

        next_token = max(candidates, key=candidates.get)  # Most probable token
        predictions.append((next_token, round(candidates[next_token], 3)))
        context = context[1:] + (next_token,)  # Update context

    return predictions


def generate_results_json(test_corpus, probabilities, n, filename):
    """Generates a JSON file with token predictions and probabilities."""
    results = {}

    for i, method in enumerate(test_corpus[:100]):  # Limit to 100 examples
        tokens = tokenize_java_code(method)[:n - 1]
        context = tuple(tokens)
        results[str(i)] = iterative_prediction_x(probabilities, context, n)

    with open(filename, "w") as f:
        json.dump(results, f, indent=4)

    print(f"Saved predictions to {filename}")
    # Brief example
    if results:
        first_method_predictions = results["0"]
        if first_method_predictions:
            print(f"First prediction for method 0: {first_method_predictions[0]}")


def generate_vocabulary(corpus):
    """Generates a vocabulary from the given corpus (training + eval + test)."""
    vocab = set()
    for method in corpus:
        tokens = tokenize_java_code(method)
        vocab.update(tokens)
    return vocab


def load_methods_from_file(filename):
    """
    Reads a file containing methods enclosed in quotes and extracts each method as a single string.
    Uses a regular expression with DOTALL to capture methods spanning multiple lines.
    """
    with open(filename, "r") as f:
        content = f.read()
    # Extract text between double quotes (non-greedy) over multiple lines.
    methods = re.findall(r'"(.*?)"', content, re.DOTALL)
    # Strip whitespace from each method and filter out any empty strings.
    methods = [method.strip() for method in methods if method.strip()]
    return methods


def main():
    # Load dataset from cleaned corpus (e.g., 7561 methods)
    with open(sys.argv[1], "r") as f:
        corpus = [line.strip() for line in f]

    print(f"Total methods in corpus: {len(corpus)}")  # Expected: 7561 methods

    # Vocabulary Generation (using training + eval + test sets)
    vocab = generate_vocabulary(corpus)
    # print(vocab)
    print(f"Vocabulary size: {len(vocab)}")  # ZZZ number of code tokens

    # Shuffle and split dataset: 80% training, 10% eval, 10% test
    random.shuffle(corpus)
    train_set = corpus[:int(0.8 * len(corpus))]
    eval_set = corpus[int(0.8 * len(corpus)):int(0.9 * len(corpus))]
    test_set = corpus[int(0.9 * len(corpus)):]

    print(f"Train set: {len(train_set)} methods")
    print(f"Eval set: {len(eval_set)} methods")
    print(f"Test set: {len(test_set)} methods")

    # Model Training & Evaluation on Student's Data
    # Experiment with n = 3, n = 5, and n = 9; select best based on perplexity
    best_n = None
    best_perplexity = float("inf")
    results = {}

    for n in [3, 5, 9]:
        print(f"Evaluating {n}-gram model on training data")
        ngram_counts, context_counts = build_ngram_model(train_set, n)
        probabilities = compute_probabilities(ngram_counts, context_counts)

        pp = perplexity(eval_set, probabilities, n)
        results[n] = pp
        print(f"{n}-gram model Perplexity on Eval set: {pp}")

        if pp < best_perplexity:
            best_perplexity = pp
            best_n = n

    print(f"Selected best N: {best_n} (Perplexity: {best_perplexity})")
    # According to our report, n = 3 was selected (with perplexity ~91.297)

    # Train best model on full training set
    best_ngram_counts, best_context_counts = build_ngram_model(train_set, best_n)
    best_probabilities = compute_probabilities(best_ngram_counts, best_context_counts)

    # Compute perplexity on the full test set for student model
    test_pp = perplexity(test_set, best_probabilities, best_n)
    print(f"Test set Perplexity for {best_n}-gram model: {test_pp}")  # Replace YYY.00000 with actual value

    # Generate JSON output for student model (first 100 predictions)
    generate_results_json(test_set, best_probabilities, best_n, "sample.json")

if __name__ == "__main__":
	if len(sys.argv) != 2:
		print("Usage: python ngram_model.py <your_corpus.txt>")
	else:
	    main()
