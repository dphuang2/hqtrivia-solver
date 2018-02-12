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
        "Which of these has NEVER been named Pantone’s Color of the Year?": 0,
        "Anne of Green Gables literally means Anne of what?": 2,
        "Which of these do adverbs NOT typically modify?": 0,
        "Catherine O'Hara and Eugene Levy do NOT kiss in which Christopher Guest film?": 1,
        "Which organization began as the North West Police Agency?": 2,
        "Marsha Bell was the model for what iconic character?": 2,
        "Which of these is NOT a skin care brand?": 1,
        "Most humans have how many kidneys?": 0,
        "What’s another name for a garbanzo bean?": 1,
        "Which of these is a U.S. postage stamp?": 1,
        "Which of these does a plant typically need to grow?": 1,
        "In the original Angry Birds game, what did the pigs do that made the birds so angry?": 1,
        'Which has been the last name of a U.S. president AND a British prime minister?': 2,
        'Knucklebones is another name for what classic game?': 1,
        'Which of these words is NOT a synonym for “nonsense”?': 1,
        'A galleon is an old-fashioned type of what?': 0,
        'What male singing voice type is higher than a bass, but lower than a tenor?': 0,
        'If you capitalize it, what Disney character name doubles as a healthcare program?': 0,
        'George Washington Carver is famous for his scientific work on what subject?': 0,
        'What does bicameral mean?': 2,
        'Which of these things can be mathematically described as an oblate spheroid?': 0,
        'Which of these baseball legends was a first-ballot Hall of Famer?': 2,
        'Which monster is NOT named in the Kanye West song “Monster”?': 0,
        'Which of these is NOT believed to be a function of the uvula?': 0,
        'Which of these websites is an online database for movies, television and video games?': 1,
        'Where do pearls come from?': 0,
        "Bart's age on “The Simpsons” is NOT the same as which of these characters?": 2,
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
