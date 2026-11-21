from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.user import UserLogin, Token
from app.schemas.base import UserCreate
from app.schemas.user import UserResponse

router = APIRouter(prefix="/users", tags=["Users"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
):
    try:
        user = User.register(db, payload.model_dump())
        db.commit()
        db.refresh(user)
        return user

    except ValueError as exc:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc

    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Username or email already exists",
        ) from exc


@router.post(
    "/login",
    response_model=Token,
    status_code=status.HTTP_200_OK,
)
def login_user(
    payload: UserLogin,
    db: Session = Depends(get_db),
):
    user_data = User.authenticate(
        db,
        payload.username,
        payload.password,
    )

    if user_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username/email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user_data
