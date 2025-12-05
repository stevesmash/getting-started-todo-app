"""Case management endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies import get_current_user
from app.schemas import Case, CaseCreate, CaseUpdate, UserPublic
from app.storage import store

router = APIRouter(prefix="/cases", tags=["cases"])


@router.get("/", response_model=list[Case])
def list_cases(current_user: UserPublic = Depends(get_current_user)) -> list[Case]:
    """Return cases created by the authenticated user."""

    return store.list_cases(owner=current_user.username)


@router.post("/", response_model=Case, status_code=status.HTTP_201_CREATED)
def create_case(payload: CaseCreate, current_user: UserPublic = Depends(get_current_user)) -> Case:
    """Create a new case owned by the current user."""

    return store.create_case(owner=current_user.username, payload=payload)


@router.get("/{case_id}", response_model=Case)
def get_case(case_id: int, current_user: UserPublic = Depends(get_current_user)) -> Case:
    """Retrieve a case by ID."""

    try:
        return store.get_case(owner=current_user.username, case_id=case_id)
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=exc.args[0] if exc.args else "Case not found",
        ) from exc


@router.patch("/{case_id}", response_model=Case)
def update_case(
    case_id: int, payload: CaseUpdate, current_user: UserPublic = Depends(get_current_user)
) -> Case:
    """Update a case's details."""

    try:
        return store.update_case(owner=current_user.username, case_id=case_id, payload=payload)
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=exc.args[0] if exc.args else "Case not found",
        ) from exc


@router.delete("/{case_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_case(case_id: int, current_user: UserPublic = Depends(get_current_user)) -> None:
    """Delete a case and its related entities/relationships."""

    try:
        store.delete_case(owner=current_user.username, case_id=case_id)
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=exc.args[0] if exc.args else "Case not found",
        ) from exc
