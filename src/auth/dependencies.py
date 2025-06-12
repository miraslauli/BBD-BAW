from datetime import datetime, timedelta
from typing import Optional, Generator, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
import os

# Import z nowego modułu database
from src.database.models import User, get_db

# Ustawienia JWT
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Ustawienia haseł
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Schemat OAuth2
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# Magazyn unieważnionych tokenów (w prawdziwej aplikacji lepiej użyć Redis)
revoked_tokens: set = set()

# get_db importowane z database.models


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Weryfikacja hasła"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hashowanie hasła"""
    return pwd_context.hash(password)


def create_access_token(
    data: Dict[str, Any], expires_delta: Optional[timedelta] = None
) -> str:
    """Tworzenie access tokena"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(
    data: Dict[str, Any], expires_delta: Optional[timedelta] = None
) -> str:
    """Tworzenie refresh tokena"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_refresh_token(token: str) -> Dict[str, Any]:
    """Dekodowanie refresh tokena"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Nieprawidłowy typ tokena",
            )
        if token in revoked_tokens:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token został unieważniony",
            )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nie można zweryfikować danych uwierzytelniających",
        )


def revoke_refresh_token(token: str) -> None:
    """Unieważnienie refresh tokena"""
    revoked_tokens.add(token)


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Pobieranie użytkownika po email"""
    return db.query(User).filter(User.email == email).first()


def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    """Pobieranie użytkownika po ID"""
    return db.query(User).filter(User.id == user_id).first()


def create_user(
    db: Session,
    email: str,
    password: str,
    is_admin: bool = False,
    full_name: str = None,
) -> User:
    """Tworzenie nowego użytkownika"""
    hashed_password = get_password_hash(password)

    # Jawnie ustawiamy is_admin
    admin_status = bool(is_admin) if is_admin is not None else False

    db_user = User(
        email=email,
        hashed_password=hashed_password,
        full_name=full_name,
        is_active=True,
        is_admin=admin_status,
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
):
    """Pobieranie obecnego użytkownika z tokena"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Nie można zweryfikować danych uwierzytelniających",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = get_user_by_id(db, user_id=int(user_id))
    if user is None:
        raise credentials_exception

    # Zwracamy obiekt w formacie schematu UserProfile
    from .schemas import UserProfile

    return UserProfile(
        id=user.id, email=user.email, is_active=user.is_active, is_admin=user.is_admin
    )


def get_current_active_user(current_user=Depends(get_current_user)):
    """Pobieranie aktywnego użytkownika"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Nieaktywny użytkownik")
    return current_user


def get_current_admin_user(current_user=Depends(get_current_user)):
    """Pobieranie użytkownika z prawami administratora"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Niewystarczające uprawnienia"
        )
    return current_user
