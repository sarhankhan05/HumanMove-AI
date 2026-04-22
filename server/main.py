import os
import torch
import torch.nn as nn
import numpy as np
import chess
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient

# --- 1. PyTorch CNN Architecture Definition ---
class ChessCNN(nn.Module):
    def __init__(self):
        super(ChessCNN, self).__init__()
        self.conv_block = nn.Sequential(
            nn.Conv2d(in_channels=12, out_channels=64, kernel_size=3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(),
            nn.Conv2d(in_channels=64, out_channels=128, kernel_size=3, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU()
        )
        self.fc_block = nn.Sequential(
            nn.Linear(8192, 4096)
        )

    def forward(self, x):
        x = self.conv_block(x)
        x = x.view(-1, 8192)
        x = self.fc_block(x)
        return x

# --- 2. Global State Initialization ---
app = FastAPI(title="Hybrid Chess AI: Deep Learning + Big Data")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["chess_db"]
recommendations_col = db["recommendations"]

# PyTorch Model
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = ChessCNN().to(device)
model_path = "models/chess_cnn.pth"

model_loaded = False
if os.path.exists(model_path):
    model.load_state_dict(torch.load(model_path, map_location=device))
    model.eval()
    model_loaded = True
    print("CNN Model loaded successfully.")
else:
    print("WARNING: CNN model weights not found. AI predictions will be randomized until training is complete.")

# --- 3. Helper Functions ---
def fen_to_tensor(fen):
    board = chess.Board(fen)
    tensor = np.zeros((1, 12, 8, 8), dtype=np.float32)
    piece_to_channel = {
        'P': 0, 'N': 1, 'B': 2, 'R': 3, 'Q': 4, 'K': 5,
        'p': 6, 'n': 7, 'b': 8, 'r': 9, 'q': 10, 'k': 11
    }
    for sq in chess.SQUARES:
        piece = board.piece_at(sq)
        if piece:
            channel = piece_to_channel[piece.symbol()]
            row_idx = 7 - chess.square_rank(sq)
            col_idx = chess.square_file(sq)
            tensor[0, channel, row_idx, col_idx] = 1.0
    return torch.tensor(tensor).to(device)

def get_best_legal_move(fen, logits):
    board = chess.Board(fen)
    legal_moves = list(board.legal_moves)
    
    if not legal_moves:
        return None, 0.0
        
    best_move = None
    highest_score = -float('inf')
    
    # Legal Move Masking
    for move in legal_moves:
        from_sq = move.from_square
        to_sq = move.to_square
        idx = from_sq * 64 + to_sq
        
        score = logits[0][idx].item()
        if score > highest_score:
            highest_score = score
            best_move = move
            
    # Apply Softmax over LEGAL moves only for a readable confidence %
    legal_logits = torch.tensor([logits[0][m.from_square * 64 + m.to_square].item() for m in legal_moves])
    probs = torch.nn.functional.softmax(legal_logits, dim=0)
    best_prob = torch.max(probs).item()
    
    return best_move.uci(), best_prob

# --- 4. API Endpoints ---
@app.get("/recommend")
async def recommend(fen: str = Query(..., description="The FEN string of the current board")):
    # 1. Deep Learning Inference (Strategic Advice)
    cnn_recommendation = None
    if model_loaded:
        try:
            tensor = fen_to_tensor(fen)
            with torch.no_grad():
                logits = model(tensor)
            
            best_move, confidence = get_best_legal_move(fen, logits)
            cnn_recommendation = {
                "move": best_move,
                "confidence": confidence,
                "explanation": f"The CNN selected this move with {confidence*100:.1f}% confidence based on strategic pattern recognition of Expert play."
            }
        except Exception as e:
            print(f"CNN Inference Error: {e}")

    # 2. Big Data Statistics (Human Success Rate)
    stripped_fen = " ".join(fen.strip().split(" ")[:4])
    stats_result = recommendations_col.find_one({"_id": stripped_fen})
    
    if not stats_result and not cnn_recommendation:
        raise HTTPException(status_code=404, detail="No AI or Statistical data available for this position.")

    # 3. Hybrid Response
    return {
        "fen": stripped_fen,
        "deep_learning_ai": cnn_recommendation,
        "big_data_stats": stats_result["recommendations"] if stats_result else None,
        "total_historical_samples": stats_result["total_samples"] if stats_result else 0
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
