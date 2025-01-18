import json

from services import Orchestrator
from services.crawler import CrawlerService
from fastapi import WebSocket, WebSocketDisconnect, APIRouter

from services.llm import LLMService
from services.socket import ConnectionManager
manager = ConnectionManager()
router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    user_unique_id = await manager.connect(websocket)
    try:
        data = await websocket.receive_text()
        data = json.loads(data)
        user_state = manager.get_user_state(user_unique_id)
        if not user_state:
            orchestrator = Orchestrator(crawler_service=CrawlerService(url=data['url'],
                                                                       crawl_type=data['crawlType']),
                                        llm_service=LLMService(model_type='openai',
                                                               model_name="gpt-4o-mini",
                                                               crawl_type='summarize'))

            status_message = dict(type="status", message="Processing your request...")

            await manager.send_message(unique_id=user_unique_id,
                                       message=json.dumps(status_message))

            manager.modify_user_state(user_unique_id, "crawling")

            async for update in orchestrator.stream_website_data(
                    user_id=user_unique_id, manager=manager,
                    description=data['description'], url=data['url'],
                    site_type=data['siteType']):
                message = dict(type="message", message=update,
                               is_complete=False)
                await manager.send_message(user_unique_id, json.dumps(message))

            status_message = dict(type="status", message="Disconnecting YOU NOW")
            message = dict(type="message", message="..",
                           is_complete=True)
            await manager.send_message(user_unique_id, json.dumps(message))
            await manager.send_message(user_unique_id, json.dumps(status_message))
            await manager.disconnect(user_unique_id)

    except WebSocketDisconnect:
        await manager.disconnect(user_unique_id)
