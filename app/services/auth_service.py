from typing import Dict, Optional
from app.models.user import User
import bcrypt
from datetime import datetime, timedelta
from flask_jwt_extended import create_access_token
import uuid


class AuthService:
    def __init__(self):
        pass

    def register(self, email: str, password: str) -> Dict:
        """Register a new user"""
        # Check if user already exists
        if User.objects(email=email).first():
            raise ValueError("Email already registered")

        # Hash password
        hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

        # Create new user
        user_id = str(uuid.uuid4())
        user = User(
            user_id=user_id, email=email, password=hashed_password.decode("utf-8")
        )
        user.save()

        # Generate access token
        access_token = create_access_token(identity=str(user.user_id))

        return {
            "message": "User registered successfully",
            "access_token": access_token,
            "user": user.to_dict(),
        }

    def login(self, email: str, password: str) -> Dict:
        """Login user"""
        # Find user by email
        user = self.get_user_by_email(email)
        if not user:
            raise ValueError("Invalid email or password")

        # Verify password
        if not bcrypt.checkpw(password.encode("utf-8"), user.password.encode("utf-8")):
            raise ValueError("Invalid email or password")

        # Generate access token
        access_token = create_access_token(identity=user.user_id)

        return {
            "message": "Login successful",
            "access_token": access_token,
            "user": user.to_dict(),
        }

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        return User.objects(user_id=user_id).first()

    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        return User.objects(email=email).first()
