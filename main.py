#!/usr/bin/env python
from argparser import get_args
from answerer import Answerer
import websocket
import requests
import time
import json 
import sys
import pdb

BEARER_TOKEN  = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOjUxMzU4NjAsInVzZXJuYW1lIjoiYmFscGhpIiwiYXZhdGFyVXJsIjoiaHR0cHM6Ly9kMnh1MWhkb21oM25yeC5jbG91ZGZyb250Lm5ldC9kZWZhdWx0X2F2YXRhcnMvVW50aXRsZWQtMV8wMDAyX3B1cnBsZS5wbmciLCJ0b2tlbiI6bnVsbCwicm9sZXMiOltdLCJjbGllbnQiOiJpT1MvMS4yLjYgYjY1IiwiZ3Vlc3RJZCI6bnVsbCwiaWF0IjoxNTE1NTQ5OTgxLCJleHAiOjE1MjMzMjU5ODEsImlzcyI6Imh5cGVxdWl6LzEifQ.7yeagYnF7UdXjMlar_rEzau7HClx0FgXLpVPxMTMB2c"
DEBUG = False

def on_message(ws, message):
    if not DEBUG:
        on_message.logger.write(message)
        on_message.logger.write('\n')
    data = json.loads(message)
    if data['type'] == 'question':
        question = data['question']
        answers = [answer['text'] for answer in data['answers']]
        print "Question: " + question
        print "Answers: " + str(answers)
        if question in on_message.memo:
            return
        else:
            answer = on_message.solver.answer(question, answers)
            on_message.memo[question] = answer
            print answer
    elif data['type'] == 'broadcastEnded':
        print 'The broadcast ended'
on_message.solver = Answerer()
on_message.memo = {}
on_message.logger = open('log', 'a+')

def on_error(ws, error):
    print("### error ###")
    print(error)

def on_close(ws):
    print("### closed ###")

def on_open(ws):
    print("### opened ###")

def setup_websocket(url, header):
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
    GET_SHOW_URL = 'https://api-quiz.hype.space/shows/now?type=hq&userId=5135860' 
    r = requests.get(GET_SHOW_URL, headers={"Authorization": BEARER_TOKEN});
    return r.json()

if __name__ == "__main__":
    DEBUG = get_args().debug
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
        ws = setup_websocket(websocket_url, {'Sec-WebSocket-Protocol': 'permessage-deflate', 'Authorization': BEARER_TOKEN})

        # Run websocket forever and reconnect on failure
        if DEBUG:
            print 'Running run_forever() once'
            ws.run_forever()
            exit()
        else:
            while True:
                ws.run_forever()
            print 'How did you get here?'
