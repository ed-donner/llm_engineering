from fastapi import APIRouter
from .socket import socket_router
router = APIRouter()
router.include_router(socket_router, prefix="/socket")
