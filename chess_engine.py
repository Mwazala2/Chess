import chess
import chess.engine
import random

CENTER_SQUARES = [chess.E4, chess.D4, chess.E5, chess.D5]

class ChessGame:
    def __init__(self):
        self.board = chess.Board()
        self.engine_path = None  # Set this to path of Stockfish if available

    def get_board_fen(self):
        return self.board.fen()

    def is_game_over(self):
        return self.board.is_game_over()

    def get_result(self):
        if not self.is_game_over():
            return None
        return self.board.result()

    def get_legal_moves(self):
        return [move.uci() for move in self.board.legal_moves]

    def push_move(self, move_uci):
        move = chess.Move.from_uci(move_uci)
        if move in self.board.legal_moves:
            self.board.push(move)
            explanation = self.explain_move(move)
            return True, explanation
        else:
            return False, "Illegal move."

    def ai_move(self, level='easy', engine_source='local'):
        """
        Generate an AI move based on selected level and engine source.
        Levels: 'easy', 'intermediate', 'hard'
        engine_source: 'local' (Stockfish), 'lichess' (cloud), fallback to random if unavailable
        """
        if self.is_game_over():
            return None, "Game is already over."

        if level == 'easy':
            move = random.choice(list(self.board.legal_moves))
            self.board.push(move)
            explanation = self.explain_move(move)
            return move.uci(), explanation

        elif level == 'intermediate':
            move = self.select_heuristic_move()
            self.board.push(move)
            explanation = self.explain_move(move)
            return move.uci(), explanation

        elif level == 'hard':
            # Try Stockfish first, fallback to random if not available
            if engine_source == 'local' and self.engine_path:
                try:
                    with chess.engine.SimpleEngine.popen_uci(self.engine_path) as engine:
                        result = engine.play(self.board, chess.engine.Limit(time=0.1))
                        move = result.move
                        self.board.push(move)
                        explanation = self.explain_move(move)
                        return move.uci(), explanation
                except Exception as e:
                    return self.fallback_ai_move("Stockfish error: " + str(e))
            elif engine_source == 'lichess':
                # To use Lichess, call lichess_best_move externally and push result here
                return None, "Use Lichess cloud engine via app.py."
            else:
                return self.fallback_ai_move("No engine available.")
        else:
            return self.fallback_ai_move("Unknown difficulty level.")

    def fallback_ai_move(self, explanation):
        move = random.choice(list(self.board.legal_moves))
        self.board.push(move)
        return move.uci(), "Fallback AI move: " + explanation

    def select_heuristic_move(self):
        # Prefer: captures > checks > center moves > others
        legal_moves = list(self.board.legal_moves)
        # 1. Captures
        capture_moves = [m for m in legal_moves if self.board.is_capture(m)]
        if capture_moves:
            return random.choice(capture_moves)
        # 2. Checks
        check_moves = []
        for m in legal_moves:
            self.board.push(m)
            if self.board.is_check():
                check_moves.append(m)
            self.board.pop()
        if check_moves:
            return random.choice(check_moves)
        # 3. Center control
        center_moves = [m for m in legal_moves if m.to_square in CENTER_SQUARES]
        if center_moves:
            return random.choice(center_moves)
        # 4. Default
        return random.choice(legal_moves)

    def explain_move(self, move):
        if self.board.is_capture(move):
            return "This move captures an opponent's piece to gain material."
        elif self.board.gives_check(move):
            return "This move puts the opponent's king in check."
        elif self.board.is_castling(move):
            return "This is castling for king safety and rook activation."
        elif self.board.is_en_passant(move):
            return "This is an en passant capture."
        elif self.board.is_checkmate():
            return "Checkmate! The game is over."
        elif self.board.is_stalemate():
            return "Stalemate! The game is drawn."
        else:
            piece = self.board.piece_at(move.to_square)
            if piece and piece.piece_type == chess.KNIGHT:
                return "Developing a knight, controlling the center."
            elif piece and piece.piece_type == chess.BISHOP:
                return "Developing a bishop, increasing activity."
            elif piece and piece.piece_type == chess.QUEEN:
                return "Moving the queen, but be careful not to expose it early."
            elif piece and piece.piece_type == chess.ROOK:
                return "Activating the rook, possibly to open files."
            elif piece and piece.piece_type == chess.PAWN:
                return "Advancing a pawn, controlling center or opening lines."
            else:
                return "A standard move for piece activity or control."
