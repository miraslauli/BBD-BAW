from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class UserCreate(BaseModel):
    """Schemat tworzenia użytkownika"""

    email: EmailStr
    password: str = Field(
        ..., min_length=6, description="Hasło musi mieć co najmniej 6 znaków"
    )
    full_name: Optional[str] = None
    is_admin: Optional[bool] = None  # Bez wartości domyślnej

    class Config:
        # Zapewnia, że wartości z JSON są poprawnie przypisywane
        validate_assignment = True


class AdminCreate(BaseModel):
    """Schemat tworzenia administratora"""

    email: EmailStr
    password: str = Field(
        ..., min_length=6, description="Hasło musi mieć co najmniej 6 znaków"
    )
    full_name: Optional[str] = None
    is_admin: bool = True  # Zawsze True dla administratorów

    class Config:
        validate_assignment = True


class UserLogin(BaseModel):
    """Schemat logowania użytkownika"""

    email: EmailStr
    password: str


class UserProfile(BaseModel):
    """Schemat profilu użytkownika"""

    id: int
    email: str
    is_active: bool
    is_admin: bool

    class Config:
        from_attributes = True


class Token(BaseModel):
    """Schemat odpowiedzi tokena"""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenRefresh(BaseModel):
    """Schemat odświeżania tokena"""

    refresh_token: str


class PasswordChange(BaseModel):
    """Schemat zmiany hasła"""

    current_password: str
    new_password: str = Field(
        ..., min_length=6, description="Nowe hasło musi mieć co najmniej 6 znaków"
    )


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str


class TokenPayload(BaseModel):
    sub: Optional[str] = None  # user identifier
    exp: Optional[int] = None  # expiration timestamp
