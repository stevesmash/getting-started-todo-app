from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import get_current_user
from app.schemas import UserPublic
from app.storage import store
from app.transforms.dispatcher import run_transforms

router = APIRouter(prefix="/entities", tags=["transforms"])


@router.post("/{entity_id}/transforms/run")
def run_entity_transforms(entity_id: int, current_user: UserPublic = Depends(get_current_user)):
    try:
        entity = store.get_entity(owner=current_user.username, entity_id=entity_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Entity not found") from exc

    return run_transforms(entity=entity, owner=current_user.username)
