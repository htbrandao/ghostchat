import secrets
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

DATA_KEY_LENGTH = 32
NONCE_LENGTH = 12
KDF_ITERS = 100_000


def derive_kek(password: str, salt: bytes, iterations: int) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=iterations,
        backend=default_backend(),
    )
    return kdf.derive(password.encode("utf-8"))


def generate_data_key() -> bytes:
    return secrets.token_bytes(DATA_KEY_LENGTH)


def encrypt_with_kek(kek: bytes, data_key: bytes):
    aesgcm = AESGCM(kek)
    nonce = secrets.token_bytes(NONCE_LENGTH)
    encrypted_data_key = aesgcm.encrypt(nonce, data_key, None)
    return encrypted_data_key, nonce
