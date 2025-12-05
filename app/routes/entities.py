"""Entity management endpoints."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.dependencies import get_current_user
from app.schemas import Entity, EntityCreate, EntityUpdate, UserPublic
from app.storage import store

router = APIRouter(prefix="/entities", tags=["entities"])


@router.get("/", response_model=list[Entity])
def list_entities(
    case_id: Optional[int] = Query(None, description="Filter entities by case ID"),
    current_user: UserPublic = Depends(get_current_user),
) -> list[Entity]:
    """Return entities for the authenticated user, optionally filtered by case."""

    return store.list_entities(owner=current_user.username, case_id=case_id)


@router.post("/", response_model=Entity, status_code=status.HTTP_201_CREATED)
def create_entity(payload: EntityCreate, current_user: UserPublic = Depends(get_current_user)) -> Entity:
    """Create a new entity within an existing case."""

    try:
        return store.create_entity(owner=current_user.username, payload=payload)
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=exc.args[0] if exc.args else "Case not found",
        ) from exc


@router.get("/{entity_id}", response_model=Entity)
def get_entity(entity_id: int, current_user: UserPublic = Depends(get_current_user)) -> Entity:
    """Retrieve an entity by ID."""

    try:
        return store.get_entity(owner=current_user.username, entity_id=entity_id)
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=exc.args[0] if exc.args else "Entity not found",
        ) from exc


@router.patch("/{entity_id}", response_model=Entity)
def update_entity(
    entity_id: int, payload: EntityUpdate, current_user: UserPublic = Depends(get_current_user)
) -> Entity:
    """Update entity attributes."""

    try:
        return store.update_entity(owner=current_user.username, entity_id=entity_id, payload=payload)
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=exc.args[0] if exc.args else "Entity not found",
        ) from exc


@router.delete("/{entity_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_entity(entity_id: int, current_user: UserPublic = Depends(get_current_user)) -> None:
    """Delete an entity and any connected relationships."""

    try:
        store.delete_entity(owner=current_user.username, entity_id=entity_id)
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=exc.args[0] if exc.args else "Entity not found",
        ) from exc
