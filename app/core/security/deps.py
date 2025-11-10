from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.security.jwt_service import decode_token

security = HTTPBearer()

class CurrentUser:
    def __init__(self, user_id: int, email: str, role: str):
        self.user_id = user_id
        self.email = email
        self.role = role

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> CurrentUser:
    token = credentials.credentials
    try:
        payload = decode_token(token)
        sub = payload.get("sub")
        role = payload.get("role")
        if not sub or not role:
            raise ValueError("Token inválido o incompleto")

        return CurrentUser(
            user_id=payload.get("user_id", 0),
            email=sub,
            role=role
        )
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido o expirado")

def roles_required(*allowed_roles: str):
    def _checker(user: CurrentUser = Depends(get_current_user)):
        if user.role not in allowed_roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No autorizado")
        return user
    return _checker
