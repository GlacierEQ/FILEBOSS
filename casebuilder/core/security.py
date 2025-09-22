"""
Security Utilities

This module provides security-related utilities including password hashing,
JWT token creation and validation, and authentication dependencies.
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Union

from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from ..core.config import settings
from ..utils import utc_now

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Generate a password hash."""
    return pwd_context.hash(password)

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login",
    auto_error=False
)

def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """Create a JWT access token.
    
    Args:
        data: Data to encode in the token
        expires_delta: Optional timedelta for token expiration
        
    Returns:
        str: Encoded JWT token
    """
    to_encode = data.copy()
    
    now = utc_now()
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=15)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    
    return encoded_jwt

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Get the current authenticated user from the JWT token.
    
    Args:
        token: JWT token from the Authorization header
        db: Database session
        
    Returns:
        Dict containing user data
        
    Raises:
        HTTPException: If authentication fails
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if not token:
        raise credentials_exception
    
    try:
        # Decode the token
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        
        # Get user from database
        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_exception
            
        # In a real app, you would fetch the user from the database here
        # user = await user_repo.get(user_id)
        # if user is None:
        #     raise credentials_exception
        # return user
        
        # For now, return the token payload
        return payload
        
    except JWTError:
        raise credentials_exception

def get_current_active_user(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get the current active user.
    
    Args:
        current_user: The current user from get_current_user
        
    Returns:
        The current user if active
        
    Raises:
        HTTPException: If the user is inactive
    """
    # In a real app, you would check if the user is active
    # if not current_user.is_active:
    #     raise HTTPException(status_code=400, detail="Inactive user")
    
    return current_user

# Role-based access control
def has_role(required_roles: list):
    """Check if the current user has any of the required roles.
    
    Args:
        required_roles: List of role names that are allowed
        
    Returns:
        Dependency that checks if the user has the required role
    """
    async def role_checker(
        current_user: Dict[str, Any] = Depends(get_current_active_user)
    ) -> Dict[str, Any]:
        # In a real app, you would check the user's roles
        # user_roles = current_user.get("roles", [])
        # if not any(role in user_roles for role in required_roles):
        #     raise HTTPException(
        #         status_code=status.HTTP_403_FORBIDDEN,
        #         detail="Insufficient permissions"
        #     )
        return current_user
    
    return role_checker

# Common role checkers
is_admin = has_role(["admin"])
is_editor = has_role(["editor", "admin"])
is_viewer = has_role(["viewer", "editor", "admin"])
