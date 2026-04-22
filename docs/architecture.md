# Hybrid Architecture & AI Philosophy

This document explains the strategic shift from a purely statistical engine to a **Hybrid CNN-Statistical Engine**.

## 1. The Need for Hybridization
While statistical analysis tells us what *has worked* in the past (Human Success Rate), it cannot "understand" the board. By adding a Convolutional Neural Network (CNN), we introduce **Strategic Intent**. The system now knows not only that a move is popular, but why it is positionally sound based on piece interactions.

## 2. The Deep Learning Layer (CNN)

### Tensor Representation ($8 \times 8 \times 12$)
We represent the board as a multidimensional numerical tensor.
- **Dimensions**: 8x8 squares.
- **Channels (12)**: 6 for White pieces (P, N, B, R, Q, K) and 6 for Black pieces (p, n, b, r, q, k).
- **Encoding**: Binary encoding ($1$ if a piece is present, $0$ otherwise). This allows the CNN filters to recognize complex patterns like pawn chains, open files, and pins.

### Expert-Only Training
The CNN is trained exclusively on moves played by **Expert players (Elo > 2000)**. This ensures the network learns high-level strategic goals rather than just replicating "average" human play or common blunders.

### Policy Head ($4096$)
The output layer is a fully connected "Policy Head" that predicts a probability distribution over all 4096 possible from-to square combinations.

## 3. The Statistical Layer (Big Data)
While the CNN provides "Strategic Advice," the **Big Data** layer (MongoDB) provides **Empirical Context**. It answers: *"The AI likes this move, but how have regular humans of my rating level actually performed with it?"*

## 4. Hybrid Serving Logic
The FastAPI serving layer integrates these two worlds:
1. **Inference**: Converts FEN to tensor and runs the PyTorch model on the GPU.
2. **Legal Move Masking**: An algorithmic filter is applied to the CNN output. We take the valid move list from the `chess` library and zero out any "illegal" predictions made by the network, ensuring 100% tactical accuracy.
3. **Combination**: The final JSON response merges the CNN's strategic confidence with the historical win rates fetched from MongoDB.

## 5. Scalability & Data Locality
To handle the 29.2M position dataset, the pipeline is optimized for **Data Locality**:
- **HDFS Block Sizing (128MB)**: Aligns HDFS storage with Spark's parallel task scheduling.
- **Replication (Factor 3)**: Ensures data is available locally on multiple nodes, preventing network I/O bottlenecks during the tensor generation phase.
