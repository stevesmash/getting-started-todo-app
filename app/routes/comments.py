"""Comments management endpoints."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies import get_current_user
from app.schemas import Comment, CommentCreate
from app.storage import store

router = APIRouter(prefix="/comments", tags=["comments"])


@router.post("/", response_model=Comment, status_code=status.HTTP_201_CREATED)
def create_comment(payload: CommentCreate, user: str = Depends(get_current_user)):
    """Create a new comment on an entity owned by the current user."""
    try:
        store.get_entity(owner=user, entity_id=payload.entity_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Entity not found")
    return store.create_comment(owner=user, payload=payload)


@router.get("/entity/{entity_id}", response_model=List[Comment])
def list_comments_for_entity(entity_id: int, user: str = Depends(get_current_user)):
    """List all comments for an entity."""
    return store.list_comments(owner=user, entity_id=entity_id)


@router.delete("/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_comment(comment_id: int, user: str = Depends(get_current_user)):
    """Delete a comment."""
    store.delete_comment(owner=user, comment_id=comment_id)
    return None
