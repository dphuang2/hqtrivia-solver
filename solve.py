#!/usr/bin/env python
import websocket
import googler
import requests
import json 

def on_message(ws, message):
    data = json.loads(message)
    print data
    if data['type'] == 'question':
        question = data['question']
        answers = data['answers']
    elif data['type'] == 'broadcastEnded':
        ws.close()

def on_error(ws, error):
    print(error)

def on_close(ws):
    print("### closed ###")

def on_open(ws):
    print("### opened ###")

def setup_websocket(url, header):
    # websocket.enableTrace(True)
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
    BEARER_TOKEN  = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOjUxMzU4NjAsInVzZXJuYW1lIjoiYmFscGhpIiwiYXZhdGFyVXJsIjoiaHR0cHM6Ly9kMnh1MWhkb21oM25yeC5jbG91ZGZyb250Lm5ldC9kZWZhdWx0X2F2YXRhcnMvVW50aXRsZWQtMV8wMDAyX3B1cnBsZS5wbmciLCJ0b2tlbiI6bnVsbCwicm9sZXMiOltdLCJjbGllbnQiOiJpT1MvMS4yLjYgYjY1IiwiZ3Vlc3RJZCI6bnVsbCwiaWF0IjoxNTE1NTQ5OTgxLCJleHAiOjE1MjMzMjU5ODEsImlzcyI6Imh5cGVxdWl6LzEifQ.7yeagYnF7UdXjMlar_rEzau7HClx0FgXLpVPxMTMB2c"
    GET_SHOW_URL = 'https://api-quiz.hype.space/shows/now?type=hq&userId=5135860' 
    r = requests.get(GET_SHOW_URL, headers={"Authorization": BEARER_TOKEN});
    return r.json()

if __name__ == "__main__":
    while True:
        # Send GET request to receive live show status and socketUrl
        show_status = get_show_status()
        if not show_status['active']: # Reset if show is not acrtive
            print 'The show is not live.'
            exit()

        websocket_url = show_status['broadcast']['socketUrl']
        # Set up websocket to socketUrl and connect
        ws = setup_websocket(websocket_url, {'Sec-WebSocket-Protocol': 'permessage-deflate', 'Authorization': BEARER_TOKEN})
        ws.run_forever()
        if prompt_continue():
            continue
        else:
            break
