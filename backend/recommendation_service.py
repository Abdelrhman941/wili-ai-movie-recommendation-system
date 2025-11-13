import google.generativeai as genai
import json
from config import Config
from models import QdrantDB
from embedding_service import encode_text, combine_embeddings, calculate_similarity

# Configure Gemini
genai.configure(api_key=Config.GEMINI_API_KEY)
gemini_model = genai.GenerativeModel('gemini-2.5-flash')


db = QdrantDB()

def load_movie_synopsis(movie_id):
    """Load movie synopsis from movies_for_embedding.json"""
    try:
        with open(Config.MOVIES_JSON_PATH, 'r', encoding='utf-8') as f:
            movies_data = json.load(f)
        
        for movie in movies_data:
            if movie['movie_id'] == movie_id:
                return movie.get('text_for_embedding', '')
        
        return None
    except Exception as e:
        print(f"Error loading synopsis: {e}")
        return None


def generate_explanation(movie_title, movie_id, user_prompt):
    """
    Generate AI explanation for why a movie was recommended
    
    Args:
        movie_title: Title of the recommended movie
        movie_id: ID of the movie
        user_prompt: User's original prompt
    
    Returns:
        AI-generated explanation string
    """
    # Load synopsis and reviews
    synopsis = load_movie_synopsis(movie_id)
    
    if not synopsis:
        return "This movie was recommended based on similarity to your preferences."
    
    # Create prompt for Gemini
    prompt = f"""You are a movie recommendation assistant. Based on the following information, explain in 2-3 sentences why this movie was recommended to the user.

User's Request: {user_prompt}

Recommended Movie: {movie_title}

Movie Information:
{synopsis}

Provide a concise, engaging explanation that highlights how this movie matches the user's request. Focus on key themes, style, and atmosphere."""
    
    try:
        response = gemini_model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Error generating explanation: {e}")
        return f"{movie_title} was recommended based on its similarity to your preferences and the themes in your request."


def wili_check(user_id, movie_title):
    """
    Use Case A: Check if user would like a specific movie
    
    Args:
        user_id: User's ID
        movie_title: Title of movie to check
    
    Returns:
        Dictionary with likelihood percentage and explanation
    """
    try:
        # ✅ FIXED: Ensure we retrieve vectors with the user data
        user = db.client.retrieve(
            collection_name=Config.USERS_COLLECTION,
            ids=[user_id],
            with_vectors=True  # 👈 ADDED THIS LINE
        )[0]
        
        user_embedding = user.vector
        
        # Check if user has completed survey
        if user_embedding is None or len(user_embedding) == 0:
            return None, "Please complete the movie survey first to get personalized recommendations"
        
        # Find the movie
        movie = db.search_movie_by_title(movie_title)
        if not movie:
            return None, f"Movie '{movie_title}' not found in database"
        
        # Get movie embedding
        movie = db.get_movie_by_id(movie.payload['movie_id'])
        if movie is None or movie.vector is None:
            return None, f"Movie '{movie_title}' data is incomplete"
        
        movie_embedding = movie.vector
        
        # Calculate similarity
        likelihood = calculate_similarity(user_embedding, movie_embedding)
        
        return {
            'movie_title': movie.payload['title'],
            'likelihood': round(likelihood, 2),
            'movie_info': {
                'genre': movie.payload.get('genre', 'N/A'),
                'rating': movie.payload.get('rating', 'N/A'),
                'release_date': movie.payload.get('release_date', 'N/A'),
                'runtime_min': movie.payload.get('runtime_min', 'N/A')
            }
        }, None
    
    except Exception as e:
        print(f"Error in wili_check: {e}")
        return None, f"An error occurred: {str(e)}"


def get_recommendations(user_prompt, min_rating=None, min_release_date=None, genre=None):
    """
    Use Case B: Get movie recommendations based on prompt and filters
    
    Args:
        user_prompt: User's text prompt
        min_rating: Minimum rating filter (optional)
        min_release_date: Minimum release date filter (optional)
        genre: Genre filter (optional)
    
    Returns:
        List of recommended movies with explanations
    """
    try:
        # Parse prompt to extract movie mentions
        movie_mentioned = None
        prompt_parts = user_prompt.lower().split()
        
        # Try to find a mentioned movie (this is simplified - you might want better NLP)
        movies = db.client.scroll(
            collection_name=Config.MOVIES_COLLECTION,
            limit=100,
            with_payload=True,
            with_vectors=False
        )[0]
        
        for movie in movies:
            title = movie.payload.get('title', '').lower()
            if title in user_prompt.lower():
                movie_mentioned = movie
                break
        
        # Compute query embedding
        if movie_mentioned:
            # Get movie embedding
            full_movie = db.get_movie_by_id(movie_mentioned.payload['movie_id'])
            movie_embedding = full_movie.vector
            
            # Encode remaining text
            text_without_movie = user_prompt.lower().replace(movie_mentioned.payload['title'].lower(), '').strip()
            if text_without_movie:
                text_embedding = encode_text(text_without_movie)
                query_embedding = combine_embeddings(movie_embedding, text_embedding)
            else:
                query_embedding = movie_embedding
        else:
            # Just encode the entire prompt
            query_embedding = encode_text(user_prompt)
        
        # Build filters
        filters = {"must": []}
        
        if min_rating:
            filters["must"].append({
                "key": "rating",
                "range": {"gte": float(min_rating)}
            })
        
        if min_release_date:
            filters["must"].append({
                "key": "release_date",
                "range": {"gte": min_release_date}
            })
        
        if genre:
            filters["must"].append({
                "key": "genre",
                "match": {"text": genre.lower()}
            })
        
        # Search for similar movies
        filter_param = filters if filters["must"] else None
        results = db.search_similar_movies(query_embedding, filters=filter_param, limit=3)
        
        # Generate explanations for each recommendation
        recommendations = []
        for result in results:
            movie_id = result.payload['movie_id']
            movie_title = result.payload['title']
            
            explanation = generate_explanation(movie_title, movie_id, user_prompt)
            
            recommendations.append({
                'movie_title': movie_title,
                'similarity_score': round(result.score * 100, 2),
                'explanation': explanation,
                'movie_info': {
                    'genre': result.payload.get('genre', 'N/A'),
                    'rating': result.payload.get('rating', 'N/A'),
                    'release_date': result.payload.get('release_date', 'N/A'),
                    'runtime_min': result.payload.get('runtime_min', 'N/A')
                }
            })
        
        return recommendations, None
    
    except Exception as e:
        print(f"Error in get_recommendations: {e}")
        return None, f"An error occurred: {str(e)}"
