from mongoengine import connect
from flask import current_app


def init_db(app):
    """Initialize database connection"""
    connect(
        db=app.config["MONGODB_DB"],
        host=app.config["MONGODB_HOST"],
        port=app.config["MONGODB_PORT"],
        username=app.config.get("MONGODB_USERNAME"),
        password=app.config.get("MONGODB_PASSWORD"),
    )
