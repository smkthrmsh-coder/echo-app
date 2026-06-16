import secrets
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.core.security import create_access_token, hash_password, verify_password
from app.db.database import get_db
from app.db.models import User

router = APIRouter(prefix="/auth", tags=["auth"])


class SignupRequest(BaseModel):
    email: str
    password: str
    display_name: str | None = None


class LoginRequest(BaseModel):
    email: str
    password: str


class UserOut(BaseModel):
    id: str
    email: str
    display_name: str
    avatar_url: str | None = None


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


def _user_out(u: User) -> UserOut:
    return UserOut(id=u.id, email=u.email, display_name=u.display_name, avatar_url=u.avatar_url)


@router.post("/signup", response_model=AuthResponse)
async def signup(request: SignupRequest, db: Session = Depends(get_db)) -> AuthResponse:
    email = request.email.strip().lower()
    if not email or "@" not in email:
        raise HTTPException(status_code=400, detail="Invalid email")
    if len(request.password) < 4:
        raise HTTPException(status_code=400, detail="Password must be at least 4 characters")
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    display = (request.display_name or "").strip() or email.split("@")[0].replace(".", " ").title()
    user = User(email=email, hashed_password=hash_password(request.password), display_name=display)
    db.add(user)
    db.commit()

    return AuthResponse(access_token=create_access_token(user.id), user=_user_out(user))


@router.post("/login", response_model=AuthResponse)
async def login(request: LoginRequest, db: Session = Depends(get_db)) -> AuthResponse:
    email = request.email.strip().lower()
    user = db.query(User).filter(User.email == email).first()
    if not user or not user.hashed_password or not verify_password(request.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    return AuthResponse(access_token=create_access_token(user.id), user=_user_out(user))


@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)) -> UserOut:
    return _user_out(current_user)


@router.get("/google")
async def google_auth() -> RedirectResponse:
    settings = get_settings()
    if not settings.google_client_id:
        raise HTTPException(status_code=503, detail="Google OAuth not configured — add GOOGLE_CLIENT_ID to env")

    params = urlencode({
        "client_id": settings.google_client_id,
        "redirect_uri": f"{settings.backend_url}/api/auth/google/callback",
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "select_account",
        "state": secrets.token_urlsafe(16),
    })
    return RedirectResponse(url=f"https://accounts.google.com/o/oauth2/v2/auth?{params}")


@router.get("/google/callback")
async def google_callback(
    code: str | None = None,
    error: str | None = None,
    db: Session = Depends(get_db),
) -> RedirectResponse:
    settings = get_settings()
    frontend = settings.frontend_url

    if error or not code:
        return RedirectResponse(url=f"{frontend}?auth_error=cancelled")

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            token_resp = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "code": code,
                    "client_id": settings.google_client_id,
                    "client_secret": settings.google_client_secret,
                    "redirect_uri": f"{settings.backend_url}/api/auth/google/callback",
                    "grant_type": "authorization_code",
                },
            )
            if not token_resp.is_success:
                return RedirectResponse(url=f"{frontend}?auth_error=exchange_failed")

            access_token = token_resp.json().get("access_token", "")
            info_resp = await client.get(
                "https://www.googleapis.com/oauth2/v3/userinfo",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            info = info_resp.json()
    except Exception:
        return RedirectResponse(url=f"{frontend}?auth_error=network_error")

    email = info.get("email", "").lower()
    google_id = info.get("sub", "")
    if not email or not google_id:
        return RedirectResponse(url=f"{frontend}?auth_error=missing_info")

    user = db.query(User).filter((User.email == email) | (User.google_id == google_id)).first()
    if user:
        if not user.google_id:
            user.google_id = google_id
        if not user.avatar_url:
            user.avatar_url = info.get("picture")
    else:
        user = User(
            email=email,
            google_id=google_id,
            display_name=info.get("name", email.split("@")[0].title()),
            avatar_url=info.get("picture"),
        )
        db.add(user)

    db.commit()
    return RedirectResponse(url=f"{frontend}?token={create_access_token(user.id)}")
