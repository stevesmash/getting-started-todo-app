"""API key management endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies import get_current_user
from app.schemas import ApiKey, ApiKeyCreate, ApiKeyUpdate, UserPublic
from app.storage import store

router = APIRouter(prefix="/apikeys", tags=["apikeys"])


@router.get("/", response_model=list[ApiKey])
def list_api_keys(current_user: UserPublic = Depends(get_current_user)) -> list[ApiKey]:
    """Return API keys owned by the current user."""

    return store.list_api_keys(owner=current_user.username)


@router.post("/", response_model=ApiKey, status_code=status.HTTP_201_CREATED)
def create_api_key(
    payload: ApiKeyCreate, current_user: UserPublic = Depends(get_current_user)
) -> ApiKey:
    """Create a new API key for the authenticated user."""

    return store.create_api_key(owner=current_user.username, payload=payload)


@router.get("/{key_id}", response_model=ApiKey)
def get_api_key(key_id: int, current_user: UserPublic = Depends(get_current_user)) -> ApiKey:
    """Retrieve a single API key by ID."""

    try:
        return store.get_api_key(owner=current_user.username, key_id=key_id)
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=exc.args[0] if exc.args else "API key not found",
        ) from exc


@router.patch("/{key_id}", response_model=ApiKey)
def update_api_key(
    key_id: int, payload: ApiKeyUpdate, current_user: UserPublic = Depends(get_current_user)
) -> ApiKey:
    """Update mutable fields on an API key."""

    try:
        return store.update_api_key(owner=current_user.username, key_id=key_id, payload=payload)
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=exc.args[0] if exc.args else "API key not found",
        ) from exc


@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_api_key(key_id: int, current_user: UserPublic = Depends(get_current_user)) -> None:
    """Delete an API key owned by the authenticated user."""

    try:
        store.delete_api_key(owner=current_user.username, key_id=key_id)
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=exc.args[0] if exc.args else "API key not found",
        ) from exc
