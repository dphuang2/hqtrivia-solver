# -*- coding: utf-8 -*-

import json
import pdb
import sys
import os

parent_dir_name = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(parent_dir_name + "/src")

DATA_DELIMITER = "|"

from answerer import Answerer 
def main():
    with open('../data/questions_clean') as f:
        questions = f.read().split('\n')
    
    data = [[val.strip() for val in question.split('|')] for question in questions]

    # Grab set of already processed questions
    try:
        questions_processed = json.load(open('questions_processed.json'))
    except ValueError:
        questions_processed = {}

    answerer = Answerer()
    for entry in data:
        # Make sure we don't process an empty line
        if not bool(entry[0]):
            continue

        # Check if question was already processed
        question = entry[0]
        if question.decode('utf-8') in questions_processed:
            continue

        # Extract information from entry
        answers = entry[1:-1]
        right_answer = int(entry[-1])

        # Get raw counts from approaches
        raw_data = answerer.answer(question, answers)

        # Check if we got rate limited
        if raw_data['rate_limited']:
            print 'We got rate limited. Use a different IP or wait a while'
            exit()

        # Convert to three rows in the input data
        one_hot_right_answer = []
        for i in range(len(answers)):
            one_hot_right_answer.append(1 if i == right_answer else 0)

        decoded_question = question.decode('utf-8')
        questions_processed[decoded_question] = {}
        questions_processed[decoded_question]['right_answer'] = one_hot_right_answer
        questions_processed[decoded_question]['raw_data'] = raw_data
        # Save question as a processed question
        with open('questions_processed.json', 'w') as f:
            json.dump(questions_processed, f, indent=4, separators=(',', ': '))

if __name__ == "__main__":
    main()
