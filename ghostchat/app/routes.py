from fastapi import APIRouter, Body, HTTPException, Request
from fastapi.templating import Jinja2Templates

from .models import Board
from .crypto import derive_kek
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import bcrypt

boards = {}
templates = Jinja2Templates(directory="ghostchat/app/templates")

router = APIRouter()


@router.get("/")
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@router.post("/boards")
async def create_board(payload: dict = Body(...)):
    name = payload.get("name")
    password = payload.get("password")
    if not password or len(password) < 6:
        raise HTTPException(status_code=400, detail="Password required (min 6 chars)")
    board = Board(name=name, password=password)
    boards[board.id] = board
    return {"id": board.id, "expires_at": board.expires_at.isoformat()}


@router.get("/boards/{board_id}")
async def chat_page(board_id: str, request: Request):
    if board_id not in boards:
        raise HTTPException(status_code=404, detail="Board not found")
    return templates.TemplateResponse("chat.html", {"request": request, "board_id": board_id})


@router.get("/boards")
async def list_boards():
    return [b.to_public() for b in boards.values()]


@router.post("/boards/{board_id}/delete")
async def delete_board(board_id: str, payload: dict = Body(...)):
    password = payload.get("password")
    board = boards.get(board_id)
    if not board:
        raise HTTPException(status_code=404, detail="Board not found")
    if not password or not bcrypt.checkpw(password.encode("utf-8"), board.password_hash):
        raise HTTPException(status_code=403, detail="Bad password")
    for ws in list(board.connections.values()):
        try:
            await ws.close(code=1000)
        except Exception:
            pass
    boards.pop(board_id, None)
    return {"ok": True}
