from flask import Blueprint, jsonify, request
from flask_restx import Resource, Namespace, fields
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services.auth_service import AuthService
from app.services.investment_service import InvestmentService
from datetime import datetime
import traceback


auth_bp = Blueprint("auth", __name__)
ns = Namespace("auth", description="Authentication operations")


def init_auth_routes(auth_service: AuthService, api):
    api.add_namespace(ns)

    # Auth schemas
    auth_register = api.model(
        "AuthRegister",
        {
            "email": fields.String(required=True, description="User email"),
            "password": fields.String(required=True, description="User password"),
        },
    )

    auth_login = api.model(
        "AuthLogin",
        {
            "email": fields.String(required=True, description="User email"),
            "password": fields.String(required=True, description="User password"),
        },
    )

    auth_response = api.model(
        "AuthResponse", {"access_token": fields.String(description="JWT access token")}
    )

    user_response = api.model(
        "UserResponse",
        {
            "user_id": fields.String(description="User ID"),
            "email": fields.String(description="User email"),
            "created_at": fields.DateTime(description="User creation date"),
            "updated_at": fields.DateTime(description="Last update date"),
        },
    )

    error_response = api.model(
        "ErrorResponse", {"error": fields.String(description="Error message")}
    )

    @ns.route("/register")
    class Register(Resource):
        @ns.doc("register")
        @ns.expect(auth_register)
        @ns.response(201, "User registered successfully", user_response)
        @ns.response(400, "Invalid input", error_response)
        def post(self):
            """Register a new user"""
            data = request.get_json()
            email = data.get("email")
            password = data.get("password")

            if not email or not password:
                return {"error": "Email and password are required"}, 400

            try:
                result = auth_service.register(email, password)
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
                return {"error": str(e)}, 400

    @ns.route("/login")
    class Login(Resource):
        @ns.doc("login")
        @ns.expect(auth_login)
        @ns.response(200, "Login successful", auth_response)
        @ns.response(401, "Invalid credentials", error_response)
        def post(self):
            """Login user"""
            data = request.get_json()
            email = data.get("email")
            password = data.get("password")

            if not email or not password:
                return {"error": "Email and password are required"}, 400

            try:
                result = auth_service.login(email, password)
                return {
                    "message": result["message"],
                    "access_token": result["access_token"],
                }
            except ValueError as e:
                return {"error": str(e)}, 401

    @ns.route("/info")
    class User(Resource):
        @ns.doc(security="Bearer Auth")
        @ns.response(200, "User details", user_response)
        @ns.response(401, "Unauthorized", error_response)
        @jwt_required()
        def get(self):
            """Get user details and investments"""
            current_user_id = get_jwt_identity()
            try:
                print(current_user_id)
                user = auth_service.get_user_by_id(current_user_id)
                print(user)
                input()
                if not user:
                    return {"message": "User not found"}, 404

                # Get user's investments
                investments = list(user.investments)

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
