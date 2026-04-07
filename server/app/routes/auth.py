"""Authentication routes"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.models import get_db
from app.schemas import UserCreate, LoginRequest, Token, UserResponse
from app.services.auth import (
    create_user, 
    authenticate_user, 
    create_access_token,
    user_to_response
)
from app.errors import UnauthorizedError, ForbiddenError

router = APIRouter()


@router.post("/register", response_model=UserResponse)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    user = await create_user(db, user_data)
    return user_to_response(user)


@router.post("/login", response_model=Token)
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    """Login and get access token"""
    user = await authenticate_user(db, request.username, request.password)
    if not user:
        raise UnauthorizedError("Invalid username or password")
    
    # Create token
    token = create_access_token({"sub": user.username, "user_id": user.id, "role": user.role})
    
    return Token(access_token=token)


@router.get("/me", response_model=UserResponse)
async def get_me(db: Session = Depends(get_db), token: str = Depends(lambda: None)):
    """Get current user info (requires auth)"""
    # Simplified - in production use proper JWT middleware
    if not token:
        raise UnauthorizedError()
    
    from fastapi import Header
    async def get_current_user(authorization: str = Header(None)):
        if not authorization or not authorization.startswith("Bearer "):
            raise UnauthorizedError()
        
        from app.services.auth import decode_access_token
        payload = decode_access_token(authorization.replace("Bearer ", ""))
        if not payload:
            raise UnauthorizedError()
        
        from app.models import User
        user = db.query(User).filter(User.username == payload.get("sub")).first()
        if not user or not user.is_active:
            raise ForbiddenError("User not found or inactive")
        
        return user
    
    user = await get_current_user(authorization=token)
    return user_to_response(user)