from fastapi import FastAPI
import uvicorn
from routes import router
from dotenv import load_dotenv
import os

load_dotenv()
app = FastAPI()
app.include_router(router)


if __name__ == '__main__':
    host = os.getenv("SOCKET_HOST", "127.101.43.41")
    port = int(os.getenv("SOCKET_PORT", 8329))
    uvicorn.run("main:app", host=host, port=port,
                reload=True)
