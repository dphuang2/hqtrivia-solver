#!/usr/bin/env python
import multiprocessing
import pdb
import requests
import spacy
from time import time
import sys

def return_lowered_content(question):
    google_query = 'https://www.google.com/search?num=100&q=' 
    if question in return_lowered_content.memo:
        return return_lowered_content.memo[question]
    r = requests.get(google_query + question)
    lowered = r.content.lower()
    return_lowered_content.memo[question] = lowered
    return lowered
return_lowered_content.memo = {}

class Answerer():
    def __init__(self):
        self.nlp = spacy.load('en')
        self.approaches = [self.word_count_nlp, self.word_count_raw, self.word_count_appended]
        self.manager = multiprocessing.Manager()

    def answer(self, question, answers):
        self.original_question = question
        # Remove 'not' from searched question
        if 'not' in question.lower():
            not_idx = self.original_question.lower().find('not')
            self.question = self.original_question[:not_idx] + self.original_question[not_idx+4:]
        else:
            self.question = self.original_question
        self.answers = [str(answer).lower() for answer in answers]
        self.confidence = [0.0] * len(answers)

        [f() for f in self.approaches]
        self.confidence = [val / sum(self.confidence) for val in self.confidence]

        if 'not' in question.lower():
            best_confidence = min(self.confidence)
        else:
            best_confidence = max(self.confidence)
        best_confidence_idx = self.confidence.index(best_confidence)
        return (self.answers[best_confidence_idx], best_confidence)

    def word_count_nlp(self):
        doc = self.nlp(self.question)
        question = ' '.join([str(chunk) for chunk in list(doc.noun_chunks)])
        lowered = return_lowered_content(question)
        self.word_count(lowered, self.answers)

    def word_count_raw(self):
        lowered = return_lowered_content(self.question)
        self.word_count(lowered, self.answers) 

    def grab_content(self, contents, question):
        contents[question] = return_lowered_content(question)

    def word_count_appended(self):
        counts = []
        contents = self.manager.dict()

        for i in range(len(self.answers)):
            p = multiprocessing.Process(target=self.grab_content, args=(contents, self.question + ' ' + self.answers[i],))
            p.start()

        for i in range(len(self.answers)):
            # Block until contents is correctly populated
            while len(contents) != len(self.answers):
                continue
            word = self.answers[i]
            content = contents[self.question + ' ' + word]
            counts.append(float(content.count(word)))

        for i in range(len(self.answers)):
            sum_of_counts = float(sum(counts))
            try:
                self.confidence[i] += counts[i] / sum_of_counts
            except ZeroDivisionError:
                break

    def word_count(self, content, words):
        counts = []
        for i in range(len(words)):
             counts.append(float(content.count(words[i])))
        for i in range(len(words)):
            sum_of_counts = float(sum(counts))
            try:
                self.confidence[i] += counts[i] / sum_of_counts
            except ZeroDivisionError:
                break


if __name__ == "__main__":
    solver = Answerer()

    t1 = time()
    print solver.answer(u'Which of these is NOT a constellation?',["fornax","draco","lucrus"])
    t2 = time()
    print t2 - t1

    # t1 = time()
    # print solver.answer(u'Which of these countries has the longest operating freight trains in the world?',["japan","brazil","canada"])
    # t2 = time()
    # print t2 - t1

    t1 = time()
    print solver.answer(u'Jennifer Hudson kicked off her musical career on which reality show?', ["american idol","america's got talent","the voice"])
    t2 = time()
    print t2 - t1

    t1 = time()
    print solver.answer(u'Who was the first U.S President to be born in a hospital?',["immy carter","richard nixon","franklin d. roosevelt"])
    t2 = time()
    print t2 - t1

    # solver.answer(u'In which ocean would you find Micronesia?', ["atlantic","pacific","indian"])
    # solver.answer(u'Whose cat is petrified by the basilisk in "Harry Potter and the Chamber of Secrets"?',["poppy pomfrey","gilderoy lockhart","argus filch"])
    # solver.answer(u'The Ewing family in the TV show "Dallas" made their money in which commodity?',["oil","coal","steel"])
    # solver.answer(u'Microsoft Passport was previously known as what?',["ms id","ms single sign-on","net passport"])
    # solver.answer(u'"The Blue Danube" isa waltz by which composer?',["richard strauss","johann strauss i","franz strauss"])
    # solver.answer(u'Which video game motion-captured "Mad Men" actor Aaron Staton as its star?',["medal of honor","l.a. noire","assassin's creed 2"])
    # solver.answer(u'The word "robot" comes from a Czech word meaning what?',["forced labor","mindless","autonomous"])
