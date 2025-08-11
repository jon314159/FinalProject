# app/schemas/base.py
from pydantic import BaseModel, EmailStr, Field, ConfigDict, model_validator

class UserBase(BaseModel):
    """Base user schema with common fields."""
    first_name: str = Field(
        ...,
        min_length=1,
        max_length=50,
        examples=["John"],
        description="User's first name"
    )
    last_name: str = Field(
        ...,
        min_length=1,
        max_length=50,
        examples=["Doe"],
        description="User's last name"
    )
    email: EmailStr = Field(
        ...,
        examples=["john.doe@example.com"],
        description="User's email address"
    )
    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        examples=["johndoe"],
        description="User's unique username"
    )

    model_config = ConfigDict(from_attributes=True)

class PasswordMixin(BaseModel):
    password: str = Field(
        ...,
        min_length=8,
        examples=["SecurePass123!"],
        description="Password"
    )

    @model_validator(mode="after")
    def validate_password(self) -> "PasswordMixin":
        if not any(char.isupper() for char in self.password):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(char.islower() for char in self.password):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(char.isdigit() for char in self.password):
            raise ValueError("Password must contain at least one digit")
        # No special character requirement so "SecurePass123" is valid.
        return self

    model_config = ConfigDict(from_attributes=True)

class UserCreate(UserBase, PasswordMixin):
    """
    Schema used when creating a new user.
    Inherits common user fields from UserBase and adds a password field.
    """
    pass

class UserLogin(BaseModel):
    """
    Schema for user login credentials.
    Contains the username and password.
    """
    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        examples=["johndoe"]
    )
    password: str = Field(
        ...,
        min_length=8,
        examples=["supersecretpassword"]
    )
