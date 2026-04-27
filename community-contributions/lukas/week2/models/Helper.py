import asyncio

from random import uniform
from time import sleep


class Helper:

    @staticmethod
    async def to_async_iterable(iterable):
        for _ in iterable:
            yield _

    @staticmethod
    def to_sync_iterable(async_generator):
        event_loop = asyncio.get_event_loop()
        try:
            while True:
                try:
                    item = async_generator.__anext__()
                    res = event_loop.run_until_complete(item)
                except StopAsyncIteration:
                    return
                else:
                    yield res
        finally:
            coro = event_loop.shutdown_asyncgens()
            event_loop.run_until_complete(coro)

    @staticmethod
    def pretend_streaming(text:str):
        result_text = ''
        for word in text.split(' '):
            result_text += word + ' '
            sleep(uniform(0, 0.1))
            yield None, result_text

    def translate_to(self, lang:str):
        pass

helper = Helper()