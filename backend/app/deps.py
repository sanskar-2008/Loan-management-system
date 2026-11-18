from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import InvalidTokenError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.admin import Admin
from app.utils.security import decode_access_token

security = HTTPBearer(auto_error=False)


def get_current_admin(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: Session = Depends(get_db),
) -> Admin:
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    try:
        payload = decode_access_token(credentials.credentials)
        admin_id = payload.get("sub")
        is_demo = payload.get("role") == "demo"
    except InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    if not admin_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
    admin = db.get(Admin, admin_id)
    if not admin or not admin.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Admin not found or inactive")
    if is_demo and admin.username != "demo-viewer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid demo identity")
    db.info["demo_mode"] = is_demo
    admin.is_demo = is_demo
    return admin


def require_admin_write(admin: Admin = Depends(get_current_admin)) -> Admin:
    if getattr(admin, "is_demo", False):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Demo account is read-only")
    return admin
