#!/usr/bin/env python
# -*- coding: utf-8 -*-
from spacy.tokenizer import Tokenizer
from HTMLParser import HTMLParser
from method_timer import timeit
from unidecode import unidecode
from bs4 import BeautifulSoup
from pprint import pprint
import lightgbm as lgb
from time import time
import pandas as pd
import numpy as np
import threading
import wikipedia
import requests
import gensim
import spacy
import pdb
import sys
import re
import os

"""
Features / Approaches:
answer_relation_to_question: Google search each answer and count number of occurences for each evaluated important word
answer_relation_to_question_bing: Bing search each answer and count number of occurences for each evaluated important word
cosine_similarity_raw: Google question and each answer, create document corpus from each answer search, compare cosine similarity of question search to corpus
question_relation_to_word: Google search each important word and count number of occurences for each answer
question_relation_to_word_bing: Bing search each important word and count number of occurences for each answer
result_count: Google question with each answer appended and count number of search results
result_count_bing: Google question with each answer appended and count number of search results
result_count_important_words: Google important words with each answer appended and count number of search results
result_count_noun_chunks: Google noun_chunks with each answer appended and count number of search results
wikipedia_search: Wikipedia search each answer and count number of occurences for each evaluated important word
word_count_appended: Google question with each answer appended in quotes and count occurences of each answer
word_count_appended_bing: Bing search question with each answer appended in quotes and count occurences of each answer
word_count_appended_relation_to_question: Google question with each answer appended in quotes and count occurences of each important word
word_count_noun_chunks: Google evaluated noun chunks of question and count occurences of each answer
word_count_raw: Google the question and count occurences of each answer

Categorical data:
type_of_question: Classify the question from 0 to 5 using the 6 Ws of questions
"""

def filename_safe(string):
    return "".join([c for c in string if c.isalpha() or c.isdigit() or c==' ']).rstrip()

def encode_unicode(string):
    return str(string.encode('utf-8', 'ignore'))

class Answerer():
    def __init__(self):
        self.approaches = [
                self.wikipedia_search,
                self.answer_relation_to_question,
                self.answer_relation_to_question_bing,
                # self.question_related_to_answer,
                # self.question_related_to_answer_bing,
                self.result_count,
                self.result_count_bing,
                self.result_count_important_words,
                self.result_count_noun_chunks,
                self.cosine_similarity_raw,
                self.type_of_question,
                self.word_count_appended,
                self.word_count_appended_bing,
                self.word_count_appended_relation_to_question,
                self.word_count_noun_chunks,
                self.word_count_raw,
                self.question_answer_similarity
                ]
        self.question_types = {
                'who': 0,
                'what': 1,
                'when': 2,
                'where': 3,
                'why': 4,
                'how': 5,
                }

        self.parent_dir_name = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
        self.POS_list = ['NOUN', 'NUM', 'PROPN', 'VERB', 'ADJ', 'ADV']
        self.negative_words = ['never', 'not']
        self.stop_words = ['which', 'Which']
        self.regex = re.compile('"resultstats">(.*) results')
        self.regex_bing = re.compile('count">(.*) results<\/')
        self.nlp_vector = spacy.load('en_vectors_web_lg')
        self.nlp = spacy.load('en')
        self.tokenizer = Tokenizer(self.nlp.vocab)
        self.h = HTMLParser()
        self.bst = lgb.Booster(model_file='{}/ml/model.txt'.format(self.parent_dir_name))
        for word in self.stop_words:
            lexeme = self.nlp.vocab[unicode(word)]
            lexeme.is_stop = True

    @timeit
    def answer(self, question, answers):
        # Initialize values
        self.answers = [str(answer).lower() for answer in answers]
        self.data = {}
        self.categorical_data = {}
        self.rate_limited = False
        try:
            self.question = question.decode('utf-8')
        except UnicodeEncodeError:
            self.question = question
        self.question = self.question.lower()
        print 'question: ' + self.question.encode('utf-8')
        print 'answers: ' + str(self.answers) 

        # Initialize nlp constants
        self.process_question()

        # Remove negative word from question and for giving correct input to model
        self.question_without_negative = self.question
        self.negative_question = False
        for word in self.negative_words:
            if word in [t.text for t in self.doc]:
                self.negative_question = True
                negative_idx = self.question.index(word)
                self.question_without_negative = self.question[:negative_idx] + self.question[negative_idx + len(word) + 1:]
                break

        # Run all approaches on separate threads
        threads = []
        for function in self.approaches:  # Run each approach in a thread
            t = threading.Thread(target=function)
            threads.append(t)
            t.start()

        for t in threads: # Wait for all threads to finish before counting sum
            t.join()

        # Convert normalize raw feature values and convert them to numpy arrays for model input
        X_input = self.raw_counts_to_input()
        print 'X_input: {}'.format(str(X_input))
        Y_pred = self.bst.predict(X_input)
        print 'Y_pred: {}'.format(str(Y_pred))

        # Provide best answer of the predicted values
        np_max = np.where(Y_pred==Y_pred.max())
        answer_position = {
                0: 'top',
                1: 'middle',
                2: 'bottom'
                }
        try:
            answer_position = answer_position[np_max[0][0]]
        except KeyError:
            print 'there was no answer?'
        best_answer = np.append(np.array(self.answers)[np_max], answer_position)
        ret_dict = {
                'z-best_answer_by_ml': list(best_answer), # the 'z-' is so pprint prints the answer last
                'ml_answers': {k:v for k,v in zip(self.answers, Y_pred)},
                'question': self.question,
                'negative_question': self.negative_question,
                'categorical_data': self.categorical_data,
                'answers': self.answers,
                'lines': self.lines,
                'data': self.data,
                'columns_in_order': sorted(list(self.data.keys())) + sorted(list(self.categorical_data.keys())), 
                'rate_limited': self.rate_limited
                }
        pprint(ret_dict)
        return ret_dict
    
    def question_answer_similarity(self):
        counts = []
        for answer in self.answers:
            try:
                answer_doc = self.nlp_vector(unicode(answer))
            except UnicodeDecodeError:
                answer_doc = self.nlp_vector(unicode(answer.decode('utf-8')))
            curr_similarity = 0.0
            for answer_token in answer_doc:
                for question_token in self.doc_vectors:
                    curr_similarity += question_token.similarity(answer_token)
            counts.append(curr_similarity)
        self.data['question_answer_similarity'] = counts

    @timeit
    def type_of_question(self):
        for category, value in self.question_types.iteritems():
            if category in [t.text for t in self.doc]:
                self.categorical_data['question_type'] = value
                break
        else:
            self.categorical_data['question_type'] = -1 # No type found

    @timeit
    def word_count_noun_chunks(self):
        lowered = self.get_lowered_google_search(self.noun_chunks_string)
        counts = []
        for answer in self.answers:
             counts.append(float(lowered.count(answer)))
        self.data['word_count_noun_chunks'] = counts

    @timeit
    def word_count_raw(self):
        lowered = self.get_lowered_google_search(self.question_without_negative)
        counts = []
        for answer in self.answers:
             counts.append(float(lowered.count(answer)))
        self.data['word_count_raw'] = counts

    @timeit
    def cosine_similarity_raw(self):
        counts = []
        contents = {}
        threads = []

        for query_text in self.answers + [self.question_without_negative]:
            t = threading.Thread(target=self.grab_content, args=(contents, query_text,), kwargs={'num_results': 20})
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # Process HTML docs
        for query_text in self.answers + [self.question_without_negative]:
            soup = BeautifulSoup(contents[query_text], 'html.parser')
            text = ' '.join([t.getText() for t in soup.findAll("span", {"class": "st"})])
            contents[query_text] = self.tokenizer(unicode(text))

        # Create corpus from answer searches
        gen_docs = [[t.text for t in doc] for doc in [contents[answer] for answer in self.answers]]
        dictionary = gensim.corpora.Dictionary(gen_docs)
        corpus = [dictionary.doc2bow(gen_doc) for gen_doc in gen_docs]
        tf_idf = gensim.models.TfidfModel(corpus)
        directory = '{}/src/wkdir'.format(self.parent_dir_name)
        if not os.path.exists(directory):
            os.makedirs(directory)
        sims = gensim.similarities.Similarity(directory, tf_idf[corpus],
                                              num_features=len(dictionary))

        # Create bag-of-words from question query
        question_doc = [t.text for t in contents[self.question_without_negative]]
        query_doc_bow = dictionary.doc2bow(question_doc)
        query_doc_tf_idf = tf_idf[query_doc_bow]
        similarities = sims[query_doc_tf_idf].tolist()

        self.data['cosine_similarity_raw'] = similarities

    @timeit
    def word_count_appended(self):
        counts = []
        contents = {}
        threads = []

        # Grab each appended search
        for answer in self.answers:
            t = threading.Thread(target=self.grab_content, args=(contents, self.concatenate_answer_to_question(answer)))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        for answer in self.answers:
            counts.append(float(contents[self.concatenate_answer_to_question(answer)].count(answer)))

        self.data['word_count_appended'] = counts

    @timeit
    def word_count_appended_bing(self):
        counts = []
        contents = {}
        threads = []

        # Grab each appended search
        for answer in self.answers:
            t = threading.Thread(target=self.grab_content_bing, args=(contents, self.concatenate_answer_to_question(answer)))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        for answer in self.answers:
            counts.append(float(contents[self.concatenate_answer_to_question(answer)].count(answer)))

        self.data['word_count_appended_bing'] = counts

    @timeit
    def word_count_appended_relation_to_question(self):
        counts = []
        contents = {}
        threads = []

        # Grab each appended search
        for answer in self.answers:
            t = threading.Thread(target=self.grab_content, args=(contents, self.concatenate_answer_to_question(answer)))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # Count occurences for each entity in each answer search
        counts = [0.0] * len(self.answers)
        for word in self.important_words:
            curr_counts = []
            for answer in self.answers:
                curr_counts.append(float(contents[self.concatenate_answer_to_question(answer)].count(word)))
            try:
                curr_counts = [count / sum(curr_counts) for count in curr_counts]
            except ZeroDivisionError:
                print 'The word "{}" was not found in any answer search'.format(word)
                continue
            counts = [x + y for x, y in zip(counts, curr_counts)]

        self.data['word_count_appended_relation_to_question'] = counts

    @timeit
    def answer_relation_to_question(self):
        # Grab google search for each answer and save contents
        contents = {}
        threads = []

        for answer in self.answers:
            t = threading.Thread(target=self.grab_content, args=(contents, answer,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # Count occurences for each entity in each answer search
        counts = [0.0] * len(self.answers)
        for word in self.important_words:
            curr_counts = []
            for answer in self.answers:
                curr_counts.append(float(contents[answer].count(word)))
            try:
                curr_counts = [count / sum(curr_counts) for count in curr_counts]
            except ZeroDivisionError:
                print 'The word "{}" was not found in any answer search'.format(word)
                continue
            counts = [x + y for x, y in zip(counts, curr_counts)]

        self.data['answer_relation_to_question'] = counts

    @timeit
    def answer_relation_to_question_bing(self):
        # Grab google search for each answer and save contents
        contents = {}
        threads = []
        
        for answer in self.answers:
            t = threading.Thread(target=self.grab_content_bing, args=(contents, answer,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # Count occurences for each entity in each answer search
        counts = [0.0] * len(self.answers)
        for word in self.important_words:
            curr_counts = []
            for answer in self.answers:
                curr_counts.append(float(contents[answer].count(word)))
            try:
                curr_counts = [count / sum(curr_counts) for count in curr_counts]
            except ZeroDivisionError:
                print 'The word "{}" was not found in any answer search'.format(word)
                continue
            counts = [x + y for x, y in zip(counts, curr_counts)]

        self.data['answer_relation_to_question_bing'] = counts

    @timeit
    def question_related_to_answer(self):
        # Grab google search for each answer and save contents
        contents = {}
        threads = []

        for word in self.noun_chunks:
            t = threading.Thread(target=self.grab_content, args=(contents, word,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # Count occurences for each entity in each answer search
        counts = [0.0] * len(self.answers)
        for word in self.noun_chunks:
            curr_counts = []
            for answer in self.answers:
                curr_counts.append(float(contents[word].count(answer)))
            try:
                curr_counts = [count / sum(curr_counts) for count in curr_counts]
            except ZeroDivisionError:
                try:
                    print 'No occurences of any answer exist for the query of "{}"'.format(word)
                except UnicodeEncodeError:
                    print 'No occurences of any answer exist for the query of "{}"'.format(word.encode('utf-8'))
                continue
            counts = [x + y for x, y in zip(counts, curr_counts)]

        self.data['question_related_to_answer'] = counts

    @timeit
    def question_related_to_answer_bing(self):
        # Grab google search for each answer and save contents
        contents = {}
        threads = []
        
        for word in self.noun_chunks:
            t = threading.Thread(target=self.grab_content_bing, args=(contents, word,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # Count occurences for each entity in each answer search
        counts = [0.0] * len(self.answers)
        for word in self.noun_chunks:
            curr_counts = []
            for answer in self.answers:
                curr_counts.append(float(contents[word].count(answer)))
            try:
                curr_counts = [count / sum(curr_counts) for count in curr_counts]
            except ZeroDivisionError:
                try:
                    print 'No occurences of any answer exist for the query of "{}"'.format(word)
                except UnicodeEncodeError:
                    print 'No occurences of any answer exist for the query of "{}"'.format(word.encode('utf-8'))
                continue
            counts = [x + y for x, y in zip(counts, curr_counts)]

        self.data['question_related_to_answer_bing'] = counts

    @timeit
    def result_count_noun_chunks(self):
        counts = []
        contents = {}
        threads = []
        
        for answer in self.answers:
            t = threading.Thread(target=self.grab_content, args=(contents, self.concatenate_answer_to_noun_chunks(answer),))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        for answer in self.answers:
            content = contents[self.concatenate_answer_to_noun_chunks(answer)]
            result = self.regex.search(content)
            try:
                count = float([int(s) for s in result.group(1).replace(',', '').split() if s.isdigit()][0])
                counts.append(count)
            except AttributeError:
                print 'There were no results for {}.'.format(answer)
                counts.append(0)

        self.data['result_count_noun_chunks'] = counts

    @timeit
    def result_count_important_words(self):
        counts = []
        contents = {}
        threads = []
        
        for answer in self.answers:
            t = threading.Thread(target=self.grab_content, args=(contents, self.concatenate_answer_to_important_words(answer),))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        for answer in self.answers:
            content = contents[self.concatenate_answer_to_important_words(answer)]
            result = self.regex.search(content)
            try:
                count = float([int(s) for s in result.group(1).replace(',', '').split() if s.isdigit()][0])
                counts.append(count)
            except AttributeError:
                print 'There were no results for {}.'.format(answer)
                counts.append(0)

        self.data['result_count_important_words'] = counts

    @timeit
    def result_count(self):
        counts = []
        contents = {}
        threads = []
        
        for answer in self.answers:
            t = threading.Thread(target=self.grab_content, args=(contents, self.concatenate_answer_to_question(answer),))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        for answer in self.answers:
            content = contents[self.concatenate_answer_to_question(answer)]
            result = self.regex.search(content)
            try:
                count = float([int(s) for s in result.group(1).replace(',', '').split() if s.isdigit()][0])
                counts.append(count)
            except AttributeError:
                print 'There were no results for {}.'.format(answer)
                counts.append(0)

        self.data['result_count'] = counts

    @timeit
    def result_count_bing(self):
        counts = []
        contents = {}
        threads = []
        
        for answer in self.answers:
            t = threading.Thread(target=self.grab_content_bing, args=(contents, self.concatenate_answer_to_question(answer),))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        for answer in self.answers:
            content = contents[self.concatenate_answer_to_question(answer)]
            result = self.regex_bing.search(content)
            try:
                count = float([int(s) for s in result.group(1).replace(',', '').split() if s.isdigit()][0])
                counts.append(count)
            except AttributeError:
                print 'There were no results for {}.'.format(answer)
                counts.append(0)

        self.data['result_count_bing'] = counts

    @timeit
    def wikipedia_search(self):
        # Grab wikipedia search for each answer and save contents
        contents = {}
        threads = []

        for answer in self.answers:
            t = threading.Thread(target=self.grab_wikipedia_content, args=(contents, answer,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()
        
        # Count occurences for each entity in each answer search
        counts = [0.0] * len(self.answers)
        for word in self.important_words:
            # Encode word to ascii if possible
            try:
                word = word.decode('utf-8').encode('ascii', 'ignore')
            except UnicodeEncodeError:
                pass
            curr_counts = []
            for answer in self.answers:
                try:
                    curr_counts.append(float(contents[answer].count(word)))
                except KeyError:
                    curr_counts.append(float(0))
            try:
                curr_counts = [count / sum(curr_counts) for count in curr_counts]
            except ZeroDivisionError:
                print 'The word. "{}" was not found in any search'.format(word)
                pass
            counts = [x + y for x, y in zip(counts, curr_counts)]

        self.data['wikipedia_search'] = counts

    def grab_wikipedia_content(self, contents, page):
        search_results = wikipedia.search(page)
        # In the case that no page exists, return False
        if not len(search_results):
            contents[page] = ''
            return
        try:
            contents[page] = wikipedia.WikipediaPage(title=search_results[0]).html()
        except wikipedia.exceptions.DisambiguationError as e:
            try:
                contents[page] = wikipedia.WikipediaPage(title=e.options[0]).html()
            except wikipedia.exceptions.PageError:
                contents[page] = wikipedia.WikipediaPage(title=e.options[1]).html()

    def grab_content(self, contents, question, num_results=100):
        contents[question] = self.get_lowered_google_search(question, num_results)

    def grab_content_bing(self, contents, question):
        contents[question] = self.get_lowered_bing_search(question)

    def word_count(self, content, words):
        counts = []
        for i in range(len(words)):
             counts.append(float(content.count(words[i])))

    @timeit
    def process_question(self):
        # Initialize nlp constants
        self.doc = self.nlp(unicode(self.question))
        self.doc_vectors = self.nlp_vector(unicode(self.question))
        # Word is part of the POS list and it is not a stop word (common word)
        self.important_words = [encode_unicode(t.text).lower() for t in self.doc if t.pos_ in self.POS_list and not t.is_stop]
        self.noun_chunks = [chunk.text for chunk in list(self.doc.noun_chunks)]
        self.noun_chunks_string = ' '.join(self.noun_chunks)
        print 'Evaluated important words: ' + str(self.important_words)
        print 'Evaluated noun_chunks: ' + str(self.noun_chunks)

    def concatenate_answer_to_question(self, answer):
        try:
            return u'{} "{}"'.format(self.question_without_negative, answer).encode('utf-8').strip()
        except UnicodeDecodeError:
            try:
                return u'{} "{}"'.format(self.question_without_negative.decode('utf-8'), answer.decode('utf-8')).encode('utf-8').strip()
            except UnicodeEncodeError:
                return u'{} "{}"'.format(self.question_without_negative, answer.decode('utf-8')).encode('utf-8').strip()
        

    def concatenate_answer_to_noun_chunks(self, answer):
        try:
            return u'{} "{}"'.format(self.noun_chunks_string, answer).encode('utf-8').strip()
        except UnicodeDecodeError:
            try:
                return u'{} "{}"'.format(self.noun_chunks_string.decode('utf-8'), answer.decode('utf-8')).encode('utf-8').strip()
            except UnicodeEncodeError:
                return u'{} "{}"'.format(self.noun_chunks_string, answer.decode('utf-8')).encode('utf-8').strip()

    def concatenate_answer_to_important_words(self, answer):
        try:
            return u'{} "{}"'.format(' '.join(self.important_words), answer).encode('utf-8').strip()
        except UnicodeDecodeError:
            return u'{} "{}"'.format(' '.join([string.decode('utf-8') for string in self.important_words]), answer.decode('utf-8')).strip()

    def get_lowered_google_search(self, question, num_results=100):
        google_query = 'https://www.google.com/search?num={}&q='.format(num_results)
        if question in self.get_lowered_google_search.currently_searching:
            # Block until the question is successfuly saved in memo
            while question not in self.get_lowered_google_search.memo:
                continue
            return self.get_lowered_google_search.memo[question]
        self.get_lowered_google_search.currently_searching.add(question)
        r = requests.get(google_query + question)
        lowered = unidecode(self.h.unescape(unicode(r.content.lower(), errors='ignore')))
        self.get_lowered_google_search.memo[question] = lowered
        # try:
            # with open(parent_dir_name + '/data/google_searches/{}'.format(filename_safe(question)), 'w') as f:
                # f.write(lowered)
        # except UnicodeEncodeError:
            # with open(parent_dir_name + '/data/google_searches/{}'.format(filename_safe(question.encode('utf-8'))), 'w') as f:
                # f.write(lowered)
        if 'our systems have detected unusual traffic from your computer network' in lowered:
            print 'Google rate limited your IP.'
            self.rate_limited = True
        return self.get_lowered_google_search.memo[question]
    get_lowered_google_search.memo = {}
    get_lowered_google_search.currently_searching = set()

    def get_lowered_bing_search(self, question):
        bing_query = 'https://www.bing.com/search?q=' 
        if question in self.get_lowered_bing_search.currently_searching:
            # Block until the question is successfuly saved in memo
            while question not in self.get_lowered_bing_search.memo:
                continue
            return self.get_lowered_bing_search.memo[question]
        self.get_lowered_bing_search.currently_searching.add(question)
        r = requests.get(bing_query + question)
        lowered = unidecode(self.h.unescape(unicode(r.content.lower(), errors='ignore')))
        self.get_lowered_bing_search.memo[question] = lowered
        # try:
            # with open(parent_dir_name + '/data/bing_searches/{}'.format(filename_safe(question)), 'w') as f:
                # f.write(lowered)
        # except UnicodeEncodeError:
            # with open(parent_dir_name + '/data/bing_searches/{}'.format(filename_safe(question.encode('utf-8'))), 'w') as f:
                # f.write(lowered)
        return self.get_lowered_bing_search.memo[question]
    get_lowered_bing_search.memo = {}
    get_lowered_bing_search.currently_searching = set()

    def raw_counts_to_input(self):
        # Convert data to input data
        lines = [[], [], []]
        for k,v in sorted(list(self.data.iteritems())):  # The reason for sorted list is to guarantee the order in which all the approaches are appended
            try:
                # Make model input inverted if question is negative (makes more sense for model)
                if self.negative_question:
                    confidence_values = [1 - (val / sum(v)) for val in v]
                    confidence_values = [val/sum(confidence_values) for val in confidence_values]
                else:
                    confidence_values = [val/sum(v) for val in v]
            except ZeroDivisionError:
                confidence_values = [0, 0, 0]
            for i in range(len(confidence_values)):
                lines[i].append(confidence_values[i])

        # Append question type to the data
        for line in lines:
            for k,v in sorted(list(self.categorical_data.iteritems())):
                line.append(float(v))

        self.lines = lines
        return np.array(lines)

def main():
    solver = Answerer()
    pprint(solver.answer("Which of these is NOT a real animal?", ["liger", "wholphin", "jackalope"]))
    pprint(solver.answer(u'The word "robot" comes from a Czech word meaning what?',["forced labor","mindless","autonomous"]))
    pprint(solver.answer(u"""In which version of “Dragnet” is the line “Just the facts, ma’am” first said?""", ["50s TV show","'50s movie","'80s movie"]))
    pprint(solver.answer('Which of these two U.S. cities are in the same time zone?', ['El Paso / Pierre', 'Bismark / Cheyenne', 'Pensacola / Sioux Falls']))
    # pprint(solver.answer("Featuring 20 scoops of ice cream, the Vermonster is found on what chain's menu?", ['Baskin-Robbins','Dairy Queen',"Ben & Jerry's"]))
    # pprint(solver.answer(u'Which of these is NOT a constellation?',["fornax","draco","lucrus"]))
    # pprint(solver.answer('Which of these actresses is NOT mentioned in Madonna’s song “Vogue”?',['Jean Harlow','Audrey Hepburn','Rita Hayworth']))
    # pprint(solver.answer(u"If you tunneled through the center of the earth from Honolulu, what country would you end up in?",["Botswana","Norway","Mongolia"]))
    # pprint(solver.answer("Anne of Green Gables literally means Anne of what?",['Green pastures','Green jars','Green walls']))
    # pprint(solver.answer(u'Which of these is NOT one of the Great Lakes', ["Lake Superior", "Ricki Lake", "Lake Michigan"]))
    # pprint(solver.answer("In which state is happy hour currently banned?",["Illinois","Arizona","Rhode Island"]))
    # pprint(solver.answer(u'Which brand mascot was NOT a real person?', ["Little Debbie", "Sara Lee", "Betty Crocker"]))
    # pprint(solver.answer(u'Jennifer Hudson kicked off her musical career on which reality show?', ["american idol","america's got talent","the voice"]))
    # pprint(solver.answer(u'Basketball is NOT a major theme of which of these 90s movies?',["white men can't jump","point break","eddie"]))
    # pprint(solver.answer(u"Which of these countries is NOT a collaborating member on the International Space Station?",["China","Russia","Canada"]))
    # pprint(solver.answer(u'Which writer has stated that his/her trademark series of books would never be adapted for film?', ["James Patterson", "Sue Grafton", "Jeff Kinney"]))
    # pprint(solver.answer("In Harry Potter's Quidditch, what ALWAYS happens when one team catches the snitch?",["That team wins","That team loses","The game ends"]))
    # pprint(solver.answer(u"The Windows 95 startup sound was composed by a former member of what band?",["They Might Be Giants","Roxy Music","Devo"]))
    # pprint(solver.answer(u"Guatemala and Mozambique are the only UN countries with what on their flags?",["Firearm","Garden tool","Bird"]))
    # pprint(solver.answer(u"Which of these fitness fads came first?",["Tae Bo","Jazzercise","Zumba"]))
    # pprint(solver.answer(u"Which movie director's daughter made her directorial debut in 2017",["Nancy Meyers","David Lynch","Ridley Scott"]))
    # pprint(solver.answer(u'In which ocean would you find Micronesia?', ["atlantic","pacific","indian"]))
    # pprint(solver.answer(u'Microsoft Passport was previously known as what?',["ms id","ms single sign-on","net passport"]))
    # pprint(solver.answer(u'Which of these Uranus moons is NOT named after a Shakespearean character?', ['Oberon', 'Umbriel', 'Trinculo']))
    # pprint(solver.answer(u'Who was the first U.S President to be born in a hospital?',["immy carter","richard nixon","franklin d. roosevelt"]))
    # pprint(solver.answer(u'The Ewing family in the TV show "Dallas" made their money in which commodity?',["oil","coal","steel"]))
    # pprint(solver.answer(u'Which video game motion-captured "Mad Men" actor Aaron Staton as its star?',["medal of honor","l.a. noire","assassin's creed 2"]))
    # pprint(solver.answer(u'The lyrics to "The Start-Spangled Banner" were written during what conflict?', ['The Civil War', 'American Revolution', 'The War of 1812']))
    # pprint(solver.answer(u'Which of these countries has the longest operating freight trains in the world?',["japan","brazil","canada"]))
    # pprint(solver.answer(u'Whose cat is petrified by the basilisk in "Harry Potter and the Chamber of Secrets"?',["poppy pomfrey","gilderoy lockhart","argus filch"]))
    # pprint(solver.answer(u'"The Blue Danube" isa waltz by which composer?',["richard strauss","johann strauss i","franz strauss"]))

if __name__ == "__main__":
    main()
