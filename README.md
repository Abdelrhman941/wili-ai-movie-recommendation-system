# Wili – AI-Powered Movie Recommendation System

Wili is an AI-powered movie recommendation system that predicts whether a user will like a specific movie and provides personalized movie suggestions based on user preferences and prompts. The system leverages embeddings generated from movie metadata, user interactions, and reviews, and uses a Large Language Model (LLM) to explain recommendations.

---

## Features

1. **Personalized Likelihood Predictions**
   Users complete a short survey selecting movies they like. Wili generates a user embedding from their selections and predicts the likelihood that the user will enjoy any movie in the database.

2. **Prompt-Based Recommendations**
   Users can request recommendations based on natural language prompts, such as:
   `"I want a dark, dystopian movie similar to Blade Runner"`.
   Users can also apply filters like genre, minimum rating, or release year. Wili returns the top three matching movies along with AI-generated explanations describing why each recommendation fits the user’s request.

3. **Database Integration**
   Wili uses Qdrant to store embeddings for users and movies, enabling fast similarity searches.

---

## Getting Started

### Prerequisites

* Python 3.9+
* Docker
* A valid Gemini API key (for LLM-based explanations)

---

### Data Setup

1. Download the datasets:
   [Google Drive Link](https://drive.google.com/file/d/1qjj-5WvKblsaxlvOse--OxEDbA6ZAIty/view?usp=sharing)
   **or** run `scrape_imdb.py` to collect data directly from IMDb.

2. Place the following files in the `data/` folder:

   ```
   movies.csv
   reviews.json
   ```

3. Run preprocessing scripts in order:

   ```bash
   python preprocess_movies.py
   python preprocess_reviews.py
   python merge_movies_and_reviews.py
   ```

---

### Qdrant Setup

1. Launch Qdrant with Docker:

   ```bash
   docker run -d --name qdrant -p 6333:6333 qdrant/qdrant
   ```

2. Verify the container is running:

   ```bash
   docker ps
   ```

   Example output:

   ```
   CONTAINER ID   IMAGE           PORTS                    NAMES
   abcd1234       qdrant/qdrant   0.0.0.0:6333->6333/tcp   qdrant
   ```

3. Upload embeddings:

   ```bash
   python embed_and_upload_local.py
   ```

4. Access Qdrant UI at: [http://localhost:6333/dashboard](http://localhost:6333/dashboard)

---

### Backend Setup

1. Add your Gemini API key to the `.env` file in the `backend/` folder.

2. Install dependencies:

   ```bash
   cd backend
   pip install -r requirements.txt
   ```

3. Start the backend server:

   ```bash
   python app.py
   ```

4. Access the dashboard at: [http://127.0.0.1:5000](http://127.0.0.1:5000)

---

### Using the Application

* **Sign Up / Log In**
  First-time users must sign up. Returning users can log in.

* **Survey**
  Users select 10 movies they have seen and liked. This generates a personalized user embedding.

* **Wili Functionality**
  Enter the name of a movie to get a predicted likelihood of liking it, based on the user embedding and movie embeddings.

* **Recommendations**
  Enter a natural language prompt along with optional filters (genre, minimum rating, release year). Wili returns three recommended movies along with AI-generated explanations for each recommendation.

---

## Project Structure

```
Wili-Ai-powered-movie-recommendation-app/
│
├── backend/
│   ├── .env
│   ├── app.py
│   ├── requirements.txt
│   ├── config.py
│   ├── models.py
│   ├── auth.py
│   ├── embedding_service.py
│   ├── recommendation_service.py
│   └── utils.py
│
├── frontend/
│   ├── index.html
│   ├── signup.html
│   ├── login.html
│   ├── survey.html
│   ├── dashboard.html
│   ├── css/
│   │   └── style.css
│   └── js/
│       ├── auth.js
│       ├── survey.js
│       └── app.js
│
└── data/
    ├── movies_for_embedding.json
    ├── movies.csv
    ├── reviews.json
    ├── scrape_imdb.py
    ├── preprocess_movies.py
    ├── preprocess_reviews.py
    ├── embed_and_upload_local.py
    └── merge_movies_and_reviews.py
```

---

## Qdrant Database Schema

**Users Collection**

* `user_id`
* `username`
* `password_hash`
* `user_embedding`

**Movies Collection**

* `movie_id`
* `title`
* `genre`
* `rating`
* `release_date`
* `runtime_min`
* `url`
* `movie_embedding`

