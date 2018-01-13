#!/usr/bin/env python
from method_timer import timeit
from time import time
import wikipedia
import threading
import requests
import spacy
import pdb
import sys
import re

@timeit
def get_lowered_google_search(question):
    google_query = 'https://www.google.com/search?num=100&q=' 
    if question in get_lowered_google_search.memo:
        return get_lowered_google_search.memo[question]
    r = requests.get(google_query + question)
    lowered = r.content.lower()
    if 'our systems have detected unusual traffic from your computer network' in lowered:
        print 'Google rate limited your IP. Exiting...'
        exit()
    get_lowered_google_search.memo[question] = lowered
    return lowered
get_lowered_google_search.memo = {}

class Answerer():
    def __init__(self):
        self.approaches = [self.word_count_raw, self.word_count_appended, self.word_relation_to_question, self.wikipedia_search]
        self.POS_list = ['NOUN', 'NUM', 'PROPN', 'VERB', 'ADJ']
        self.regex = re.compile('about (.*) result')
        self.negation = ['not', 'never', 'none']
        self.nlp = spacy.load('en')

    @timeit
    def answer(self, question, answers):
        # Initialize values
        self.answers = [str(answer).lower() for answer in answers]
        self.confidence = [0] * len(answers)
        self.integer_answers = [0] * len(answers)
        self.original_question = question
        self.negative = False

        # Remove 'not' from searched question
        for negative in self.negation:
            if negative in question.lower():
                self.negative = True
                print 'Detected a negative question'
                not_idx = self.original_question.lower().find(negative)
                self.question = self.original_question[:not_idx] + self.original_question[not_idx+len(negative)+1:]
                break
        else:
            self.question = self.original_question
        print 'Evaluated question: ' + self.question

        # Initialize nlp constants
        self.nlp_question()

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
            print 'Confidence values: ' + str(self.confidence)
            self.confidence = [val / sum(self.confidence) for val in self.confidence]
        except ZeroDivisionError:
            print 'Getting zero results from Google. Exiting...'
            exit()

        # Provide either the negation answer of regular answer
        if self.negative:
            best_confidence = min(self.confidence)
            best_integer = min(self.integer_answers)
        else:
            best_confidence = max(self.confidence)
            best_integer = max(self.integer_answers)
        best_confidence_idx = self.confidence.index(best_confidence)
        best_integer_answers = self.integer_answers.index(best_integer)
        return (self.answers[best_confidence_idx], best_confidence, self.answers[best_integer_answers], best_integer, len(self.approaches))

    @timeit
    def word_count_entities(self):
        lowered = get_lowered_google_search(self.entities)
        self.word_count(lowered, self.answers)
        print 'Confidence values after word_count_entities: ' + str(self.confidence)

    @timeit
    def word_count_raw(self):
        lowered = get_lowered_google_search(self.question)
        self.word_count(lowered, self.answers) 
        print 'Confidence values after word_count_raw: ' + str(self.confidence)

    @timeit
    def word_count_appended(self):
        counts = []
        contents = {}

        for answer in self.answers:
            t = threading.Thread(target=self.grab_content, args=(contents, self.question + ' ' + answer,))
            t.start()

        # Block until contents is correctly populated cause thats the important part :)
        while len(contents) != len(self.answers):
            continue

        for answer in self.answers:
            curr_count = 0
            content = contents[self.question + ' ' + answer]
            curr_count += float(content.count(answer))
            counts.append(curr_count)

        print 'Counts after word_count_appended: ' + str(counts)
        self.counts_to_confidence(counts)
        print 'Confidence values after word_count_appended: ' + str(self.confidence)

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
        counts = []
        for answer in self.answers:
            curr_count = 0
            for word in self.important_words:
                curr_count += contents[answer].count(word)
            counts.append(curr_count)
        print 'Counts after word_relation_to_question: ' + str(counts)
        self.counts_to_confidence(counts)
        print 'Confidence values after word_relation_to_question: ' + str(self.confidence)

    @timeit
    def result_count(self):
        counts = []
        contents = {}

        for answer in self.answers:
            t = threading.Thread(target=self.grab_content, args=(contents, self.question + ' ' + answer,))
            t.start()

        for answer in self.answers:
            # Block until contents is correctly populated cause thats the important part :)
            while len(contents) != len(self.answers):
                continue
            content = contents[self.question + ' ' + answer]
            result = self.regex.search(content)
            try:
                counts.append(float(result.group(1).replace(',', '')))
            except AttributeError:
                print 'What?! that regex should have worked...'

        print 'Counts after result_count: ' + str(counts)
        self.counts_to_confidence(counts)
        print 'Confidence values after result_count: ' + str(self.confidence)

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
        counts = []
        for answer in self.answers:
            curr_count = 0
            for word in self.important_words:
                curr_count += contents[answer].count(word)
            counts.append(curr_count)
        print 'Counts after wikipedia_search: ' + str(counts)
        self.counts_to_confidence(counts)
        print 'Confidence values after wikipedia_search: ' + str(self.confidence)

    @timeit
    def grab_wikipedia_content(self, contents, page):
        search_results = wikipedia.search(page)
        try:
            contents[page] = wikipedia.WikipediaPage(title=search_results[0]).html()
        except wikipedia.exceptions.DisambiguationError as e:
            contents[page] = wikipedia.WikipediaPage(title=e.options[0]).html()

    @timeit
    def grab_content(self, contents, question):
        contents[question] = get_lowered_google_search(question)

    @timeit
    def counts_to_confidence(self, counts):
        self.integer_answers[counts.index(max(counts))] += 1
        for i in range(len(counts)):
            sum_of_counts = float(sum(counts))
            try:
                self.confidence[i] += counts[i] / sum_of_counts
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
    def nlp_question(self):
        # Initialize nlp constants
        doc = self.nlp(self.question)
        # Word is part of the POS list and it is not a stop word (common word)
        self.important_words = [str(t.text).lower() for t in doc if t.pos_ in self.POS_list and not t.is_stop]
        self.entities = ' '.join([str(chunk) for chunk in list(doc.ents) + list(doc.noun_chunks)])
        print 'Evaluated important words: ' + str(self.important_words)
        print 'Evaluated entities: ' + self.entities

if __name__ == "__main__":
    solver = Answerer()
    print solver.answer(u'Which of these is NOT a constellation?',["fornax","draco","lucrus"])
    print solver.answer(u'Which of these countries has the longest operating freight trains in the world?',["japan","brazil","canada"])
    print solver.answer(u'Jennifer Hudson kicked off her musical career on which reality show?', ["american idol","america's got talent","the voice"])
    print solver.answer(u'Who was the first U.S President to be born in a hospital?',["immy carter","richard nixon","franklin d. roosevelt"])
    print solver.answer(u'In which ocean would you find Micronesia?', ["atlantic","pacific","indian"])
    print solver.answer(u'Whose cat is petrified by the basilisk in "Harry Potter and the Chamber of Secrets"?',["poppy pomfrey","gilderoy lockhart","argus filch"])
    print solver.answer(u'The Ewing family in the TV show "Dallas" made their money in which commodity?',["oil","coal","steel"])
    print solver.answer(u'Microsoft Passport was previously known as what?',["ms id","ms single sign-on","net passport"])
    print solver.answer(u'"The Blue Danube" isa waltz by which composer?',["richard strauss","johann strauss i","franz strauss"])
    print solver.answer(u'Which video game motion-captured "Mad Men" actor Aaron Staton as its star?',["medal of honor","l.a. noire","assassin's creed 2"])
    print solver.answer(u'The word "robot" comes from a Czech word meaning what?',["forced labor","mindless","autonomous"])
