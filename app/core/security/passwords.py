from passlib.context import CryptContext
from passlib.exc import UnknownHashError

_pwd = CryptContext(
    schemes=["argon2"],
    deprecated="auto",
)

def hash_password(plain: str) -> str:

    return _pwd.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return _pwd.verify(plain, hashed)
    except UnknownHashError:
        # Caso legacy: en BD está guardado en texto plano (Adm!n#2025, Gestor123, etc.)
        return plain == hashed
