import pytest
from app import create_app
from pymongo import MongoClient
import os

@pytest.fixture
def app():
    app = create_app()
    app.config.update({
        'TESTING': True,
        'MONGODB_URI': 'mongodb://localhost:27017/test_db'
    })
    return app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def runner(app):
    return app.test_cli_runner()

@pytest.fixture(autouse=True)
def setup_database():
    # Connect to test database
    client = MongoClient('mongodb://localhost:27017/')
    db = client['test_db']
    
    # Clear all collections before each test
    db.users.delete_many({})
    
    yield db
    
    # Clean up after tests
    client.drop_database('test_db') 