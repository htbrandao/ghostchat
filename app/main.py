import asyncio
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .routes import router
from .ws import websocket_endpoint
from .cleanup import cleanup_expired_boards

app = FastAPI()
app.include_router(router)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.add_api_websocket_route("/ws/{board_id}", websocket_endpoint)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(cleanup_expired_boards())
