import uuid
import json
import secrets

from fastapi import WebSocket
from datetime import datetime
from fastapi.websockets import WebSocketDisconnect
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from .routes import boards
from .crypto import derive_kek
from .models import EncryptedMessage


async def websocket_endpoint(websocket: WebSocket, board_id: str):
    await websocket.accept()
    params = dict(websocket.query_params)
    password = params.get("password")
    if not password:
        await websocket.send_json({"error": "password required"})
        await websocket.close(code=1008)
        return

    board = boards.get(board_id)
    if not board:
        await websocket.send_json({"error": "board not found"})
        await websocket.close(code=1008)
        return

    if len(board.connections) >= 2:
        await websocket.send_json({"error": "board full"})
        await websocket.close(code=1008)
        return

    try:
        kek = derive_kek(password, board.kdf_salt, board.kdf_iters)
        aesgcm = AESGCM(kek)
        data_key = aesgcm.decrypt(board.encrypted_data_key_nonce, board.encrypted_data_key, None)
    except Exception:
        await websocket.send_json({"error": "bad password"})
        await websocket.close(code=1008)
        return

    client_id = str(uuid.uuid4())
    board.connections[client_id] = websocket
    aes_data = AESGCM(data_key)

    # Send last 20 messages
    recent = []
    for m in board.messages[-20:]:
        try:
            pt = aes_data.decrypt(m.nonce, m.ciphertext, None).decode("utf-8")
        except Exception:
            pt = "<decrypt error>"
        recent.append({"ts": m.ts.isoformat(), "sender": m.sender, "text": pt})
    await websocket.send_json({"type": "history", "messages": recent})

    try:
        while True:
            data = await websocket.receive_text()
            try:
                payload = json.loads(data)
                text = payload.get("text")
            except Exception:
                text = data
            if not text:
                continue
            nonce = secrets.token_bytes(12)
            ct = aes_data.encrypt(nonce, text.encode("utf-8"), None)
            m = EncryptedMessage(ciphertext=ct, nonce=nonce, ts=datetime.utcnow(), sender=client_id)
            board.messages.append(m)
            payload_out = {"type": "message", "ts": m.ts.isoformat(), "sender": m.sender, "text": text}
            disconnected = []
            for cid, ws in list(board.connections.items()):
                try:
                    await ws.send_json(payload_out)
                except Exception:
                    disconnected.append(cid)
            for cid in disconnected:
                board.connections.pop(cid, None)
    except WebSocketDisconnect:
        pass
    finally:
        board.connections.pop(client_id, None)
