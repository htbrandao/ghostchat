import secrets
import uuid
from datetime import datetime, timedelta
from typing import List, Dict
import bcrypt

from .crypto import derive_kek, generate_data_key, encrypt_with_kek
from .crypto import DATA_KEY_LENGTH, NONCE_LENGTH, KDF_ITERS


BOARD_LIFETIME = timedelta(hours=12)


class EncryptedMessage:
    def __init__(self, ciphertext: bytes, nonce: bytes, ts: datetime, sender: str):
        self.ciphertext = ciphertext
        self.nonce = nonce
        self.ts = ts
        self.sender = sender

    def to_dict(self):
        return {
            "ciphertext": self.ciphertext.hex(),
            "nonce": self.nonce.hex(),
            "ts": self.ts.isoformat(),
            "sender": self.sender,
        }


class Board:
    def __init__(self, name: str, password: str):
        self.id = str(uuid.uuid4())
        self.name = name or ""
        self.created_at = datetime.utcnow()
        self.expires_at = self.created_at + BOARD_LIFETIME

        # Password hash
        self.password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

        # KDF params
        self.kdf_salt = secrets.token_bytes(16)
        self.kdf_iters = KDF_ITERS

        # Data key (random) encrypted with KEK
        data_key = generate_data_key()
        kek = derive_kek(password, self.kdf_salt, self.kdf_iters)
        self.encrypted_data_key, self.encrypted_data_key_nonce = encrypt_with_kek(kek, data_key)

        self.messages: List[EncryptedMessage] = []
        self.connections: Dict[str, any] = {}  # client_id -> websocket

    def to_public(self):
        return {
            "id": self.id,
            "name": self.name,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "user_count": len(self.connections),
        }
