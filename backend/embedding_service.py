#embedding_service.py
from sentence_transformers import SentenceTransformer
import numpy as np
from config import Config
from models import QdrantDB

# Load the embedding model
model = SentenceTransformer(Config.EMBEDDING_MODEL)
db = QdrantDB()

def compute_user_embedding(movie_ids):
    """
    Compute user embedding by averaging the embeddings of selected movies
    
    Args:
        movie_ids: List of movie IDs selected by the user
    
    Returns:
        numpy array of the averaged embedding
    """
    embeddings = []
    
    for movie_id in movie_ids:
        movie = db.get_movie_by_id(movie_id)
        if movie and movie.vector:
            embeddings.append(movie.vector)
    
    if not embeddings:
        # Return zero embedding if no movies found
        return np.zeros(Config.EMBEDDING_DIM)
    
    # Average all movie embeddings
    user_embedding = np.mean(embeddings, axis=0)
    
    # Normalize the embedding
    norm = np.linalg.norm(user_embedding)
    if norm > 0:
        user_embedding = user_embedding / norm
    
    return user_embedding

def encode_text(text):
    """
    Encode text into an embedding vector
    
    Args:
        text: Text to encode
    
    Returns:
        numpy array of the embedding
    """
    embedding = model.encode(text, convert_to_numpy=True)
    return embedding

def combine_embeddings(movie_embedding, text_embedding, movie_weight=0.7):
    """
    Combine movie and text embeddings with weighted average
    
    Args:
        movie_embedding: Embedding of a movie
        text_embedding: Embedding of text prompt
        movie_weight: Weight for movie embedding (text gets 1-movie_weight)
    
    Returns:
        Combined embedding
    """
    # Convert to numpy arrays if they aren't already
    movie_emb = np.array(movie_embedding)
    text_emb = np.array(text_embedding)
    
    combined = movie_weight * movie_emb + (1 - movie_weight) * text_emb
    
    # Normalize
    norm = np.linalg.norm(combined)
    if norm > 0:
        combined = combined / norm
    
    return combined

def calculate_similarity(embedding1, embedding2):
    """
    Calculate cosine similarity between two embeddings
    
    Args:
        embedding1: First embedding vector
        embedding2: Second embedding vector
    
    Returns:
        Similarity score (0-1)
    """
    # Ensure they're numpy arrays
    e1 = np.array(embedding1)
    e2 = np.array(embedding2)
    
    # Calculate cosine similarity
    dot_product = np.dot(e1, e2)
    norm1 = np.linalg.norm(e1)
    norm2 = np.linalg.norm(e2)
    
    if norm1 == 0 or norm2 == 0:
        return 0.0
    
    similarity = dot_product / (norm1 * norm2)
    
    # Convert to percentage (0-100)
    return float((similarity + 1) / 2 * 100)  # Normalize from [-1,1] to [0,100]