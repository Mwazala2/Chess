import chess

class ChessGame:
    def __init__(self):
        self.board = chess.Board()

    def push_move(self, uci_move):
        try:
            move = chess.Move.from_uci(uci_move)
            if move in self.board.legal_moves:
                self.board.push(move)
                return True, "Move played."
            else:
                return False, "Illegal move."
        except Exception as e:
            return False, f"Invalid move format: {e}"

    def ai_move(self, level="easy", engine_source="local"):
        # Dummy implementation for AI move selection
        # For demonstration, just pick the first legal move
        legal_moves = list(self.board.legal_moves)
        if legal_moves:
            move = legal_moves[0].uci()
            self.board.push(legal_moves[0])
            return move, "AI played: " + move
        else:
            return None, "No legal moves left."

    def is_game_over(self):
        return self.board.is_game_over()

    def get_result(self):
        return self.board.result()
