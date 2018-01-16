import argparse

def get_args():
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('-d', action='store_true', help='Run in debug mode or production mode')
    parser.add_argument('-a', action='store_true', help='Run in answerer debug mode')
    return parser.parse_args()

