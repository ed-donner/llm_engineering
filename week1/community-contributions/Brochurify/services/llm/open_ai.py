import json
import os
from typing import Dict, List

from openai import AsyncOpenAI
from .summarizer_llm import BaseSummarizer


class OpenAISummarize(BaseSummarizer):
    def __init__(self, model_name: str = "gpt-4o-mini"):
        self.model = model_name
        api_key = os.getenv("OPENAI_API_KEY")
        self.openai = AsyncOpenAI(api_key=api_key)

    async def generate(self, url, content: List[Dict], description,
                       site_type):
        content_dict = {item['url']: item for item in content}
        links = list(content_dict.keys())

        yield f"Now I Am filtering links that i found on {url}\n"
        new_links = await self.remove_unnecessary_link(url=url,
                                                       links=links,
                                                       description=description,
                                                       site_type=site_type)
        yield "Links have been filtered. Advancing...\n\n"

        new_links = new_links['links']

        filtered_content = [content_dict[link_info['url']] for link_info in new_links if
                            link_info['url'] in content_dict]

        yield "It's Almost Done\n"
        prompt = self.get_boruchure_prompt(filtered_content)
        response = await self.openai.chat.completions.create(model="gpt-4o-mini",
                                                             messages=prompt, stream=True)

        async for response_chunk in response:
            yield response_chunk.choices[0].delta.content

    async def remove_unnecessary_link(self, url, links, description,
                                      site_type):

        prompt = self.prompts_for_removing_links(url=url,
                                                 description=description,
                                                 site_type=site_type,
                                                 links=links)
        links = await self.openai.chat.completions.create(
            messages=prompt,
            model=self.model,
            response_format={"type": "json_object"}
        )
        result = links.choices[0].message.content
        return json.loads(result)

    @staticmethod
    def get_boruchure_prompt(link_content_list):
        system_prompt = "You are an assistant that analyzes \
        the contents of several relevant pages from a company website \
        and creates a short brochure about the company for prospective\
         customers, investors and recruits. Respond in markdown.\
        Include details of company culture, customers and careers/jobs if you have the information."
        user_prompt = f"Here are the contents of its landing page and other relevant pages; \
        use this information to build a short brochure of the company in markdown.\n"
        result = "links content are :\n\n"
        for item in link_content_list:
            link = item['url']
            content = item['content']
            result += f"url: {link},\t content: {content[:2000]}"
        user_prompt += result
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
