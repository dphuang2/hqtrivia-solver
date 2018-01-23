#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import pdb

delimiter = '|'

ANSWERS = {
        "To help first create Maps, Google acquired what company?": 1,
        "What term describes a person from the state between New York and Rhode Island?": 1,
        "What gargantuan fruit is the subject of a Roald Dahl children's book?": 2,
        "Which of these quantities is the largest?": 2,
        "What TV series derived from a nearly 20-year-old Michael Crichton screenplay?": 2,
        "Which of these celebrities is known for having aviophobia?": 1,
        "Which of these is NOT a geometric shape?": 1,
        "Who wrote a #1 hit song for the Monkees?": 1,
        "Which of these is NOT a machine used for printing?": 0,
        "Pixies, Bon Iver, Iron & Wine and Bauhaus were all once signed to which record label?": 1,
        "Which of these verbs has two meanings that are opposites of each other?": 2,
        "Which of these is NOT a real animal?": 0,
        "What dish is made with ham, poached eggs and Hollandaise sauce?": 1,
        "What tech mogul became a billionaire the youngest?": 1,
        "Who holds the record as the youngest solo artist with a Billboard #1 hit?": 2,
        "Which of these modes of transportation has only one wheel?": 2,
        "What is the correct pronunciation of the performer who sings “Smooth Operator”?": 0,
        "Who was the president of the Screen Actors Guild before its merger with AFTRA?": 2,
        "Lonnie Lynn's only Academy Award win was in what category?": 2,
        "Talking is discouraged on what Amtrak car?": 2,
        "Queen Victoria is credited with starting what fashion trend?": 2,
        "What iconic painting once hung in Napoleon's bedroom?": 1,
        "Which of these things is NOT found inside an atom?": 1,
        "Which of these is NOT the title of a current TV show?": 2,
        "Which of these creatures is most likely to bark?": 2,
        "Which of these companies went public first?": 0,
        "Which of these celebrities has NOT been a ProActiv spokesperson?":  2,
        "Which of these products was featured on “Shark Tank”?": 1,
        "In which of these movies is the title NOT spoken by any character?": 1,
        "What does a rattlesnake typically do when it feels threatened?": 1,
        "Which of these film composers most recently won an Oscar?": 0,
        "Who is the director of “Tyler Perry’s Madea’s Family Reunion”?": 0,
        "Which of these has NEVER been named Pantone’s Color of the Year?": 0
        }

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
        if text in questions_without_answers:
            print question
            question += "|" + str(ANSWERS[text])
            f.write(question + '\n')
        elif len(data) == 5:
            f.write(question + '\n')
