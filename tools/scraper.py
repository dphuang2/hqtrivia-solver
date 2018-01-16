#!/usr/bin/env python
import json
import pdb

with open('../data/log', 'r') as f:
    logs = f.read()

questions = set()
for log in logs.split('\n'):
    if '"type":"questionSummary"' in log:
        questions.add(log)

def encode_unicode(string):
    return str(string.encode('utf-8'))


with open('../data/questions_clean', 'w') as f_clean:
    with open('../data/questions', 'w') as f:
        for question in questions:
            data = json.loads(question)
            for i in range(len(data['answerCounts'])):
                if data['answerCounts'][i]['correct']:
                    break
            data = ",".join([encode_unicode(data['question'])] + [encode_unicode(answer['answer']) for answer in data['answerCounts']] + [str(i)])
            f_clean.write(data + '\n')
            f.write(question + '\n')
