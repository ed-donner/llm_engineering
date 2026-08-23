import asyncio

from random import uniform
from time import sleep


class Helper:

    @staticmethod
    async def pretend_streaming(text:str):
        result_text = ''
        for word in text.split(' '):
            result_text += word + ' '
            await asyncio.sleep(uniform(0, 0.1))
            yield None, result_text

    def translate_to(self, lang:str):
        pass

helper = Helper()