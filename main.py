#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import os

# Allows us to import scripts from src folder
parent_dir_name = os.path.dirname(os.path.realpath(__file__))
sys.path.append(parent_dir_name + "/src")

from argparser import get_args
from answerer import Answerer
from pprint import pprint
import websocket
import requests
import time
import json 
import pdb

BEARER_TOKEN  = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOjEwMzY5MjkwLCJ1c2VybmFtZSI6ImJhbHBodXMiLCJhdmF0YXJVcmwiOiJzMzovL2h5cGVzcGFjZS1xdWl6L2RlZmF1bHRfYXZhdGFycy9VbnRpdGxlZC0xXzAwMDRfZ29sZC5wbmciLCJ0b2tlbiI6bnVsbCwicm9sZXMiOltdLCJjbGllbnQiOiIiLCJndWVzdElkIjpudWxsLCJpYXQiOjE1MTc3MzEyMTcsImV4cCI6MTUyNTUwNzIxNywiaXNzIjoiaHlwZXF1aXovMSJ9.2r6bo9ANnsbXOL7VeK-3HdAE-9A_ttrMs6ll4_PrbKU"
args = get_args()
DEBUG = args.d

def on_message(ws, message):
    data = json.loads(message)
    if data['type'] == 'question':
        if not DEBUG:
            on_message.logger.write(message)
            on_message.logger.write('\n')
        question = data['question']
        answers = [answer['text'] for answer in data['answers']]
        print "Question: " + question
        print "Answers: " + str(answers)
        if not args.collect:
            if question not in on_message.memo:
                    on_message.memo[question] = on_message.solver.answer(question, answers)
            pprint(on_message.memo[question])
    elif data['type'] == 'questionSummary':
        on_message.logger.write(message)
        on_message.logger.write('\n')
    elif data['type'] == 'broadcastEnded':
        print 'The broadcast ended'
        ws.close()
print 'Instantiating Answerer class...make take a while'
on_message.solver = Answerer()
print 'Done Instantiating Answerer class!'
on_message.memo = {}
on_message.logger = open(parent_dir_name + '/data/log', 'a+')

def on_error(ws, error):
    print(error)
    print("### error ###")

def on_close(ws):
    print("### closed ###")

def on_open(ws):
    print("### opened ###")

def setup_websocket(url, header):
    if args.d:
        websocket.enableTrace(True)
    ws = websocket.WebSocketApp(url, header)
    ws.on_open = on_open
    ws.on_close = on_close
    ws.on_message = on_message
    ws.on_error = on_error
    return ws

def prompt_continue():
    key = ''
    while key != 'y' or key != 'n':
        key = raw_input("Continue? (y/n)\n")
        if key == 'y':
            return True
        elif key == 'n':
            return False

def get_show_status():
    GET_SHOW_URL = 'https://api-quiz.hype.space/shows/now?type=hq' 
    r = requests.get(GET_SHOW_URL, headers={"Authorization": BEARER_TOKEN});
    return r.json()

if __name__ == "__main__":
    if args.a:
        from answerer import main
        main()
        exit()
    if args.collect:
        print "Running in collect mode"
    while True:
        # Send GET request to receive live show status and socketUrl
        print 'QUERYING SHOW STATUS'
        show_status = get_show_status()
        if not show_status['active']: # Reset if show is not acrtive
            print 'The show is not live.'
            if not DEBUG:
                if prompt_continue():
                    print
                    continue
                else:
                    exit()

        try:
            if DEBUG:
                websocket_url = 'ws://localhost:8080' 
            else:
                websocket_url = show_status['broadcast']['socketUrl'] # 'https://ws-quiz.hype.space/ws/43041' 
        except KeyError:
            print 'HQ Trivia has changed their schema, update the code!'
            exit()
        websocket_url = websocket_url.replace('https', 'wss')

        print 'The show is live!'
        print
        print 'SETTING UP WEBSOCKET TO URL: ' + websocket_url
        # Set up websocket to socketUrl and connect
        ws = setup_websocket(websocket_url, {
            'Sec-WebSocket-Protocol': 'permessage-deflate',
            'Authorization': BEARER_TOKEN,
            'User-Agent': 'HQ/1.2.7 (iPhone; iOS 11.2.1; Scale/3.00)',
            'Accept-Encoding': 'br, gzip, deflate',
            'Connection': 'keep-alive',
            'Accept': '*/*',
            'Accept-Language': 'en-US;q=1'
            })

        # Run websocket forever and reconnect on failure
        if DEBUG:
            print 'Running run_forever() once'
            ws.run_forever()
            exit()
        else:
            while True:
                ws.run_forever()
                print 'Connection to websocket closed...starting again'
            print 'How did you get here?'
