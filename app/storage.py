"""PostgreSQL-backed storage layer for GhostLock."""

from __future__ import annotations

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timezone
from threading import Lock
from typing import List, Optional

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

DATABASE_URL = os.environ.get("DATABASE_URL")
_lock = Lock()


class PostgresStore:
    def __init__(self):
        self._init_db()

    def _connect(self):
        return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

    def _init_db(self):
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    username TEXT PRIMARY KEY,
                    password_hash TEXT NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL
                )
                """)

                cur.execute("""
                CREATE TABLE IF NOT EXISTS api_keys (
                    id SERIAL PRIMARY KEY,
                    name TEXT,
                    description TEXT,
                    key TEXT,
                    active BOOLEAN DEFAULT TRUE,
                    owner TEXT NOT NULL
                )
                """)

                cur.execute("""
                CREATE TABLE IF NOT EXISTS cases (
                    id SERIAL PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    owner TEXT NOT NULL
                )
                """)

                cur.execute("""
                CREATE TABLE IF NOT EXISTS entities (
                    id SERIAL PRIMARY KEY,
                    case_id INTEGER NOT NULL REFERENCES cases(id),
                    name TEXT NOT NULL,
                    kind TEXT,
                    description TEXT,
                    owner TEXT NOT NULL
                )
                """)

                cur.execute("""
                CREATE TABLE IF NOT EXISTS relationships (
                    id SERIAL PRIMARY KEY,
                    source_entity_id INTEGER NOT NULL REFERENCES entities(id),
                    target_entity_id INTEGER NOT NULL REFERENCES entities(id),
                    relation TEXT,
                    owner TEXT NOT NULL
                )
                """)

            conn.commit()

    # User management -----------------------------------------------------
    def create_user(self, payload: UserCreate) -> UserPublic:
        with _lock, self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT username FROM users WHERE username = %s",
                    (payload.username,)
                )
                if cur.fetchone():
                    raise ValueError("Username already exists")

                created_at = datetime.now(timezone.utc)
                cur.execute(
                    "INSERT INTO users (username, password_hash, created_at) VALUES (%s, %s, %s)",
                    (payload.username, hash_password(payload.password), created_at)
                )
            conn.commit()
            return UserPublic(username=payload.username, created_at=created_at)

    def authenticate(self, username: str, password: str) -> Optional[UserPublic]:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM users WHERE username = %s", (username,))
                record = cur.fetchone()
                if not record:
                    return None
                if not verify_password(password, record["password_hash"]):
                    return None
                return UserPublic(
                    username=record["username"],
                    created_at=record["created_at"]
                )

    def get_user(self, username: str) -> Optional[UserPublic]:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM users WHERE username = %s", (username,))
                record = cur.fetchone()
                if not record:
                    return None
                return UserPublic(
                    username=record["username"],
                    created_at=record["created_at"]
                )

    # API key management --------------------------------------------------
    def list_api_keys(self, owner: str) -> List[ApiKey]:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM api_keys WHERE owner = %s", (owner,))
                rows = cur.fetchall()
                return [ApiKey(id=r["id"], name=r["name"], description=r["description"],
                              key=r["key"], active=r["active"], owner=r["owner"]) for r in rows]

    def create_api_key(self, owner: str, payload: ApiKeyCreate) -> ApiKey:
        with _lock, self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COALESCE(MAX(id), 0) + 1 as next_id FROM api_keys")
                next_id = cur.fetchone()["next_id"]
                key_value = f"key-{next_id:06d}"
                cur.execute(
                    "INSERT INTO api_keys (name, description, key, active, owner) VALUES (%s, %s, %s, %s, %s) RETURNING id",
                    (payload.name, payload.description, key_value, True, owner)
                )
                new_id = cur.fetchone()["id"]
            conn.commit()
            return ApiKey(
                id=new_id,
                name=payload.name,
                description=payload.description,
                key=key_value,
                active=True,
                owner=owner
            )

    def get_api_key(self, owner: str, key_id: int) -> ApiKey:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM api_keys WHERE id = %s AND owner = %s", (key_id, owner))
                row = cur.fetchone()
                if not row:
                    raise KeyError("API key not found")
                return ApiKey(id=row["id"], name=row["name"], description=row["description"],
                             key=row["key"], active=row["active"], owner=row["owner"])

    def update_api_key(self, owner: str, key_id: int, payload: ApiKeyUpdate) -> ApiKey:
        self.get_api_key(owner, key_id)
        updates = payload.dict(exclude_none=True)
        if updates:
            fields = ", ".join(f"{k}=%s" for k in updates)
            values = list(updates.values()) + [key_id, owner]
            with _lock, self._connect() as conn:
                with conn.cursor() as cur:
                    cur.execute(f"UPDATE api_keys SET {fields} WHERE id=%s AND owner=%s", values)
                conn.commit()
        return self.get_api_key(owner, key_id)

    def delete_api_key(self, owner: str, key_id: int) -> None:
        self.get_api_key(owner, key_id)
        with _lock, self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM api_keys WHERE id = %s AND owner = %s", (key_id, owner))
            conn.commit()

    # Case management ----------------------------------------------------
    def list_cases(self, owner: str) -> List[Case]:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM cases WHERE owner = %s", (owner,))
                rows = cur.fetchall()
                return [Case(id=r["id"], name=r["name"], description=r["description"], owner=r["owner"]) for r in rows]

    def create_case(self, owner: str, payload: CaseCreate) -> Case:
        with _lock, self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO cases (name, description, owner) VALUES (%s, %s, %s) RETURNING id",
                    (payload.name, payload.description, owner)
                )
                new_id = cur.fetchone()["id"]
            conn.commit()
            return Case(id=new_id, name=payload.name, description=payload.description, owner=owner)

    def get_case(self, owner: str, case_id: int) -> Case:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM cases WHERE id = %s AND owner = %s", (case_id, owner))
                row = cur.fetchone()
                if not row:
                    raise KeyError("Case not found")
                return Case(id=row["id"], name=row["name"], description=row["description"], owner=row["owner"])

    def update_case(self, owner: str, case_id: int, payload: CaseUpdate) -> Case:
        self.get_case(owner, case_id)
        updates = payload.dict(exclude_none=True)
        if updates:
            fields = ", ".join(f"{k}=%s" for k in updates)
            values = list(updates.values()) + [case_id, owner]
            with _lock, self._connect() as conn:
                with conn.cursor() as cur:
                    cur.execute(f"UPDATE cases SET {fields} WHERE id=%s AND owner=%s", values)
                conn.commit()
        return self.get_case(owner, case_id)

    def delete_case(self, owner: str, case_id: int) -> None:
        self.get_case(owner, case_id)
        entity_ids = [e.id for e in self.list_entities(owner, case_id)]
        for entity_id in entity_ids:
            self.delete_entity(owner, entity_id)
        with _lock, self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM cases WHERE id = %s AND owner = %s", (case_id, owner))
            conn.commit()

    # Entity management --------------------------------------------------
    def list_entities(self, owner: str, case_id: Optional[int] = None) -> List[Entity]:
        with self._connect() as conn:
            with conn.cursor() as cur:
                if case_id is not None:
                    cur.execute("SELECT * FROM entities WHERE owner = %s AND case_id = %s", (owner, case_id))
                else:
                    cur.execute("SELECT * FROM entities WHERE owner = %s", (owner,))
                rows = cur.fetchall()
                return [Entity(id=r["id"], case_id=r["case_id"], name=r["name"],
                              kind=r["kind"], description=r["description"], owner=r["owner"]) for r in rows]

    def create_entity(self, owner: str, payload: EntityCreate) -> Entity:
        self.get_case(owner, payload.case_id)
        with _lock, self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO entities (case_id, name, kind, description, owner) VALUES (%s, %s, %s, %s, %s) RETURNING id",
                    (payload.case_id, payload.name, payload.kind, payload.description, owner)
                )
                new_id = cur.fetchone()["id"]
            conn.commit()
            return Entity(
                id=new_id,
                case_id=payload.case_id,
                name=payload.name,
                kind=payload.kind,
                description=payload.description,
                owner=owner
            )

    def get_entity(self, owner: str, entity_id: int) -> Entity:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM entities WHERE id = %s AND owner = %s", (entity_id, owner))
                row = cur.fetchone()
                if not row:
                    raise KeyError("Entity not found")
                return Entity(id=row["id"], case_id=row["case_id"], name=row["name"],
                             kind=row["kind"], description=row["description"], owner=row["owner"])

    def update_entity(self, owner: str, entity_id: int, payload: EntityUpdate) -> Entity:
        self.get_entity(owner, entity_id)
        updates = payload.dict(exclude_none=True)
        if updates:
            fields = ", ".join(f"{k}=%s" for k in updates)
            values = list(updates.values()) + [entity_id, owner]
            with _lock, self._connect() as conn:
                with conn.cursor() as cur:
                    cur.execute(f"UPDATE entities SET {fields} WHERE id=%s AND owner=%s", values)
                conn.commit()
        return self.get_entity(owner, entity_id)

    def delete_entity(self, owner: str, entity_id: int) -> None:
        entity = self.get_entity(owner, entity_id)
        with _lock, self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM relationships WHERE owner = %s AND (source_entity_id = %s OR target_entity_id = %s)",
                    (owner, entity.id, entity.id)
                )
                cur.execute("DELETE FROM entities WHERE id = %s AND owner = %s", (entity_id, owner))
            conn.commit()

    # Relationship management -------------------------------------------
    def list_relationships(self, owner: str, case_id: Optional[int] = None) -> List[Relationship]:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM relationships WHERE owner = %s", (owner,))
                rows = cur.fetchall()
                relationships = [
                    Relationship(
                        id=r["id"],
                        source_entity_id=r["source_entity_id"],
                        target_entity_id=r["target_entity_id"],
                        relation=r["relation"],
                        owner=r["owner"]
                    ) for r in rows
                ]
                if case_id is not None:
                    entity_ids = {e.id for e in self.list_entities(owner, case_id)}
                    relationships = [
                        rel for rel in relationships
                        if rel.source_entity_id in entity_ids and rel.target_entity_id in entity_ids
                    ]
                return relationships

    def create_relationship(self, owner: str, payload: RelationshipCreate) -> Relationship:
        source = self.get_entity(owner, payload.source_entity_id)
        target = self.get_entity(owner, payload.target_entity_id)
        if source.case_id != target.case_id:
            raise ValueError("Entities must belong to the same case")

        with _lock, self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO relationships (source_entity_id, target_entity_id, relation, owner) VALUES (%s, %s, %s, %s) RETURNING id",
                    (payload.source_entity_id, payload.target_entity_id, payload.relation, owner)
                )
                new_id = cur.fetchone()["id"]
            conn.commit()
            return Relationship(
                id=new_id,
                source_entity_id=payload.source_entity_id,
                target_entity_id=payload.target_entity_id,
                relation=payload.relation,
                owner=owner
            )

    def get_relationship(self, owner: str, relationship_id: int) -> Relationship:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM relationships WHERE id = %s AND owner = %s", (relationship_id, owner))
                row = cur.fetchone()
                if not row:
                    raise KeyError("Relationship not found")
                return Relationship(
                    id=row["id"],
                    source_entity_id=row["source_entity_id"],
                    target_entity_id=row["target_entity_id"],
                    relation=row["relation"],
                    owner=row["owner"]
                )

    def update_relationship(self, owner: str, relationship_id: int, payload: RelationshipUpdate) -> Relationship:
        self.get_relationship(owner, relationship_id)
        updates = payload.dict(exclude_none=True)
        if updates:
            fields = ", ".join(f"{k}=%s" for k in updates)
            values = list(updates.values()) + [relationship_id, owner]
            with _lock, self._connect() as conn:
                with conn.cursor() as cur:
                    cur.execute(f"UPDATE relationships SET {fields} WHERE id=%s AND owner=%s", values)
                conn.commit()
        return self.get_relationship(owner, relationship_id)

    def delete_relationship(self, owner: str, relationship_id: int) -> None:
        self.get_relationship(owner, relationship_id)
        with _lock, self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM relationships WHERE id = %s AND owner = %s", (relationship_id, owner))
            conn.commit()


store = PostgresStore()
