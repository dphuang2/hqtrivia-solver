import threading
import datetime
import random
from time import time, sleep


def my_sleep_func():
    sleep(3)


def display_date(num):
    end_time = time() + 15.0
    while True:
        print("Loop: {} Time: {}".format(num, datetime.datetime.now()))
        if (time() + 1.0) >= end_time:
            break
        my_sleep_func()


for i in range(15):
    t = threading.Thread(target=display_date, args=(i,))
    t.start()
