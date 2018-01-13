#!/usr/bin/env python
import pdb

with open('log', 'r') as f:
    logs = f.read()

questions = set()
for log in logs.split('\n'):
    if '"type":"questionSummary"' in log:
        questions.add(log)

with open('questions', 'w') as f:
    for question in questions:
        f.write(question + '\n')
