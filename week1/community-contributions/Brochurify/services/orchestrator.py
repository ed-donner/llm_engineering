import json
from services.socket import ConnectionManager


class Orchestrator:
    def __init__(self, crawler_service, llm_service):
        self.crawler_service = crawler_service
        self.llm_service = llm_service

    async def stream_website_data(self, user_id: str, manager: ConnectionManager,
                                  description,
                                  site_type,
                                  url):

        await manager.send_message(user_id, "Starting crawling process...")
        crawl_result = await self.crawler_service.crawl()

        status_message = dict(type="status", message="Processing content with LLM...")
        await manager.send_message(user_id, json.dumps(status_message))
        async for llm_update in self.llm_service.generate_response(
                url=url, crawl_result=crawl_result, description=description,
                site_type=site_type):
            yield llm_update
