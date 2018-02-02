#!/usr/bin/env python
import multiprocessing
from time import time
import urllib2

# def millis():
  # return int(round(time.time() * 1000))

# def http_get(url):
  # start_time = millis()
  # result = {"url": url, "data": urllib2.urlopen(url, timeout=5).read()[:100]}
  # print url + " took " + str(millis() - start_time) + " ms"
  # return result
  
# pool = Pool(processes=len(urls))

# start_time = millis()
# results = pool.map(http_get, urls)

# print "\nTotal took " + str(millis() - start_time) + " ms\n"

import threading

# def millis():
  # return int(round(time.time() * 1000))

# results = []

# def http_get(url):
  # start_time = millis()
  # result = {"url": url, "data": urllib2.urlopen(url, timeout=5).read()[:100]}
  # print url + " took " + str(millis() - start_time) + " ms"
  # results.append(result)
  

# threads = []
# start_time = millis()
# for url in urls:
    # t = threading.Thread(target=http_get, args=(url,))
    # threads.append(t)
    # t.start()
# for t in threads:
    # t.join()

# print "\nTotal took " + str(millis() - start_time) + " ms\n"

def test():
    x = 0
    for i in range(1000000):
        x *= x
    return x

processes = []
t1 = time()
for i in range(15):
    p = multiprocessing.Process(target=test)
    processes.append(p)
    p.start()
for p in processes:
    p.join()
print 'Time taking for processes: {}'.format(time() - t1)


threads = []
t1 = time()
for i in range(15):
    t = threading.Thread(target=test)
    threads.append(t)
    t.start()
for t in threads:
    t.join()
print 'Time taking for threads: {}'.format(time() - t1)
