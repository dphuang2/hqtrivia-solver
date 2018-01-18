import pdb
import sys
import os

parent_dir_name = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(parent_dir_name + "/src")

DATA_DELIMITER = "|"

from answerer import Answerer 
def main():
    with open('../data/questions_data') as f:
        questions = f.read().split('\n')
    
    data = [[val.strip() for val in question.split('|')] for question in questions]

    # Grab set of already processed questions
    with open('questions_processed', 'r') as f:
        questions_processed = set(f.read().split('\n'))

    answerer = Answerer()
    with open('questions_processed', 'a') as f:
        for entry in data:
            # Check if question was already processed
            question = entry[0]
            if question in questions_processed:
                continue

            # Extract information from entry
            answers = entry[1:-1]
            right_answer = int(entry[-1])

            # Get raw counts from approaches
            raw_counts = answerer.answer(question, answers)

            # Check if we got rate limited
            if raw_counts['rate_limited']:
                print 'We got rate limited. Use a different IP or wait a while'
                exit()

            # Convert to three rows in the input data
            lines = ["", "", ""]
            for i in range(len(lines)):
                lines[i] = "1" if i == right_answer else "0"
            for k,v in raw_counts['data'].iteritems():
                try:
                    confidence_values = [val/sum(v) for val in v]
                except ZeroDivisionError:
                    confidence_values = [0, 0, 0]
                for i in range(len(confidence_values)):
                    lines[i] += DATA_DELIMITER + str(confidence_values[i])

            # Add whether or not question was negative in the data
            for i in range(len(lines)):
                lines[i] += DATA_DELIMITER + ("1" if raw_counts['negative_question'] else "0")

            # Save the data
            with open('regression.data', 'a') as f_data:
                for line in lines:
                    f_data.write(line + '\n')

            # Save question as a processed question
            f.write(question + '\n')

if __name__ == "__main__":
    main()
