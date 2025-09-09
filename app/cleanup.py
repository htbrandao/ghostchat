import asyncio

from .routes import boards
from datetime import datetime


async def cleanup_expired_boards():
    while True:
        await asyncio.sleep(60)
        now = datetime.utcnow()
        expired = [b_id for b_id, b in boards.items() if b.expires_at <= now]
        for b_id in expired:
            board = boards.pop(b_id, None)
            if board:
                for ws in list(board.connections.values()):
                    try:
                        await ws.close(code=1000)
                    except Exception:
                        pass
