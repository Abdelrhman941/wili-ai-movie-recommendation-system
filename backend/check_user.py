from models import QdrantDB
from config import Config

db = QdrantDB()

user_id = "2022ce8b-a24b-4253-9f99-f21389103701"

try:
    user = db.client.retrieve(
    collection_name=Config.USERS_COLLECTION,
    ids=[user_id],
    with_vectors=True  # 👈 ADD THIS
)[0]
    
    print(f"User payload: {user.payload}")
    print(f"User vector exists: {user.vector is not None}")
    print(f"User vector type: {type(user.vector)}")
    if user.vector:
        print(f"User vector length: {len(user.vector)}")
        print(f"First 5 values: {user.vector[:5]}")
except Exception as e:
    print(f"Error: {e}")