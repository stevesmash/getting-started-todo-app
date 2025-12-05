"""Pydantic schemas shared across the application."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    message: str


class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)


class UserCreate(UserBase):
    password: str = Field(..., min_length=6, max_length=128)


class UserPublic(UserBase):
    created_at: datetime

    class Config:
        orm_mode = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    username: str
    password: str


class ApiKeyBase(BaseModel):
    name: str = Field(..., min_length=3, max_length=100)
    description: Optional[str] = None


class ApiKeyCreate(ApiKeyBase):
    pass


class ApiKey(ApiKeyBase):
    id: int
    key: str
    active: bool
    owner: str


class ApiKeyUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=3, max_length=100)
    description: Optional[str] = None
    active: Optional[bool] = None


class CaseBase(BaseModel):
    name: str = Field(..., min_length=3, max_length=150)
    description: Optional[str] = None


class CaseCreate(CaseBase):
    pass


class Case(CaseBase):
    id: int
    owner: str


class CaseUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=3, max_length=150)
    description: Optional[str] = None


class EntityBase(BaseModel):
    case_id: int
    name: str = Field(..., min_length=1, max_length=150)
    kind: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None


class EntityCreate(EntityBase):
    pass


class Entity(EntityBase):
    id: int
    owner: str


class EntityUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=150)
    kind: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None


class RelationshipBase(BaseModel):
    source_entity_id: int
    target_entity_id: int
    relation: str = Field(..., min_length=1, max_length=100)


class RelationshipCreate(RelationshipBase):
    pass


class Relationship(RelationshipBase):
    id: int
    owner: str


class RelationshipUpdate(BaseModel):
    relation: Optional[str] = Field(None, min_length=1, max_length=100)
