from HTMLParser import HTMLParser
from bs4 import BeautifulSoup
from spacy.tokenizer import Tokenizer
from unidecode import unidecode
import gensim
import pdb
import requests
import spacy

nlp = spacy.load('en')
tokenizer = Tokenizer(nlp.vocab) # slightly faster processing for tokenizing
h = HTMLParser()

question = requests.get('https://www.google.com/search?num=100&q=If you tunneled through the center of the earth from Honolulu, what country would you end up in?')
answer_1 = requests.get('https://www.google.com/search?num=100&q=If you tunneled through the center of the earth from Honolulu, what country would you end up in? "Botswana"')
answer_2 = requests.get('https://www.google.com/search?num=100&q=If you tunneled through the center of the earth from Honolulu, what country would you end up in? "Norway"')
answer_3 = requests.get('https://www.google.com/search?num=100&q=If you tunneled through the center of the earth from Honolulu, what country would you end up in? "Mongolia"')

question = unidecode(h.unescape(unicode(question.content.lower(), errors='ignore')))
answer_1 = unidecode(h.unescape(unicode(answer_1.content.lower(), errors='ignore')))
answer_2 = unidecode(h.unescape(unicode(answer_2.content.lower(), errors='ignore')))
answer_3 = unidecode(h.unescape(unicode(answer_3.content.lower(), errors='ignore')))

question_soup = BeautifulSoup(question, 'html.parser')
answer_1_soup = BeautifulSoup(answer_1, 'html.parser')
answer_2_soup = BeautifulSoup(answer_2, 'html.parser')
answer_3_soup = BeautifulSoup(answer_3, 'html.parser')

question_text = ' '.join([t.getText() for t in question_soup.findAll("span", {"class": "st"})])
answer_1_text = ' '.join([t.getText() for t in answer_1_soup.findAll("span", {"class": "st"})])
answer_2_text = ' '.join([t.getText() for t in answer_2_soup.findAll("span", {"class": "st"})])
answer_3_text = ' '.join([t.getText() for t in answer_3_soup.findAll("span", {"class": "st"})])

question_doc = tokenizer(unicode(question_text))
answer_1_doc = tokenizer(unicode(answer_1_text))
answer_2_doc = tokenizer(unicode(answer_2_text))
answer_3_doc = tokenizer(unicode(answer_3_text))

docs = [answer_1_doc, answer_2_doc, answer_3_doc]
gen_docs = [[t.text for t in doc] for doc in docs]
dictionary = gensim.corpora.Dictionary(gen_docs)
corpus = [dictionary.doc2bow(gen_doc) for gen_doc in gen_docs]
tf_idf = gensim.models.TfidfModel(corpus)
sims = gensim.similarities.Similarity('./wkdir',tf_idf[corpus],
                                      num_features=len(dictionary))
question_input = [t.text for t in question_doc]
query_doc_bow = dictionary.doc2bow(question_input)
query_doc_tf_idf = tf_idf[query_doc_bow]
sims[query_doc_tf_idf]
pdb.set_trace()
