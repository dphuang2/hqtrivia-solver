#!/usr/bin/env python
# -*- coding: utf-8 -*-
from method_timer import timeit
from pprint import pprint
import lightgbm as lgb
from time import time
import pandas as pd
import numpy as np
import threading
import wikipedia
import requests
import spacy
import pdb
import sys
import re
import os

parent_dir_name = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

def filename_safe(string):
    return "".join([c for c in string if c.isalpha() or c.isdigit() or c==' ']).rstrip()

def encode_unicode(string):
    return str(string.encode('utf-8', 'ignore'))

class Answerer():
    def __init__(self):
        self.approaches = [
                self.word_count_entities,
                self.word_count_appended,
                self.word_count_raw,
                self.result_count,
                self.wikipedia_search,
                self.word_relation_to_question
                ]
        self.POS_list = ['NOUN', 'NUM', 'PROPN', 'VERB', 'ADJ', 'ADV']
        self.stop_words = ['which', 'Which']
        self.regex = re.compile('"resultstats">(.*) results')
        self.nlp = spacy.load('en')
        self.bst = lgb.Booster(model_file='{}/ml/model.txt'.format(parent_dir_name))
        for word in self.stop_words:
            lexeme = self.nlp.vocab[unicode(word)]
            lexeme.is_stop = True

    @timeit
    def answer(self, question, answers):
        # Initialize values
        self.answers = [str(answer).lower() for answer in answers]
        self.confidences = [0] * len(answers)
        self.integer_answers = [0] * len(answers)
        self.data = {}
        self.rate_limited = False
        try:
            self.question = question.decode('utf-8')
        except UnicodeEncodeError:
            self.question = question
        print 'question: ' + self.question
        print 'answers: ' + str(self.answers) 
        # Initialize nlp constants
        self.process_question()

        # Run all approaches on separate threads
        threads = []
        for function in self.approaches:  # Run each approach in a thread
            t = threading.Thread(target=function)
            threads.append(t)
            t.start()
        for t in threads: # Wait for all threads to finish before counting sum
            t.join()

        # Consolidate confidence values
        try:
            print 'Confidence values: ' + str(self.confidences)
            self.confidences = [val / sum(self.confidences) for val in self.confidences]
        except ZeroDivisionError:
            print 'Getting zero results from Google. Exiting...'
            exit()

        X_input = self.raw_counts_to_input()
        Y_pred = self.bst.predict(X_input)

        # Provide either the negation answer of regular answer
        best_answer = np.array(self.answers)[np.where(Y_pred==Y_pred.min())] if self.negative else np.array(self.answers)[np.where(Y_pred==Y_pred.max())]
        return {
                'best_answer_by_ml': list(best_answer),
                'integer_answers': {k:v for (k,v) in zip(self.answers, self.integer_answers)},
                'fraction_answers': {k:v for (k,v) in zip(self.answers, self.confidences)},
                'ml_answers': {k:v for k,v in zip(self.answers, Y_pred)},
                'negative_question': self.negative,
                'data': self.data,
                'rate_limited': self.rate_limited
                }

    @timeit
    def word_count_entities(self):
        lowered = self.get_lowered_google_search(self.entities)
        counts = []
        for answer in self.answers:
             counts.append(float(lowered.count(answer)))
        print 'Counts after word_count: ' + str(counts)
        self.data['word_count_entities'] = counts
        self.counts_to_confidence(counts)
        print 'Confidence values after word_count_entities: ' + str(self.confidences)

    @timeit
    def word_count_raw(self):
        lowered = self.get_lowered_google_search(self.question)
        counts = []
        for answer in self.answers:
             counts.append(float(lowered.count(answer)))
        print 'Counts after word_count: ' + str(counts)
        self.data['word_count_raw'] = counts
        self.counts_to_confidence(counts)
        print 'Confidence values after word_count_raw: ' + str(self.confidences)

    @timeit
    def word_count_appended(self):
        counts = []
        contents = {}

        # Grab each appended search
        for answer in self.answers:
            t = threading.Thread(target=self.grab_content, args=(contents, self.concatenate_answer(answer)))
            t.start()

        # Block until contents is correctly populated cause thats the important part :)
        while len(contents) != len(self.answers):
            continue

        for answer in self.answers:
            counts.append(float(contents[self.concatenate_answer(answer)].count(answer)))

        print 'Counts after word_count_appended: ' + str(counts)
        self.data['word_count_appended'] = counts
        self.counts_to_confidence(counts)
        print 'Confidence values after word_count_appended: ' + str(self.confidences)

    @timeit
    def word_relation_to_question(self):
        # Grab google search for each answer and save contents
        contents = {}
        for answer in self.answers:
            t = threading.Thread(target=self.grab_content, args=(contents, answer,))
            t.start()

        # Block until contents is correctly populated cause thats the important part :)
        while len(contents) != len(self.answers):
            continue

        # Count occurences for each entity in each answer search
        counts = [0.0] * len(self.answers)
        for word in self.important_words:
            curr_counts = []
            for answer in self.answers:
                curr_counts.append(float(contents[answer].count(word)))
            try:
                curr_counts = [count / sum(curr_counts) for count in curr_counts]
            except ZeroDivisionError:
                print 'The word. "{}" was not found in any search'.format(word)
                pass
            counts = [x + y for x, y in zip(counts, curr_counts)]

        print 'Counts after word_relation_to_question: ' + str(counts)
        self.data['word_relation_to_question'] = counts
        self.counts_to_confidence(counts)
        print 'Confidence values after word_relation_to_question: ' + str(self.confidences)

    @timeit
    def result_count(self):
        counts = []
        contents = {}

        for answer in self.answers:
            t = threading.Thread(target=self.grab_content, args=(contents, self.concatenate_answer(answer),))
            t.start()

        # Block until contents is correctly populated cause thats the important part :)
        while len(contents) != len(self.answers):
            continue

        for answer in self.answers:
            content = contents[self.concatenate_answer(answer)]
            result = self.regex.search(content)
            try:
                count = float([int(s) for s in result.group(1).replace(',', '').split() if s.isdigit()][0])
                counts.append(count)
            except AttributeError:
                print 'There were no results for {}.'.format(answer)
                counts.append(0)

        print 'Counts after result_count: ' + str(counts)
        self.data['result_count'] = counts
        self.counts_to_confidence(counts)
        print 'Confidence values after result_count: ' + str(self.confidences)

    @timeit
    def wikipedia_search(self):
        # Grab wikipedia search for each answer and save contents
        contents = {}
        for answer in self.answers:
            t = threading.Thread(target=self.grab_wikipedia_content, args=(contents, answer,))
            t.start()

        # Block until contents is correctly populated cause thats the important part :)
        while len(contents) != len(self.answers):
            continue
        
        # Count occurences for each entity in each answer search
        counts = [0.0] * len(self.answers)
        for word in self.important_words:
            curr_counts = []
            for answer in self.answers:
                curr_counts.append(float(contents[answer].count(word.decode('utf-8').encode('ascii', 'ignore'))))
            try:
                curr_counts = [count / sum(curr_counts) for count in curr_counts]
            except ZeroDivisionError:
                print 'The word. "{}" was not found in any search'.format(word)
                pass
            counts = [x + y for x, y in zip(counts, curr_counts)]

        print 'Counts after wikipedia_search: ' + str(counts)
        self.data['wikipedia_search'] = counts
        self.counts_to_confidence(counts)
        print 'Confidence values after wikipedia_search: ' + str(self.confidences)

    @timeit
    def grab_wikipedia_content(self, contents, page):
        search_results = wikipedia.search(page)
        # In the case that no page exists, return False
        if not len(search_results):
            contents[page] = False
            return
        try:
            contents[page] = wikipedia.WikipediaPage(title=search_results[0]).html()
        except wikipedia.exceptions.DisambiguationError as e:
            try:
                contents[page] = wikipedia.WikipediaPage(title=e.options[0]).html()
            except wikipedia.exceptions.PageError:
                contents[page] = wikipedia.WikipediaPage(title=e.options[1]).html()

    @timeit
    def grab_content(self, contents, question):
        contents[question] = self.get_lowered_google_search(question)

    @timeit
    def counts_to_confidence(self, counts):
        print 'counts_to_confidence counts: {}'.format(counts)
        if max(counts):
            print 'winning answer: ' + self.answers[counts.index(max(counts))]
            self.integer_answers[counts.index(max(counts))] += 1
        for i in range(len(counts)):
            sum_of_counts = float(sum(counts))
            try:
                self.confidences[i] += counts[i] / sum_of_counts
            except ZeroDivisionError:
                break

    @timeit
    def word_count(self, content, words):
        counts = []
        for i in range(len(words)):
             counts.append(float(content.count(words[i])))
        print 'Counts after word_count: ' + str(counts)
        self.counts_to_confidence(counts)

    @timeit
    def process_question(self):
        # Initialize nlp constants
        doc = self.nlp(unicode(self.question))
        # Word is part of the POS list and it is not a stop word (common word)
        self.important_words = [encode_unicode(t.text).lower() for t in doc if t.pos_ in self.POS_list and not t.is_stop]
        self.entities = ' '.join([chunk.text for chunk in list(doc.noun_chunks)])
        # For giving "best" answer - HQTrivia gives negative questions in form of all caps word
        self.negative = False
        if any(t.is_upper and t.pos_ == 'ADV' and not t.is_title for t in doc):
            self.negative = True
        print 'Evaluated important words: ' + str(self.important_words)
        print 'Evaluated entities: ' + self.entities

    def concatenate_answer(self, answer):
        return u'{} "{}"'.format(self.question, answer).encode('utf-8').strip()

    @timeit
    def get_lowered_google_search(self, question):
        google_query = 'https://www.google.com/search?num=100&q=' 
        if question in self.get_lowered_google_search.memo:
            return self.get_lowered_google_search.memo[question]
        r = requests.get(google_query + question)
        lowered = r.content.lower()
        with open(parent_dir_name + '/data/google_searches/{}'.format(filename_safe(question)), 'w') as f:
            f.write(lowered)
        if 'our systems have detected unusual traffic from your computer network' in lowered:
            print 'Google rate limited your IP.'
            self.rate_limited = True
        self.get_lowered_google_search.memo[question] = lowered
        return lowered
    get_lowered_google_search.memo = {}

    def raw_counts_to_input(self):
        # Convert data to input data
        lines = [[], [], []]
        for k,v in self.data.iteritems():
            try:
                confidence_values = [val/sum(v) for val in v]
            except ZeroDivisionError:
                confidence_values = [0, 0, 0]
            for i in range(len(confidence_values)):
                lines[i].append(confidence_values[i])

        # Add whether or not question was negative in the data
        for i in range(len(lines)):
            lines[i].append(1 if self.negative else 0)

        return np.array(lines)


def main():
    solver = Answerer()
    pprint(solver.answer(u"The Windows 95 startup sound was composed by a former member of what band?",["They Might Be Giants","Roxy Music","Devo"]))
    # pprint(solver.answer(u"Guatemala and Mozambique are the only UN countries with what on their flags?",["Firearm","Garden tool","Bird"]))
    # pprint(solver.answer(u"Which of these countries is NOT a collaborating member on the International Space Station?",["China","Russia","Canada"]))
    # pprint(solver.answer(u"Which of these fitness fads came first?",["Tae Bo","Jazzercise","Zumba"]))
    # pprint(solver.answer(u"Which movie director's daughter made her directorial debut in 2017",["Nancy Meyers","David Lynch","Ridley Scott"]))
    # pprint(solver.answer(u'The word "robot" comes from a Czech word meaning what?',["forced labor","mindless","autonomous"]))
    # pprint(solver.answer(u'In which ocean would you find Micronesia?', ["atlantic","pacific","indian"]))
    # pprint(solver.answer("Which of these is NOT a real animal?", ["liger", "wholphin", "jackalope"]))
    # pprint(solver.answer(u'Microsoft Passport was previously known as what?',["ms id","ms single sign-on","net passport"]))
    # pprint(solver.answer(u'Jennifer Hudson kicked off her musical career on which reality show?', ["american idol","america's got talent","the voice"]))
    # pprint(solver.answer(u'Which of these Uranus moons is NOT named after a Shakespearean character?', ['Oberon', 'Umbriel', 'Trinculo']))
    # pprint(solver.answer('Which of these two U.S. cities are in the same time zone?', ['El Paso / Pierre', 'Bismark / Cheyenne', 'Pensacola / Sioux Falls']))
    # pprint(solver.answer(u'Who was the first U.S President to be born in a hospital?',["immy carter","richard nixon","franklin d. roosevelt"]))
    # pprint(solver.answer(u'The Ewing family in the TV show "Dallas" made their money in which commodity?',["oil","coal","steel"]))
    # pprint(solver.answer(u'Which brand mascot was NOT a real person?', ["Little Debbie", "Sara Lee", "Betty Crocker"]))
    # pprint(solver.answer(u'Which video game motion-captured "Mad Men" actor Aaron Staton as its star?',["medal of honor","l.a. noire","assassin's creed 2"]))
    # pprint(solver.answer(u'Which of these is NOT a constellation?',["fornax","draco","lucrus"]))
    # pprint(solver.answer(u'Which of these is NOT one of the Great Lakes', ["Lake Superior", "Ricki Lake", "Lake Michigan"]))
    # pprint(solver.answer(u'The lyrics to "The Start-Spangled Banner" were written during what conflict?', ['The Civil War', 'American Revolution', 'The War of 1812']))
    # pprint(solver.answer(u"""In which version of “Dragnet” is the line “Just the facts, ma’am” first said?""", ["50s TV show","'50s movie","'80s movie"]))
    # pprint(solver.answer(u'Which writer has stated that his/her trademark series of books would never be adapted for film?', ["James Patterson", "Sue Grafton", "Jeff Kinney"]))
    # pprint(solver.answer(u'Which of these countries has the longest operating freight trains in the world?',["japan","brazil","canada"]))
    # pprint(solver.answer(u'Whose cat is petrified by the basilisk in "Harry Potter and the Chamber of Secrets"?',["poppy pomfrey","gilderoy lockhart","argus filch"]))
    # pprint(solver.answer(u'"The Blue Danube" isa waltz by which composer?',["richard strauss","johann strauss i","franz strauss"]))

if __name__ == "__main__":
    main()
