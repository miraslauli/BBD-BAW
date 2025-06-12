from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from src.database.models import get_db
from .schemas import UserCreate, UserLogin, Token, UserProfile, TokenRefresh, PasswordChange
from .dependencies import (
    get_password_hash, create_access_token, create_refresh_token,
    get_user_by_email, create_user, get_current_user, verify_password,
    decode_refresh_token, revoke_refresh_token, get_user_by_id
)

auth_router = APIRouter(
    prefix="/auth",
    tags=["authentication"]
)


@auth_router.post("/register", response_model=Token)
def register_user(
    user: UserCreate,
    db: Session = Depends(get_db)
):
    """Rejestracja nowego użytkownika"""
    # Sprawdzamy czy użytkownik już istnieje
    db_user = get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Użytkownik z tym adresem email już istnieje"
        )
    
    # Tworzymy nowego użytkownika
    db_user = create_user(db=db, email=user.email, password=user.password)
    
    # Tworzymy tokeny
    access_token = create_access_token(data={"sub": str(db_user.id)})
    refresh_token = create_refresh_token(data={"sub": str(db_user.id)})
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer"
    )


@auth_router.post("/login", response_model=Token)
def login_user(
    user_data: UserLogin,
    db: Session = Depends(get_db)
):
    """Logowanie użytkownika"""
    # Sprawdzamy użytkownika
    user = get_user_by_email(db, email=user_data.email)
    if not user or not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nieprawidłowy email lub hasło",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Konto użytkownika jest nieaktywne"
        )
    
    # Tworzymy tokeny
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer"
    )


@auth_router.get("/me", response_model=UserProfile)
def get_current_user_profile(
    current_user: UserProfile = Depends(get_current_user)
):
    """Pobieranie profilu obecnego użytkownika"""
    return current_user


@auth_router.post("/refresh", response_model=Token)
def refresh_access_token(
    token_data: TokenRefresh,
    db: Session = Depends(get_db)
):
    """Odświeżanie access tokena przy użyciu refresh tokena"""
    try:
        payload = decode_refresh_token(token_data.refresh_token)
        user_id = payload.get("sub")
        
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Nieprawidłowy token"
            )
        
        # Sprawdzamy czy użytkownik nadal istnieje
        user = get_user_by_id(db, user_id=int(user_id))
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Użytkownik nie znaleziony"
            )
        
        # Unieważniamy stary refresh token
        revoke_refresh_token(token_data.refresh_token)
        
        # Tworzymy nowe tokeny
        access_token = create_access_token(data={"sub": str(user.id)})
        new_refresh_token = create_refresh_token(data={"sub": str(user.id)})
        
        return Token(
            access_token=access_token,
            refresh_token=new_refresh_token,
            token_type="bearer"
        )
    
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nieprawidłowy token"
        )


@auth_router.post("/logout")
def logout_user(
    token_data: TokenRefresh,
    current_user: UserProfile = Depends(get_current_user)
):
    """Wylogowanie użytkownika (unieważnienie refresh tokena)"""
    revoke_refresh_token(token_data.refresh_token)
    return {"message": "Pomyślnie wylogowano"}


@auth_router.post("/change-password")
def change_password(
    password_data: PasswordChange,
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Zmiana hasła użytkownika"""
    # Pobieramy pełne dane użytkownika z bazy
    user = get_user_by_id(db, user_id=current_user.id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Użytkownik nie znaleziony"
        )
    
    # Sprawdzamy obecne hasło
    if not verify_password(password_data.current_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nieprawidłowe obecne hasło"
        )
    
    # Aktualizujemy hasło
    user.hashed_password = get_password_hash(password_data.new_password)
    db.commit()
    
    return {"message": "Hasło zostało pomyślnie zmienione"}
