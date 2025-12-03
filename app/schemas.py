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
