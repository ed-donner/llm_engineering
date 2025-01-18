from .builder import llm_builder


class LLMService:
    def __init__(self, model_type, model_name, crawl_type):

        self.llm = llm_builder(model_type, model_name, crawl_type)

    async def generate_response(self, crawl_result,
                                url,
                                description,
                                site_type
                                ):
        async for response_chunk in self.llm.generate(content=crawl_result,
                                                      url=url, description=description,
                                                      site_type=site_type
                                                      ):
            yield response_chunk
