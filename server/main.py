from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient

app = FastAPI(title="Chess AI Recommendation API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"], # Vite Default
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup MongoDB Connection
client = MongoClient("mongodb://localhost:27017/")
db = client["chess_db"]
recommendations_col = db["recommendations"]

@app.get("/")
async def root():
    return {
        "status": "online",
        "description": "Chess Move Recommendation API (Categorized Analysis)",
        "endpoints": {
            "/recommend?fen=...": "Get Popular, Success, and Expert move choices"
        }
    }

@app.get("/recommend")
async def recommend(fen: str = Query(..., description="The FEN string of the current board position")):
    """
    Endpoint to retrieve categorized recommendations for a board state.
    """
    # Standardize FEN (Strip clocks)
    stripped_fen = " ".join(fen.strip().split(" ")[:4])
    
    # Lookup in Hashed Index (_id)
    result = recommendations_col.find_one({"_id": stripped_fen})
    
    if not result:
        raise HTTPException(
            status_code=404, 
            detail="Strategic analysis for this position is currently unavailable in our 128MB chunked dataset."
        )
    
    return {
        "fen": stripped_fen,
        "total_samples": result["total_samples"],
        "recommendations": result["recommendations"]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
