from flask import Blueprint, jsonify, request
from flask_restx import Resource, Api
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services.auth_service import AuthService
from app.services.investment_service import InvestmentService
from datetime import datetime
import traceback


auth_bp = Blueprint("auth", __name__)
api = Api(
    auth_bp,
    version="1.0",
    title="Authentication API",
    description="API for user authentication",
)


def init_auth_routes(auth_service: AuthService, schemas):
    @api.route("/register")
    class Register(Resource):
        @api.doc(security="Bearer Auth")
        @api.response(201, "User registered successfully", schemas["user_response"])
        @api.response(400, "Invalid input", schemas["error_response"])
        def post(self):
            """Register a new user"""
            data = request.get_json()
            email = data.get("email")
            password = data.get("password")

            if not email or not password:
                return {"message": "Email and password are required"}, 400

            try:
                result = auth_service.register(email, password)
                print(result)
                return {
                    "message": result["message"],
                    "access_token": result["access_token"],
                    "user": {
                        "user_id": str(result["user"]["user_id"]),
                        "email": result["user"]["email"],
                        "created_at": (
                            result["user"]["created_at"].isoformat()
                            if isinstance(result["user"]["created_at"], datetime)
                            else result["user"]["created_at"]
                        ),
                        "updated_at": (
                            result["user"]["updated_at"].isoformat()
                            if isinstance(result["user"]["updated_at"], datetime)
                            else result["user"]["updated_at"]
                        ),
                    },
                }, 201
            except ValueError as e:
                return {"message": str(e)}, 400

    @api.route("/login")
    class Login(Resource):
        @api.doc(security="Bearer Auth")
        @api.response(200, "Login successful", schemas["user_response"])
        @api.response(401, "Invalid credentials", schemas["error_response"])
        def post(self):
            """Login user"""
            data = request.get_json()
            email = data.get("email")
            password = data.get("password")

            if not email or not password:
                return {"message": "Email and password are required"}, 400

            try:
                result = auth_service.login(email, password)
                return result, 200
            except ValueError as e:
                traceback.print_exc()
                return {"message": str(e)}, 401

    @api.route("/info")
    class User(Resource):
        @api.doc(security="Bearer Auth")
        @api.response(200, "User details", schemas["user_response"])
        @api.response(401, "Unauthorized", schemas["error_response"])
        @jwt_required()
        def get(self):
            """Get user details and investments"""
            current_user_id = get_jwt_identity()
            try:
                user = auth_service.get_user_by_id(current_user_id)
                if not user:
                    return {"message": "User not found"}, 404

                # Get user's investments
                investments = InvestmentService.get_user_investments(user)

                return {
                    "message": "User details retrieved successfully",
                    "user": {
                        "id": str(user.id),
                        "email": user.email,
                        "created_at": (
                            user.created_at.isoformat() if user.created_at else None
                        ),
                        "updated_at": (
                            user.updated_at.isoformat() if user.updated_at else None
                        ),
                    },
                    "investments": [inv.to_dict() for inv in investments],
                }, 200
            except Exception as e:
                traceback.print_exc()
                return {"message": str(e)}, 500
