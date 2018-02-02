import asyncio
import datetime
import random


async def my_sleep_func():
    await asyncio.sleep(3)


async def display_date(num, loop):
    end_time = loop.time() + 15.0
    while True:
        print("Loop: {} Time: {}".format(num, datetime.datetime.now()))
        if (loop.time() + 1.0) >= end_time:
            break
        await my_sleep_func()


loop = asyncio.get_event_loop()

asyncio.ensure_future(display_date(1, loop))
asyncio.ensure_future(display_date(2, loop))
asyncio.ensure_future(display_date(3, loop))
asyncio.ensure_future(display_date(4, loop))
asyncio.ensure_future(display_date(5, loop))
asyncio.ensure_future(display_date(6, loop))
asyncio.ensure_future(display_date(7, loop))
asyncio.ensure_future(display_date(8, loop))
asyncio.ensure_future(display_date(9, loop))
asyncio.ensure_future(display_date(10, loop))
asyncio.ensure_future(display_date(11, loop))
asyncio.ensure_future(display_date(12, loop))
asyncio.ensure_future(display_date(13, loop))
asyncio.ensure_future(display_date(14, loop))
asyncio.ensure_future(display_date(15, loop))

loop.run_forever()
