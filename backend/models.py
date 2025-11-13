from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from config import Config
import uuid


class QdrantDB:
    def __init__(self):
        self.client = QdrantClient(host=Config.QDRANT_HOST, port=Config.QDRANT_PORT)
        self._ensure_collections()

    def _ensure_collections(self):
        """Ensure both movies and users collections exist"""
        collections = [col.name for col in self.client.get_collections().collections]

        # Users collection should already exist (movies)
        # Create users collection if it doesn't exist
        if Config.USERS_COLLECTION not in collections:
            self.client.create_collection(
                collection_name=Config.USERS_COLLECTION,
                vectors_config=VectorParams(
                    size=Config.EMBEDDING_DIM,
                    distance=Distance.COSINE
                )
            )
            print(f"Created collection: {Config.USERS_COLLECTION}")

    def get_random_movies(self, count=3, exclude_ids=None):
        """Get random movies from the database"""
        # Qdrant doesn't have native random sampling, so we'll use scroll with random offset
        movies = self.client.scroll(
            collection_name=Config.MOVIES_COLLECTION,
            limit=count * 10,  # Get more to filter out excluded
            with_payload=True,
            with_vectors=False
        )[0]

        if exclude_ids:
            movies = [m for m in movies if m.payload.get('movie_id') not in exclude_ids]

        return movies[:count]

    def get_movie_by_id(self, movie_id):
        """Get a specific movie by its ID"""
        results = self.client.scroll(
            collection_name=Config.MOVIES_COLLECTION,
            scroll_filter={
                "must": [
                    {
                        "key": "movie_id",
                        "match": {"value": movie_id}
                    }
                ]
            },
            limit=1,
            with_payload=True,
            with_vectors=True
        )[0]

        return results[0] if results else None

    def search_movie_by_title(self, title):
        """Search for a movie by title (case-insensitive partial match)"""
        # Since Qdrant doesn't support full-text search natively,
        # we'll scroll through and filter in Python
        movies = self.client.scroll(
            collection_name=Config.MOVIES_COLLECTION,
            limit=1000,
            with_payload=True,
            with_vectors=False
        )[0]

        title_lower = title.lower()
        matches = [m for m in movies if title_lower in m.payload.get('title', '').lower()]

        return matches[0] if matches else None

    def create_user(self, username, password_hash, user_embedding):
        """Create a new user in the users collection"""
        user_id = str(uuid.uuid4())

        point = PointStruct(
            id=user_id,
            vector=user_embedding.tolist(),
            payload={
                'user_id': user_id,
                'username': username,
                'password_hash': password_hash
            }
        )

        self.client.upsert(
            collection_name=Config.USERS_COLLECTION,
            points=[point]
        )

        return user_id

    def get_user_by_username(self, username):
        """Get user by username"""
        results = self.client.scroll(
            collection_name=Config.USERS_COLLECTION,
            scroll_filter={
                "must": [
                    {
                        "key": "username",
                        "match": {"value": username}
                    }
                ]
            },
            limit=1,
            with_payload=True,
            with_vectors=True
        )[0]

        return results[0] if results else None

    def update_user_embedding(self, user_id, new_embedding):
        """Update a user's embedding"""
        # Get current user data WITH VECTORS
        user = self.client.retrieve(
            collection_name=Config.USERS_COLLECTION,
            ids=[user_id],
            with_vectors=True  # 👈 include vectors
        )[0]

        # Update with new embedding
        point = PointStruct(
            id=user_id,
            vector=new_embedding.tolist(),
            payload=user.payload
        )

        self.client.upsert(
            collection_name=Config.USERS_COLLECTION,
            points=[point]
        )

    def search_similar_movies(self, query_embedding, filters=None, limit=3):
        """Search for similar movies using vector similarity"""
        search_params = {
            "collection_name": Config.MOVIES_COLLECTION,
            "query_vector": query_embedding.tolist(),
            "limit": limit,
            "with_payload": True
        }

        if filters:
            search_params["query_filter"] = filters

        return self.client.search(**search_params)
