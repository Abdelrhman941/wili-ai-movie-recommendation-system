from flask_bcrypt import Bcrypt
import jwt
from datetime import datetime, timedelta
from config import Config
from models import QdrantDB

bcrypt = Bcrypt()
db = QdrantDB()

def hash_password(password):
    """Hash a password"""
    return bcrypt.generate_password_hash(password).decode('utf-8')

def check_password(password_hash, password):
    """Verify a password against its hash"""
    return bcrypt.check_password_hash(password_hash, password)

def generate_token(user_id, username):
    """Generate JWT token for user"""
    payload = {
        'user_id': user_id,
        'username': username,
        'exp': datetime.utcnow() + timedelta(days=7)
    }
    return jwt.encode(payload, Config.SECRET_KEY, algorithm='HS256')

def verify_token(token):
    """Verify JWT token"""
    try:
        payload = jwt.decode(token, Config.SECRET_KEY, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def register_user(username, password):
    """Register a new user (without embedding initially)"""
    # Check if username already exists
    existing_user = db.get_user_by_username(username)
    if existing_user:
        return None, "Username already exists"
    
    # For now, create a zero embedding (will be updated after survey)
    import numpy as np
    zero_embedding = np.zeros(Config.EMBEDDING_DIM)
    
    # Hash password and create user
    password_hash = hash_password(password)
    user_id = db.create_user(username, password_hash, zero_embedding)
    
    # Generate token
    token = generate_token(user_id, username)
    
    return {
        'user_id': user_id,
        'username': username,
        'token': token
    }, None

def login_user(username, password):
    """Login user"""
    # Get user from database
    user = db.get_user_by_username(username)
    if not user:
        return None, "Invalid username or password"
    
    # Check password
    if not check_password(user.payload['password_hash'], password):
        return None, "Invalid username or password"
    
    # Generate token
    token = generate_token(user.payload['user_id'], username)
    
    return {
        'user_id': user.payload['user_id'],
        'username': username,
        'token': token,
        'has_embedding': any(user.vector)  # Check if user has completed survey
    }, None