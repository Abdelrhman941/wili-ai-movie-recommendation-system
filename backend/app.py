#app.py
from flask import Flask, request, jsonify, send_from_directory, Blueprint
from flask_cors import CORS
from functools import wraps
import os

from config import Config
from auth import register_user, login_user, verify_token
from models import QdrantDB
from embedding_service import compute_user_embedding
from recommendation_service import wili_check, get_recommendations

app = Flask(__name__, static_folder='../frontend')
app.config.from_object(Config)

# Fix CORS
CORS(app, origins="*", supports_credentials=True)

db = QdrantDB()

# Create API blueprint
api = Blueprint('api', __name__, url_prefix='/api')

# Authentication decorator
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        
        if not token:
            return jsonify({'error': 'Token is missing'}), 401
        
        try:
            # Remove 'Bearer ' prefix if present
            if token.startswith('Bearer '):
                token = token[7:]
            
            payload = verify_token(token)
            if not payload:
                return jsonify({'error': 'Token is invalid or expired'}), 401
            
            request.user = payload
        except Exception as e:
            return jsonify({'error': 'Token verification failed'}), 401
        
        return f(*args, **kwargs)
    
    return decorated

# Authentication endpoints
@api.route('/auth/signup', methods=['POST'])
def signup():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400
    
    if len(password) < 6:
        return jsonify({'error': 'Password must be at least 6 characters'}), 400
    
    result, error = register_user(username, password)
    
    if error:
        return jsonify({'error': error}), 400
    
    return jsonify(result), 201

@api.route('/auth/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400
    
    result, error = login_user(username, password)
    
    if error:
        return jsonify({'error': error}), 401
    
    return jsonify(result), 200

@api.route('/auth/verify', methods=['GET'])
@token_required
def verify():
    return jsonify({
        'user_id': request.user['user_id'],
        'username': request.user['username']
    }), 200

# Survey endpoints
@api.route('/survey/movies', methods=['GET'])
@token_required
def get_survey_movies():
    """Get random movies for survey"""
    exclude_ids = request.args.get('exclude', '').split(',') if request.args.get('exclude') else []
    
    movies = db.get_random_movies(count=Config.MOVIES_PER_ROUND, exclude_ids=exclude_ids)
    
    movie_list = []
    for movie in movies:
        movie_list.append({
            'movie_id': movie.payload['movie_id'],
            'title': movie.payload['title'],
            'genre': movie.payload.get('genre', 'N/A'),
            'rating': movie.payload.get('rating', 'N/A'),
            'release_date': movie.payload.get('release_date', 'N/A')
        })
    
    return jsonify({'movies': movie_list}), 200

@api.route('/survey/submit', methods=['POST'])
@token_required
def submit_survey():
    """Submit completed survey and compute user embedding"""
    data = request.json
    selected_movie_ids = data.get('movie_ids', [])
    
    if len(selected_movie_ids) != Config.TOTAL_MOVIES_TO_SELECT:
        return jsonify({
            'error': f'Please select exactly {Config.TOTAL_MOVIES_TO_SELECT} movies'
        }), 400
    
    # Compute user embedding
    user_embedding = compute_user_embedding(selected_movie_ids)
    
    # Update user's embedding in database
    user_id = request.user['user_id']
    db.update_user_embedding(user_id, user_embedding)
    
    return jsonify({
        'message': 'Survey completed successfully',
        'embedding_computed': True
    }), 200

# Use Case A: Wili check
@api.route('/wili/check', methods=['POST'])
@token_required
def check_movie():
    """Check if user would like a specific movie"""
    print("=== INSIDE check_movie FUNCTION ===")
    data = request.json
    print(f"Request data: {data}")
    movie_title = data.get('movie_title')
    print(f"Movie title: {movie_title}")
    
    if not movie_title:
        return jsonify({'error': 'Movie title is required'}), 400
    
    user_id = request.user['user_id']
    print(f"User ID: {user_id}")
    
    result, error = wili_check(user_id, movie_title)
    print(f"Result: {result}")
    print(f"Error: {error}")
    
    if error:
        return jsonify({'error': error}), 404
    
    return jsonify(result), 200

# Use Case B: Get recommendations
@api.route('/recommendations', methods=['POST'])
@token_required
def get_movie_recommendations():
    """Get movie recommendations based on prompt and filters"""
    data = request.json
    prompt = data.get('prompt')
    min_rating = data.get('min_rating')
    min_release_date = data.get('min_release_date')
    genre = data.get('genre')
    
    if not prompt:
        return jsonify({'error': 'Prompt is required'}), 400
    
    recommendations, error = get_recommendations(
        user_prompt=prompt,
        min_rating=min_rating,
        min_release_date=min_release_date,
        genre=genre
    )
    
    if error:
        return jsonify({'error': error}), 400
    
    return jsonify({'recommendations': recommendations}), 200

# Health check
@api.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy'}), 200

# Register blueprint BEFORE static routes
app.register_blueprint(api)

# Serve static files - MUST BE LAST
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path == "":
        return send_from_directory(app.static_folder, 'index.html')
    else:
        file_path = os.path.join(app.static_folder, path)
        if os.path.exists(file_path):
            return send_from_directory(app.static_folder, path)
        else:
            return send_from_directory(app.static_folder, 'index.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)