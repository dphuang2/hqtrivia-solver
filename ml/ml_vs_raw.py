import lightgbm as lgb
import numpy as np
import json
import pdb

ml_correct_count = 0.0
raw_correct_count = 0.0
num_questions = 0.0

bst = lgb.Booster(model_file='./model.txt')

questions_processed = json.load(open('questions_processed.json'))
for question, data in questions_processed.iteritems():
    num_questions += 1
    maximum_value = -1
    raw_answer = ""
    for answer, value in data['raw_data']['fraction_answers'].iteritems():
        if value > maximum_value:
            maximum_value = value
            raw_answer = answer

    X_input = np.array(data['raw_data']['lines'])
    Y_pred = bst.predict(X_input)
    ml_answer = np.array(data['raw_data']['answers'])[np.where(Y_pred==Y_pred.max())][0]

    for i in range(len(data['right_answer'])):
        if data['right_answer'][i]:
            correct_answer = data['raw_data']['answers'][i]

    ml_correct_count += 1 if correct_answer == ml_answer else 0
    raw_correct_count += 1 if correct_answer == raw_answer else 0

print 'ML model accuracy: {}%'.format((ml_correct_count / num_questions) * 100)
print 'Equally Weighting each approach accuracy: {}%'.format((raw_correct_count / num_questions) * 100)

