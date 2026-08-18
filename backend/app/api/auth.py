from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_admin
from app.models.admin import Admin
from app.schemas import AdminOut, ChangePasswordRequest, LoginRequest, TokenResponse
from app.services.activity_service import log_activity
from app.utils.security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    admin = db.scalar(
        select(Admin).where(
            or_(Admin.username == body.username, Admin.email == body.username)
        )
    )
    if not admin or not verify_password(body.password, admin.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not admin.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Admin inactive")
    admin.last_login_at = datetime.utcnow()
    log_activity(db, admin_id=admin.id, action="auth.login", summary=f"Admin {admin.username} logged in")
    db.commit()
    token = create_access_token(admin.id, {"username": admin.username})
    return TokenResponse(access_token=token)


@router.get("/me", response_model=AdminOut)
def me(admin: Admin = Depends(get_current_admin)):
    return admin


@router.put("/change-password")
def change_password(
    body: ChangePasswordRequest,
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
):
    if body.new_password != body.confirm_password:
        raise HTTPException(status_code=400, detail="New password and confirmation do not match")
    if not verify_password(body.current_password, admin.password_hash):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    if body.new_password == body.current_password:
        raise HTTPException(status_code=400, detail="New password must be different")
    admin.password_hash = hash_password(body.new_password)
    db.commit()
    return {"detail": "Password updated"}


@router.post("/logout")
def logout(admin: Admin = Depends(get_current_admin)):
    return {"detail": "Logged out"}
