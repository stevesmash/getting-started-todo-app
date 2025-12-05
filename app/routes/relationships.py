"""Relationship management endpoints."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.dependencies import get_current_user
from app.schemas import Relationship, RelationshipCreate, RelationshipUpdate, UserPublic
from app.storage import store

router = APIRouter(prefix="/relationships", tags=["relationships"])


@router.get("/", response_model=list[Relationship])
def list_relationships(
    case_id: Optional[int] = Query(None, description="Filter relationships by case ID"),
    current_user: UserPublic = Depends(get_current_user),
) -> list[Relationship]:
    """Return relationships for the authenticated user."""

    return store.list_relationships(owner=current_user.username, case_id=case_id)


@router.post("/", response_model=Relationship, status_code=status.HTTP_201_CREATED)
def create_relationship(
    payload: RelationshipCreate, current_user: UserPublic = Depends(get_current_user)
) -> Relationship:
    """Create a relationship between two entities."""

    try:
        return store.create_relationship(owner=current_user.username, payload=payload)
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=exc.args[0] if exc.args else "Related entity not found",
        ) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/{relationship_id}", response_model=Relationship)
def get_relationship(
    relationship_id: int, current_user: UserPublic = Depends(get_current_user)
) -> Relationship:
    """Retrieve a relationship by ID."""

    try:
        return store.get_relationship(owner=current_user.username, relationship_id=relationship_id)
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=exc.args[0] if exc.args else "Relationship not found",
        ) from exc


@router.patch("/{relationship_id}", response_model=Relationship)
def update_relationship(
    relationship_id: int,
    payload: RelationshipUpdate,
    current_user: UserPublic = Depends(get_current_user),
) -> Relationship:
    """Update relationship metadata."""

    try:
        return store.update_relationship(
            owner=current_user.username, relationship_id=relationship_id, payload=payload
        )
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=exc.args[0] if exc.args else "Relationship not found",
        ) from exc


@router.delete("/{relationship_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_relationship(
    relationship_id: int, current_user: UserPublic = Depends(get_current_user)
) -> None:
    """Delete a relationship by ID."""

    try:
        store.delete_relationship(owner=current_user.username, relationship_id=relationship_id)
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=exc.args[0] if exc.args else "Relationship not found",
        ) from exc
