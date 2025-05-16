from flask import Flask
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from app.database import init_db
from app.services.auth_service import AuthService
from app.services.wallet_service import WalletService
from app.routes.auth import auth_bp, init_auth_routes, api as auth_api
from app.routes.wallet import wallet_bp, init_wallet_routes
from app.schemas import init_schemas
import os
from dotenv import load_dotenv


def create_app():
    # Load environment variables
    load_dotenv()

    app = Flask(__name__)

    # CORS 설정
    CORS(app)

    # JWT 설정
    app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "your-secret-key")
    jwt = JWTManager(app)

    # MongoDB 설정
    app.config["MONGODB_HOST"] = os.getenv("MONGODB_HOST", "localhost")
    app.config["MONGODB_PORT"] = int(os.getenv("MONGODB_PORT", 27017))
    app.config["MONGODB_DB"] = os.getenv("MONGODB_DB", "crypto_wallet")
    app.config["MONGODB_USERNAME"] = os.getenv("MONGODB_USERNAME")
    app.config["MONGODB_PASSWORD"] = os.getenv("MONGODB_PASSWORD")

    # 데이터베이스 초기화
    init_db(app)

    # 서비스 초기화
    auth_service = AuthService()
    wallet_service = WalletService()

    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix="/api")
    app.register_blueprint(wallet_bp, url_prefix="/api/wallet")

    # 스키마 초기화
    schemas = init_schemas(auth_api)

    # 라우트 초기화
    init_auth_routes(auth_service, schemas)
    init_wallet_routes(schemas)

    # Configure Swagger UI
    app.config["SWAGGER_UI_DOC_EXPANSION"] = "list"
    app.config["RESTX_VALIDATE"] = True
    app.config["RESTX_MASK_SWAGGER"] = False
    app.config["ERROR_404_HELP"] = False

    return app
