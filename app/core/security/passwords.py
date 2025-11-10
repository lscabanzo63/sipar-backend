from passlib.context import CryptContext
import secrets
import string


_pwd = CryptContext(schemes=["argon2"], deprecated="auto")

def hash_password(plain: str) -> str:

    return _pwd.hash(plain)

def verify_password(plain: str, hashed: str) -> bool:
    
    return _pwd.verify(plain, hashed)

def generar_password(length: int = 12) -> str:
   
    chars = string.ascii_letters + string.digits + string.punctuation
    return ''.join(secrets.choice(chars) for _ in range(length))