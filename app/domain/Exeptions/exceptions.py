from typing import Optional

class DomainError(Exception):
    """Errores de negocio controlados."""
    def __init__(self, status: int, code: str, message: str):
        self.status = status
        self.code = code
        self.message = message
        super().__init__(f"[{status}] {code}: {message}")

    def to_dict(self) -> dict:
        return {"code": self.code, "message": self.message}