from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator


def _validate_password(value: str) -> str:
    if len(value) < 8 or len(value) > 128:
        raise ValueError("Password must be 8-128 characters long")
    has_letter = any(ch.isalpha() for ch in value)
    has_digit = any(ch.isdigit() for ch in value)
    if not (has_letter and has_digit):
        raise ValueError("Password must include letters and digits")
    return value


def _validate_email(value: str) -> str:
    email = value.strip().lower()
    if "@" not in email:
        raise ValueError("Invalid email address")
    local_part, domain = email.split("@", 1)
    if not local_part or not domain:
        raise ValueError("Invalid email address")
    if domain == "localhost" or domain.endswith(".local") or "." in domain:
        return email
    raise ValueError("Invalid email address")


class UserCreate(BaseModel):
    login: str = Field(min_length=2, max_length=120)
    email: str = Field(min_length=5, max_length=200)
    password: str = Field(min_length=8, max_length=128)
    role: Literal["admin", "driver"]

    _password_validator = field_validator("password")(_validate_password)
    _email_validator = field_validator("email")(_validate_email)


class UserRead(BaseModel):
    id: str
    name: str
    email: str | None
    role: str
    active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class RegisterRequest(BaseModel):
    login: str = Field(min_length=2, max_length=120)
    email: str = Field(min_length=5, max_length=200)
    password: str = Field(min_length=8, max_length=128)

    _password_validator = field_validator("password")(_validate_password)
    _email_validator = field_validator("email")(_validate_email)


class RegisterRead(UserRead):
    api_key: str


class LoginRequest(BaseModel):
    email: str = Field(min_length=5, max_length=200)
    password: str = Field(min_length=8, max_length=128)

    _password_validator = field_validator("password")(_validate_password)
    _email_validator = field_validator("email")(_validate_email)


class LoginRead(UserRead):
    api_key: str


class BootstrapRequest(BaseModel):
    login: str = Field(min_length=2, max_length=120)
    email: str = Field(min_length=5, max_length=200)
    password: str = Field(min_length=8, max_length=128)
    bootstrap_key: str = Field(min_length=4, max_length=128)

    _password_validator = field_validator("password")(_validate_password)
    _email_validator = field_validator("email")(_validate_email)


class AuditLogRead(BaseModel):
    id: str
    actor_user_id: str | None
    actor_role: str | None
    action: str
    path: str
    status_code: int
    details: dict
    created_at: datetime

    model_config = {"from_attributes": True}
