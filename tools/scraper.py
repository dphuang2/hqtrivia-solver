#!/usr/bin/env python
import json
import pdb

delimiter = '|'

with open('../data/log', 'r') as f:
    logs = f.read()

questions = set()
for log in logs.split('\n'):
    if '"type":"questionSummary"' in log or '"type":"question"' in log:
        questions.add(log)

def encode_unicode(string):
    return str(string.encode('utf-8'))

questions_without_answers = set()
questions_with_answers = set()
with open('../data/questions_clean', 'w') as f_clean:
    with open('../data/questions', 'w') as f:
        for question in questions:
            data = json.loads(question)
            if data["type"] == "question":
                line = delimiter.join([encode_unicode(data['question'])] + [encode_unicode(answer['text']) for answer in data['answers']])
                questions_without_answers.add(encode_unicode(data['question']))
                f_clean.write(line + '\n')
            elif data["type"] == "questionSummary":
                for i in range(len(data['answerCounts'])):
                    if data['answerCounts'][i]['correct']:
                        break
                line = delimiter.join([encode_unicode(data['question'])] + [encode_unicode(answer['answer']) for answer in data['answerCounts']] + [str(i)])
                questions_with_answers.add(encode_unicode(data['question']))
                f_clean.write(line + '\n')
            f.write(question + '\n')

questions_without_answers = questions_without_answers - questions_with_answers
print 'Removing duplicate questions'
with open('../data/questions_clean', 'r') as f:
    all_questions = f.read()
with open('../data/questions_clean', 'w') as f:
    for question in all_questions.split('\n'):
        data = question.split(delimiter)
        text = data[0]
        if text in questions_without_answers or len(data) == 5:
            f.write(question + '\n')
