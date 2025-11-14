"""
Authentication service for user management and JWT token handling.

This module provides user registration, login, and JWT token management
using MongoDB for user storage and bcrypt for password hashing.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Dict
from jose import JWTError, jwt
from passlib.context import CryptContext
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError

logger = logging.getLogger(__name__)


class AuthService:
    """
    Handles user authentication, registration, and JWT token management.
    """
    
    def __init__(
        self,
        connection_string: str = "mongodb://localhost:27017/",
        database_name: str = "financial_chatbot",
        secret_key: str = "your-secret-key-change-in-production",
        algorithm: str = "HS256",
        access_token_expire_minutes: int = 30
    ):
        """
        Initialize the AuthService.
        
        Args:
            connection_string: MongoDB connection string
            database_name: Name of the database to use
            secret_key: Secret key for JWT encoding/decoding
            algorithm: JWT algorithm (default: HS256)
            access_token_expire_minutes: Token expiration time in minutes
        """
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.access_token_expire_minutes = access_token_expire_minutes
        
        # Password hashing context
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
        try:
            # Initialize MongoDB client
            self.client = MongoClient(connection_string, serverSelectionTimeoutMS=5000)
            self.client.admin.command('ping')
            
            # Get database and collection
            self.db = self.client[database_name]
            self.users_collection = self.db['users']
            
            # Create unique index on username and email
            self.users_collection.create_index("username", unique=True)
            self.users_collection.create_index("email", unique=True)
            
            logger.info("AuthService initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing AuthService: {e}")
            raise
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verify a password against its hash.
        
        Args:
            plain_password: Plain text password
            hashed_password: Hashed password from database
            
        Returns:
            bool: True if password matches, False otherwise
        """
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """
        Hash a password.
        
        Args:
            password: Plain text password
            
        Returns:
            str: Hashed password
        """
        return self.pwd_context.hash(password)
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """
        Create a JWT access token.
        
        Args:
            data: Data to encode in the token
            expires_delta: Optional custom expiration time
            
        Returns:
            str: Encoded JWT token
        """
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        
        return encoded_jwt
    
    def decode_token(self, token: str) -> Optional[Dict]:
        """
        Decode and verify a JWT token.
        
        Args:
            token: JWT token string
            
        Returns:
            Optional[Dict]: Decoded token payload or None if invalid
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except JWTError as e:
            logger.warning(f"Invalid token: {e}")
            return None
    
    def register_user(
        self,
        username: str,
        email: str,
        password: str,
        full_name: Optional[str] = None
    ) -> Dict:
        """
        Register a new user.
        
        Args:
            username: Unique username
            email: Unique email address
            password: Plain text password (will be hashed)
            full_name: Optional full name
            
        Returns:
            Dict: User information (without password)
            
        Raises:
            ValueError: If username or email already exists
        """
        try:
            # Hash the password
            hashed_password = self.get_password_hash(password)
            
            # Create user document
            user_doc = {
                "username": username,
                "email": email,
                "hashed_password": hashed_password,
                "full_name": full_name,
                "is_active": True,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            # Insert user
            result = self.users_collection.insert_one(user_doc)
            
            logger.info(f"User registered successfully: {username}")
            
            # Return user info without password
            return {
                "user_id": str(result.inserted_id),
                "username": username,
                "email": email,
                "full_name": full_name,
                "is_active": True,
                "created_at": user_doc["created_at"].isoformat()
            }
            
        except DuplicateKeyError as e:
            # Check which field caused the duplicate
            if "username" in str(e):
                raise ValueError("Username already exists")
            elif "email" in str(e):
                raise ValueError("Email already exists")
            else:
                raise ValueError("User already exists")
        except Exception as e:
            logger.error(f"Error registering user: {e}")
            raise
    
    def authenticate_user(self, username: str, password: str) -> Optional[Dict]:
        """
        Authenticate a user with username and password.
        
        Args:
            username: Username
            password: Plain text password
            
        Returns:
            Optional[Dict]: User information if authentication successful, None otherwise
        """
        try:
            # Find user by username
            user = self.users_collection.find_one({"username": username})
            
            if not user:
                logger.warning(f"User not found: {username}")
                return None
            
            # Verify password
            if not self.verify_password(password, user["hashed_password"]):
                logger.warning(f"Invalid password for user: {username}")
                return None
            
            # Check if user is active
            if not user.get("is_active", True):
                logger.warning(f"Inactive user attempted login: {username}")
                return None
            
            # Update last login
            self.users_collection.update_one(
                {"_id": user["_id"]},
                {"$set": {"last_login": datetime.utcnow()}}
            )
            
            logger.info(f"User authenticated successfully: {username}")
            
            # Return user info without password
            return {
                "user_id": str(user["_id"]),
                "username": user["username"],
                "email": user["email"],
                "full_name": user.get("full_name"),
                "is_active": user.get("is_active", True)
            }
            
        except Exception as e:
            logger.error(f"Error authenticating user: {e}")
            return None
    
    def get_user_by_username(self, username: str) -> Optional[Dict]:
        """
        Get user information by username.
        
        Args:
            username: Username
            
        Returns:
            Optional[Dict]: User information or None if not found
        """
        try:
            user = self.users_collection.find_one({"username": username})
            
            if not user:
                return None
            
            return {
                "user_id": str(user["_id"]),
                "username": user["username"],
                "email": user["email"],
                "full_name": user.get("full_name"),
                "is_active": user.get("is_active", True),
                "created_at": user["created_at"].isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting user: {e}")
            return None
    
    def update_user(self, username: str, **kwargs) -> bool:
        """
        Update user information.
        
        Args:
            username: Username
            **kwargs: Fields to update (email, full_name, etc.)
            
        Returns:
            bool: True if update successful, False otherwise
        """
        try:
            # Remove fields that shouldn't be updated directly
            kwargs.pop("username", None)
            kwargs.pop("hashed_password", None)
            kwargs.pop("created_at", None)
            
            if not kwargs:
                return False
            
            # Add updated_at timestamp
            kwargs["updated_at"] = datetime.utcnow()
            
            # Update user
            result = self.users_collection.update_one(
                {"username": username},
                {"$set": kwargs}
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"Error updating user: {e}")
            return False
    
    def change_password(self, username: str, old_password: str, new_password: str) -> bool:
        """
        Change user password.
        
        Args:
            username: Username
            old_password: Current password
            new_password: New password
            
        Returns:
            bool: True if password changed successfully, False otherwise
        """
        try:
            # Authenticate with old password
            user = self.authenticate_user(username, old_password)
            
            if not user:
                return False
            
            # Hash new password
            new_hashed_password = self.get_password_hash(new_password)
            
            # Update password
            result = self.users_collection.update_one(
                {"username": username},
                {
                    "$set": {
                        "hashed_password": new_hashed_password,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            logger.info(f"Password changed for user: {username}")
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"Error changing password: {e}")
            return False
    
    def deactivate_user(self, username: str) -> bool:
        """
        Deactivate a user account.
        
        Args:
            username: Username
            
        Returns:
            bool: True if deactivated successfully, False otherwise
        """
        try:
            result = self.users_collection.update_one(
                {"username": username},
                {
                    "$set": {
                        "is_active": False,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            if result.modified_count > 0:
                logger.info(f"User deactivated: {username}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error deactivating user: {e}")
            return False
    
    def create_password_reset_token(self, email: str) -> Optional[str]:
        """
        Create a password reset token for a user.
        
        Args:
            email: User's email address
            
        Returns:
            Optional[str]: Reset token if user found, None otherwise
        """
        try:
            # Find user by email
            user = self.users_collection.find_one({"email": email})
            
            if not user:
                logger.warning(f"Password reset requested for non-existent email: {email}")
                return None
            
            # Check if user is active
            if not user.get("is_active", True):
                logger.warning(f"Password reset requested for inactive user: {email}")
                return None
            
            # Create reset token (valid for 1 hour)
            reset_token_data = {
                "sub": user["username"],
                "email": email,
                "type": "password_reset"
            }
            
            reset_token = self.create_access_token(
                data=reset_token_data,
                expires_delta=timedelta(hours=1)
            )
            
            # Store reset token info in database (for tracking/invalidation)
            self.users_collection.update_one(
                {"_id": user["_id"]},
                {
                    "$set": {
                        "reset_token": reset_token,
                        "reset_token_created": datetime.utcnow(),
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            logger.info(f"Password reset token created for user: {user['username']}")
            return reset_token
            
        except Exception as e:
            logger.error(f"Error creating password reset token: {e}")
            return None
    
    def verify_reset_token(self, token: str) -> Optional[Dict]:
        """
        Verify a password reset token.
        
        Args:
            token: Reset token
            
        Returns:
            Optional[Dict]: User info if token valid, None otherwise
        """
        try:
            # Decode token
            payload = self.decode_token(token)
            
            if not payload:
                return None
            
            # Check token type
            if payload.get("type") != "password_reset":
                logger.warning("Invalid token type for password reset")
                return None
            
            username = payload.get("sub")
            email = payload.get("email")
            
            if not username or not email:
                return None
            
            # Find user and verify token matches
            user = self.users_collection.find_one({"username": username, "email": email})
            
            if not user:
                return None
            
            # Check if token matches stored token
            if user.get("reset_token") != token:
                logger.warning(f"Reset token mismatch for user: {username}")
                return None
            
            return {
                "username": username,
                "email": email
            }
            
        except Exception as e:
            logger.error(f"Error verifying reset token: {e}")
            return None
    
    def reset_password(self, token: str, new_password: str) -> bool:
        """
        Reset user password using reset token.
        
        Args:
            token: Password reset token
            new_password: New password
            
        Returns:
            bool: True if password reset successful, False otherwise
        """
        try:
            # Verify token
            user_info = self.verify_reset_token(token)
            
            if not user_info:
                logger.warning("Invalid or expired reset token")
                return False
            
            username = user_info["username"]
            
            # Hash new password
            new_hashed_password = self.get_password_hash(new_password)
            
            # Update password and clear reset token
            result = self.users_collection.update_one(
                {"username": username},
                {
                    "$set": {
                        "hashed_password": new_hashed_password,
                        "updated_at": datetime.utcnow()
                    },
                    "$unset": {
                        "reset_token": "",
                        "reset_token_created": ""
                    }
                }
            )
            
            if result.modified_count > 0:
                logger.info(f"Password reset successful for user: {username}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error resetting password: {e}")
            return False
    
    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """
        Get user information by email.
        
        Args:
            email: Email address
            
        Returns:
            Optional[Dict]: User information or None if not found
        """
        try:
            user = self.users_collection.find_one({"email": email})
            
            if not user:
                return None
            
            return {
                "user_id": str(user["_id"]),
                "username": user["username"],
                "email": user["email"],
                "full_name": user.get("full_name"),
                "is_active": user.get("is_active", True),
                "created_at": user["created_at"].isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting user by email: {e}")
            return None
    
    def close(self):
        """Close the MongoDB connection."""
        try:
            self.client.close()
            logger.info("AuthService MongoDB connection closed")
        except Exception as e:
            logger.error(f"Error closing MongoDB connection: {e}")
