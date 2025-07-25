from stockfish import Stockfish

# Initialize Stockfish engine
stockfish = Stockfish("/usr/games/stockfish")  # Default path on Raspberry Pi

# Set up a position with a few example moves
stockfish.set_position(["e2e4", "e7e5"])

# Get the best move from current position
best_move = stockfish.get_best_move()
print("Stockfish recommends:", best_move)