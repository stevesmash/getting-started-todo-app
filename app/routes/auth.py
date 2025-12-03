"""Authentication and user management endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies import get_current_user
from app.schemas import LoginRequest, Token, UserCreate, UserPublic
from app.security import create_access_token
from app.storage import store
from app.config import get_settings

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
def register_user(payload: UserCreate) -> UserPublic:
    """Register a new user with a hashed password."""

    try:
        return store.create_user(payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/login", response_model=Token)
def login(credentials: LoginRequest) -> Token:
    """Authenticate a user and return a signed access token."""

    user = store.authenticate(credentials.username, credentials.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    settings = get_settings()
    token = create_access_token(
        data={"sub": user.username},
        expires_minutes=settings.access_token_expiry_minutes,
    )
    return Token(access_token=token)


@router.get("/me", response_model=UserPublic)
def get_me(current_user: UserPublic = Depends(get_current_user)) -> UserPublic:
    """Return the authenticated user's profile."""

    return current_user
