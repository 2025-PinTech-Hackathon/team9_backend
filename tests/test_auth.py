import pytest
from app.models.user import User

def test_register_success(client):
    response = client.post('/api/register', json={
        'email': 'test@example.com',
        'password': 'password123'
    })
    assert response.status_code == 201
    assert response.json['message'] == 'User registered successfully'

def test_register_duplicate_email(client):
    # First registration
    client.post('/api/register', json={
        'email': 'test@example.com',
        'password': 'password123'
    })
    
    # Try to register with same email
    response = client.post('/api/register', json={
        'email': 'test@example.com',
        'password': 'password123'
    })
    assert response.status_code == 400
    assert response.json['error'] == 'User already exists'

def test_login_success(client):
    # Register a user
    client.post('/api/register', json={
        'email': 'test@example.com',
        'password': 'password123'
    })
    
    # Try to login
    response = client.post('/api/login', json={
        'email': 'test@example.com',
        'password': 'password123'
    })
    assert response.status_code == 200
    assert 'access_token' in response.json

def test_login_wrong_password(client):
    # Register a user
    client.post('/api/register', json={
        'email': 'test@example.com',
        'password': 'password123'
    })
    
    # Try to login with wrong password
    response = client.post('/api/login', json={
        'email': 'test@example.com',
        'password': 'wrongpassword'
    })
    assert response.status_code == 401
    assert response.json['error'] == 'Invalid password'

def test_login_nonexistent_user(client):
    response = client.post('/api/login', json={
        'email': 'nonexistent@example.com',
        'password': 'password123'
    })
    assert response.status_code == 401
    assert response.json['error'] == 'User not found' 