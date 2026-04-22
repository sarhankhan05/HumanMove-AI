import os
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import pandas as pd
import numpy as np
import pyarrow.parquet as pq

# 1. Define the CNN Architecture
class ChessCNN(nn.Module):
    def __init__(self):
        super(ChessCNN, self).__init__()
        # Input shape: (Batch, 12, 8, 8)
        self.conv_block = nn.Sequential(
            nn.Conv2d(in_channels=12, out_channels=64, kernel_size=3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(),
            nn.Conv2d(in_channels=64, out_channels=128, kernel_size=3, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU()
        )
        
        # Flatten size: 128 channels * 8 * 8 = 8192
        self.fc_block = nn.Sequential(
            nn.Linear(8192, 4096)
            # We output raw logits here because nn.CrossEntropyLoss applies Softmax internally
        )

    def forward(self, x):
        x = self.conv_block(x)
        x = x.view(-1, 8192) # Flatten
        x = self.fc_block(x)
        return x

# 2. PyTorch Dataset for Parquet
class ChessParquetDataset(Dataset):
    def __init__(self, parquet_path):
        print(f"Loading data from {parquet_path}...")
        # For huge datasets, use pyarrow dataset iterators. 
        # Here we read via pandas for straightforward batching.
        table = pq.read_table(parquet_path)
        self.df = table.to_pandas()
        print(f"Loaded {len(self.df)} expert positions.")

    def __len__(self):
        return len(self.df)

    def __getitem__(self, idx):
        row = self.df.iloc[idx]
        
        # Reconstruct the 12x8x8 tensor from the flattened array
        tensor_1d = np.array(row['board_tensor'], dtype=np.float32)
        tensor_3d = tensor_1d.reshape((12, 8, 8))
        
        target = int(row['target_move'])
        
        return torch.tensor(tensor_3d), torch.tensor(target, dtype=torch.long)

def train_model():
    # Setup Device (CUDA if available)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Training on device: {device}")
    
    # Hyperparameters
    BATCH_SIZE = 128
    LEARNING_RATE = 0.001
    EPOCHS = 5
    
    # Prepare Data
    # We switch to local path because pyarrow requires complex DLL setup for HDFS on Windows
    parquet_path = "datasets/tensors.parquet"
    
    if not os.path.exists(parquet_path):
         print(f"ERROR: Local data not found at {parquet_path}. Please run 'hdfs dfs -get /chess/tensors.parquet datasets/' first.")
         return
         
    dataset = ChessParquetDataset(parquet_path)
    dataloader = DataLoader(dataset, batch_size=BATCH_SIZE, shuffle=True, num_workers=0)
    
    # Initialize Model, Loss, and Optimizer
    model = ChessCNN().to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=LEARNING_RATE)
    
    # Training Loop
    print("Starting Training...")
    for epoch in range(EPOCHS):
        model.train()
        running_loss = 0.0
        correct_preds = 0
        total_preds = 0
        
        for batch_idx, (inputs, targets) in enumerate(dataloader):
            inputs, targets = inputs.to(device), targets.to(device)
            
            optimizer.zero_grad()
            
            # Forward pass
            outputs = model(inputs)
            loss = criterion(outputs, targets)
            
            # Backward pass and optimize
            loss.backward()
            optimizer.step()
            
            running_loss += loss.item()
            
            # Calculate accuracy
            _, predicted = torch.max(outputs.data, 1)
            total_preds += targets.size(0)
            correct_preds += (predicted == targets).sum().item()
            
            if batch_idx % 50 == 0:
                print(f"Epoch [{epoch+1}/{EPOCHS}], Batch [{batch_idx}/{len(dataloader)}], Loss: {loss.item():.4f}")
                
        epoch_loss = running_loss / len(dataloader)
        epoch_acc = 100 * correct_preds / total_preds
        print(f"--- Epoch {epoch+1} Summary: Loss={epoch_loss:.4f}, Accuracy={epoch_acc:.2f}% ---")
        
    # Save the trained model weights
    os.makedirs("models", exist_ok=True)
    torch.save(model.state_dict(), "models/chess_cnn.pth")
    print("Training complete! Model saved to models/chess_cnn.pth")

if __name__ == "__main__":
    train_model()
