import argparse

def get_args():
    parser = argparse.ArgumentParser(description='Answer some trivia questions')
    parser.add_argument('-d', action='store_true', help='Run in debug mode (expects websocketd using tools/websocket_test.py) ')
    parser.add_argument('-a', action='store_true', help='Run in answerer debug mode')
    return parser.parse_args()

