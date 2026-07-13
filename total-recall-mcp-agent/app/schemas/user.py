"""
User Pydantic Schemas
"""

from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr


class UserBase(BaseModel):
    """
    Common user fields.
    """

    email: EmailStr
    first_name: str
    last_name: str


class UserCreate(UserBase):
    """
    Payload for creating a user.
    """

    cognito_sub: str | None = None


class UserUpdate(BaseModel):
    """
    Payload for updating a user.
    """

    first_name: str | None = None
    last_name: str | None = None
    is_active: bool | None = None


class UserRead(UserBase):
    """
    User returned from the repository/service.
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    is_active: bool
    cognito_sub: str | None
