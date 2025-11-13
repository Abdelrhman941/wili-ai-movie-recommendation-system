#config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-change-in-production')
    
    # Qdrant
    QDRANT_HOST = os.getenv('QDRANT_HOST', 'localhost')
    QDRANT_PORT = int(os.getenv('QDRANT_PORT', 6333))
    MOVIES_COLLECTION = 'movies'
    USERS_COLLECTION = 'users'
    
    # Embedding Model
    EMBEDDING_MODEL = 'sentence-transformers/all-mpnet-base-v2'
    EMBEDDING_DIM = 768  # Dimension for all-mpnet-base-v2
    
    # Gemini API
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
    
    # Survey
    MOVIES_PER_ROUND = 3
    TOTAL_MOVIES_TO_SELECT = 10
    
    # Data paths
    MOVIES_JSON_PATH = os.getenv('MOVIES_JSON_PATH', 'data/movies_for_embedding.json')