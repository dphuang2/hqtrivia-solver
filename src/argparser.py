import argparse

def get_args():
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('--debug', action='store_true', help='Run in debug mode or production mode')
    return parser.parse_args()

