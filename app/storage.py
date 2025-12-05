"""Simple in-memory storage layer for demo purposes."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List, Optional

from app.schemas import (
    ApiKey,
    ApiKeyCreate,
    ApiKeyUpdate,
    Case,
    CaseCreate,
    CaseUpdate,
    Entity,
    EntityCreate,
    EntityUpdate,
    Relationship,
    RelationshipCreate,
    RelationshipUpdate,
    UserCreate,
    UserPublic,
)
from app.security import hash_password, verify_password


class InMemoryStore:
    def __init__(self) -> None:
        self._users: Dict[str, dict] = {}
        self._api_keys: Dict[int, ApiKey] = {}
        self._api_key_counter = 0
        self._cases: Dict[int, Case] = {}
        self._case_counter = 0
        self._entities: Dict[int, Entity] = {}
        self._entity_counter = 0
        self._relationships: Dict[int, Relationship] = {}
        self._relationship_counter = 0

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

    # Case management ----------------------------------------------------
    def list_cases(self, owner: str) -> List[Case]:
        return [case for case in self._cases.values() if case.owner == owner]

    def create_case(self, owner: str, payload: CaseCreate) -> Case:
        self._case_counter += 1
        case = Case(id=self._case_counter, owner=owner, **payload.dict())
        self._cases[case.id] = case
        return case

    def get_case(self, owner: str, case_id: int) -> Case:
        case = self._cases.get(case_id)
        if not case or case.owner != owner:
            raise KeyError("Case not found")
        return case

    def update_case(self, owner: str, case_id: int, payload: CaseUpdate) -> Case:
        case = self.get_case(owner, case_id)
        updated = case.copy(update=payload.dict(exclude_none=True))
        self._cases[case_id] = updated
        return updated

    def delete_case(self, owner: str, case_id: int) -> None:
        # Ensure the case exists and belongs to the owner
        self.get_case(owner, case_id)

        # Remove dependent entities and relationships
        entity_ids = [eid for eid, ent in self._entities.items() if ent.case_id == case_id and ent.owner == owner]
        for entity_id in entity_ids:
            self.delete_entity(owner, entity_id)

        del self._cases[case_id]

    # Entity management --------------------------------------------------
    def list_entities(self, owner: str, case_id: Optional[int] = None) -> List[Entity]:
        entities = [entity for entity in self._entities.values() if entity.owner == owner]
        if case_id is not None:
            entities = [entity for entity in entities if entity.case_id == case_id]
        return entities

    def create_entity(self, owner: str, payload: EntityCreate) -> Entity:
        # Ensure the case exists and belongs to the owner
        self.get_case(owner, payload.case_id)

        self._entity_counter += 1
        entity = Entity(id=self._entity_counter, owner=owner, **payload.dict())
        self._entities[entity.id] = entity
        return entity

    def get_entity(self, owner: str, entity_id: int) -> Entity:
        entity = self._entities.get(entity_id)
        if not entity or entity.owner != owner:
            raise KeyError("Entity not found")
        return entity

    def update_entity(self, owner: str, entity_id: int, payload: EntityUpdate) -> Entity:
        entity = self.get_entity(owner, entity_id)
        updated = entity.copy(update=payload.dict(exclude_none=True))
        self._entities[entity_id] = updated
        return updated

    def delete_entity(self, owner: str, entity_id: int) -> None:
        # Ensure ownership
        entity = self.get_entity(owner, entity_id)

        # Remove relationships connected to this entity
        relationship_ids = [rid for rid, rel in self._relationships.items() if rel.owner == owner and (rel.source_entity_id == entity.id or rel.target_entity_id == entity.id)]
        for rel_id in relationship_ids:
            del self._relationships[rel_id]

        del self._entities[entity_id]

    # Relationship management -------------------------------------------
    def list_relationships(self, owner: str, case_id: Optional[int] = None) -> List[Relationship]:
        relationships = [rel for rel in self._relationships.values() if rel.owner == owner]
        if case_id is not None:
            relationships = [
                rel
                for rel in relationships
                if (
                    (source := self._entities.get(rel.source_entity_id))
                    and (target := self._entities.get(rel.target_entity_id))
                    and source.case_id == case_id
                    and target.case_id == case_id
                )
            ]
        return relationships

    def create_relationship(self, owner: str, payload: RelationshipCreate) -> Relationship:
        source = self.get_entity(owner, payload.source_entity_id)
        target = self.get_entity(owner, payload.target_entity_id)

        if source.case_id != target.case_id:
            raise ValueError("Entities must belong to the same case")

        self._relationship_counter += 1
        relationship = Relationship(id=self._relationship_counter, owner=owner, **payload.dict())
        self._relationships[relationship.id] = relationship
        return relationship

    def get_relationship(self, owner: str, relationship_id: int) -> Relationship:
        relationship = self._relationships.get(relationship_id)
        if not relationship or relationship.owner != owner:
            raise KeyError("Relationship not found")
        return relationship

    def update_relationship(self, owner: str, relationship_id: int, payload: RelationshipUpdate) -> Relationship:
        relationship = self.get_relationship(owner, relationship_id)
        updated = relationship.copy(update=payload.dict(exclude_none=True))
        self._relationships[relationship_id] = updated
        return updated

    def delete_relationship(self, owner: str, relationship_id: int) -> None:
        self.get_relationship(owner, relationship_id)
        del self._relationships[relationship_id]


store = InMemoryStore()
