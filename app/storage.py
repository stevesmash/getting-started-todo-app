"""Simple in-memory storage layer for demo purposes."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List, Optional

from app.schemas import ApiKey, ApiKeyCreate, ApiKeyUpdate, UserCreate, UserPublic
from app.security import hash_password, verify_password


class InMemoryStore:
    def __init__(self) -> None:
        self._users: Dict[str, dict] = {}
        self._api_keys: Dict[int, ApiKey] = {}
        self._api_key_counter = 0

    # User management -----------------------------------------------------
    def create_user(self, payload: UserCreate) -> UserPublic:
        if payload.username in self._users:
            raise ValueError("Username already exists")

        user_record = {
            "username": payload.username,
            "hashed_password": hash_password(payload.password),
            "created_at": datetime.now(timezone.utc),
        }
        self._users[payload.username] = user_record
        return UserPublic(**{k: v for k, v in user_record.items() if k != "hashed_password"})

    def authenticate(self, username: str, password: str) -> Optional[UserPublic]:
        record = self._users.get(username)
        if not record:
            return None
        if not verify_password(password, record["hashed_password"]):
            return None
        return UserPublic(**{k: v for k, v in record.items() if k != "hashed_password"})

    def get_user(self, username: str) -> Optional[UserPublic]:
        record = self._users.get(username)
        if not record:
            return None
        return UserPublic(**{k: v for k, v in record.items() if k != "hashed_password"})

    # API key management --------------------------------------------------
    def list_api_keys(self, owner: str) -> List[ApiKey]:
        return [key for key in self._api_keys.values() if key.owner == owner]

    def create_api_key(self, owner: str, payload: ApiKeyCreate) -> ApiKey:
        self._api_key_counter += 1
        new_key = ApiKey(
            id=self._api_key_counter,
            key=f"key-{self._api_key_counter:06d}",
            active=True,
            owner=owner,
            **payload.dict(),
        )
        self._api_keys[new_key.id] = new_key
        return new_key

    def get_api_key(self, owner: str, key_id: int) -> ApiKey:
        key = self._api_keys.get(key_id)
        if not key or key.owner != owner:
            raise KeyError("API key not found")
        return key

    def update_api_key(self, owner: str, key_id: int, payload: ApiKeyUpdate) -> ApiKey:
        key = self.get_api_key(owner, key_id)
        updated = key.copy(update=payload.dict(exclude_none=True))
        self._api_keys[key_id] = updated
        return updated

    def delete_api_key(self, owner: str, key_id: int) -> None:
        self.get_api_key(owner, key_id)
        del self._api_keys[key_id]


store = InMemoryStore()
