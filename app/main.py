import os
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from typing import List, Optional

from app.recommender import ContentBasedRecommender

# ==============================================================================
# FASTAPI APP INITIALIZATION
# ==============================================================================
app = FastAPI(
    title="TechStack Recommender AI",
    description="A content-based recommender system utilizing TF-IDF and Cosine Similarity to match skills to career roles.",
    version="1.0.0"
)

# ==============================================================================
# FILE PATH RESOLUTION & ENGINE SETUP
# ==============================================================================
# Resolve absolute paths to ensure the dataset CSV file is found regardless of 
# where the server command is run from.
BASE_DIR = os.path.dirname(os.path.abspath(__file__)) # .../app
PROJECT_DIR = os.path.dirname(BASE_DIR)              # .../Project 3
DATASET_PATH = os.path.join(PROJECT_DIR, "dataset", "raw_skills.csv")

if not os.path.exists(DATASET_PATH):
    raise FileNotFoundError(f"Missing critical dataset at {DATASET_PATH}")

# Instantiate the custom content-based filtering model (loads, fits vocabulary, computes IDFs)
recommender = ContentBasedRecommender(DATASET_PATH)

# ==============================================================================
# PYDANTIC SCHEMAS (DATA VALIDATION)
# ==============================================================================
class RecommendationRequest(BaseModel):
    """
    Pydantic request body schema for matching recommendations.
    Accepts arrays of skills, interests, and goals alongside the Top-N count.
    """
    skills: List[str] = Field(default_factory=list, description="Array of user skills (e.g. ['python', 'aws'])")
    interests: List[str] = Field(default_factory=list, description="Array of user interests (e.g. ['security', 'machine-learning'])")
    goals: List[str] = Field(default_factory=list, description="Array of user goals (e.g. ['automate infrastructure'])")
    
    # Restrict Top-N to between 1 and 10 to protect database querying performance and prevent visual clutter
    top_n: Optional[int] = Field(default=3, ge=1, le=10, description="Number of recommendations to return (Top-N)")


# ==============================================================================
# API ROUTE HANDLERS
# ==============================================================================
@app.post("/api/recommend")
def get_recommendations(request: RecommendationRequest):
    """
    HTTP POST endpoint that accepts a user profile state.
    Calculates TF-IDF and Cosine Similarity scores.
    Returns:
      - A lists of matched job roles, description, tech stack, and similarity scores.
      - A 'cold_start' boolean flag if the user profile contains no matching terms.
    """
    try:
        results = recommender.recommend(
            skills=request.skills,
            interests=request.interests,
            goals=request.goals,
            top_n=request.top_n
        )
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/skills")
def get_vocabulary_skills():
    """
    HTTP GET endpoint to fetch a list of all unique technical skills in the database.
    Used by the frontend to dynamically populate preset tags during onboarding.
    """
    try:
        skills = recommender.get_all_unique_skills()
        return {"skills": skills}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==============================================================================
# STATIC FILES & PAGE ROUTING
# ==============================================================================
# Ensure the static files directory exists
static_dir = os.path.join(BASE_DIR, "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir)

# Mount static files folder to serve styles, scripts, and media.
# CRITICAL: This mounting block must be placed at the very end of the file. 
# Placing it earlier would cause FastAPI to hijack other route paths (like /api/*) 
# and try to resolve them as static folder files.
app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
def read_root():
    """
    Root endpoint serving the main dashboard HTML interface.
    Falls back to a JSON welcome message if static folder is missing.
    """
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "Welcome to TechStack Recommender API. Place index.html in app/static to view the UI."}
