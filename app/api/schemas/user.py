from pydantic import BaseModel, EmailStr, Field
from app.core.utils import get_settings


class UserRegistration(BaseModel):
    """Schema for user registration."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=100)


class UserActivation(BaseModel):
    """Schema for user activation."""

    code: str = Field(min_length=get_settings().activation_code_length, max_length=get_settings().activation_code_length, pattern=r"^\d{4}$")
