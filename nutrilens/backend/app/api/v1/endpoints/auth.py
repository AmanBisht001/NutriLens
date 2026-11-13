import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db
from app.core.security import create_access_token, get_password_hash, verify_password
from app.models.user import User, UserProfile
from app.schemas.user import (
    MessageResponse,
    TokenResponse,
    UserLogin,
    UserRegister,
    UserResponse,
    UserUpdate,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
)
def register_user(
    user_in: UserRegister,
    db: Session = Depends(get_db),
) -> TokenResponse:
    """Register a new user account with dietary profile and return JWT token."""
    normalized_email = user_in.email.lower().strip()

    # Check for existing user
    existing_user = db.query(User).filter(User.email == normalized_email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists.",
        )

    # Hash the password securely with bcrypt
    hashed_password = get_password_hash(user_in.password)

    # Create User model instance
    db_user = User(
        email=normalized_email,
        hashed_password=hashed_password,
        full_name=user_in.full_name.strip(),
        age=user_in.age,
        is_active=True,
    )

    # Create associated dietary profile
    db_profile = UserProfile(
        dietary_preference=user_in.dietary_preference or "None",
        allergies=user_in.allergies or [],
        dietary_restrictions=user_in.dietary_restrictions or [],
        nutrition_goals=user_in.nutrition_goals or [],
    )
    db_user.profile = db_profile

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    # Generate JWT access token
    access_token = create_access_token(subject=db_user.id)

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=db_user,
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Authenticate user and obtain JWT access token",
)
def login_user(
    credentials: UserLogin,
    db: Session = Depends(get_db),
) -> TokenResponse:
    """Authenticate with email and password, returning JWT access token."""
    normalized_email = credentials.email.lower().strip()
    user = db.query(User).filter(User.email == normalized_email).first()

    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This account has been deactivated.",
        )

    access_token = create_access_token(subject=user.id)

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=user,
    )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current authenticated user profile",
)
def get_current_user_profile(
    current_user: User = Depends(get_current_active_user),
) -> UserResponse:
    """Retrieve the current logged-in user's profile and dietary settings."""
    return current_user


@router.put(
    "/profile",
    response_model=UserResponse,
    summary="Update user details and dietary profile",
)
@router.put(
    "/me",
    response_model=UserResponse,
    include_in_schema=False,
)
def update_user_profile(
    update_data: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> UserResponse:
    """Update personal info, dietary preference, allergies, restrictions, and goals."""
    if update_data.full_name is not None:
        current_user.full_name = update_data.full_name.strip()
    if update_data.age is not None:
        current_user.age = update_data.age

    # Ensure profile object exists
    if current_user.profile is None:
        current_user.profile = UserProfile(user_id=current_user.id)
        db.add(current_user.profile)

    if update_data.dietary_preference is not None:
        current_user.profile.dietary_preference = update_data.dietary_preference
    if update_data.allergies is not None:
        current_user.profile.allergies = update_data.allergies
    if update_data.dietary_restrictions is not None:
        current_user.profile.dietary_restrictions = update_data.dietary_restrictions
    if update_data.nutrition_goals is not None:
        current_user.profile.nutrition_goals = update_data.nutrition_goals

    db.commit()
    db.refresh(current_user)
    return current_user


@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="Logout user session",
)
def logout_user() -> MessageResponse:
    """Client handles clearing the stored JWT access token; endpoint confirms session termination."""
    return MessageResponse(message="Successfully logged out.")
