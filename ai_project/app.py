import tkinter as tk
import tkinter.messagebox as messagebox
import tkinter.font as tkfont
import sys
import random
import chess  # Requires 'pip install python-chess'

# --- Constants ---
# Board dimensions (8x8)
ROWS, COLS = 8, 8
SQUARE_SIZE = 80
WIDTH, HEIGHT = COLS * SQUARE_SIZE, ROWS * SQUARE_SIZE

# Colors (Tkinter-friendly)
LIGHT_SQUARE = '#EEEED2'  # (238, 238, 210)
DARK_SQUARE = '#769656'   # (118, 150, 86)
HIGHLIGHT_COLOR = '#FFFF33' # (255, 255, 51) - Using a solid yellow for highlight

# --- AI Logic (Copied directly from your Pygame code) ---
# These functions don't need to change, as they are pure logic.

def evaluate_board(board):
    """
    Simple board evaluation - just counts material.
    Works with the python-chess board.
    """
    piece_values = {
        chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3,
        chess.ROOK: 5, chess.QUEEN: 9, chess.KING: 0
    }
    score = 0
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece:
            value = piece_values[piece.piece_type]
            if piece.color == chess.WHITE:
                score += value
            else:
                score -= value
    return score

def make_ai_move(board):
    """
    Makes a move for the AI (black pieces) using a 1-ply "min" search.
    """
    legal_moves = list(board.legal_moves)
    if not legal_moves:
        return False  # No legal moves

    best_moves = []
    best_score = float('inf')  # AI is 'min' player (black)
    
    for move in legal_moves:
        board.push(move)
        score = evaluate_board(board)
        board.pop()
        
        if score < best_score:
            best_score = score
            best_moves = [move]
        elif score == best_score:
            best_moves.append(move)
    
    if best_moves:
        chosen_move = random.choice(best_moves)
        board.push(chosen_move)
        return True
    
    return False

# --- Tkinter Application Class ---

class ChessApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Tkinter Chess")
        
        # --- Game State ---
        self.board = chess.Board()
        self.selected_square = None
        self.game_over = False

        # --- GUI Elements ---
        # Configure font for chess pieces
        # We find a font that can render the symbols
        self.piece_font = None
        font_families = ['Segoe UI Symbol', 'DejaVu Sans', 'Arial Unicode MS']
        for family in font_families:
            if family in tkfont.families():
                self.piece_font = tkfont.Font(family=family, size=int(SQUARE_SIZE * 0.6))
                break
        
        # Fallback to default font if none are found
        if self.piece_font is None:
            print("Warning: Could not find ideal chess font. Using default.")
            self.piece_font = tkfont.Font(size=int(SQUARE_SIZE * 0.6))

        # Create the canvas
        self.canvas = tk.Canvas(root, width=WIDTH, height=HEIGHT)
        self.canvas.pack()

        # Bind the click event
        self.canvas.bind("<Button-1>", self.on_square_click)

        # Draw the initial board
        self.redraw_board()

    def get_square_from_mouse(self, event):
        """
        Converts mouse click (x, y) to a chess.Square.
        """
        x, y = event.x, event.y
        col = x // SQUARE_SIZE
        row = y // SQUARE_SIZE
        
        # Convert Tkinter (row, col) to a chess.Square
        # We must flip the row: Tkinter (0,0) is top-left, chess 'a1' (rank 0) is bottom-left
        square = chess.square(col, 7 - row)
        return square

    def redraw_board(self):
        """
        Clears the canvas and redraws the entire board,
        including squares, pieces, and highlights.
        """
        self.canvas.delete("all")

        for r in range(ROWS):
            for c in range(COLS):
                # --- Draw the Square ---
                x1, y1 = c * SQUARE_SIZE, r * SQUARE_SIZE
                x2, y2 = x1 + SQUARE_SIZE, y1 + SQUARE_SIZE
                color = LIGHT_SQUARE if (r + c) % 2 == 0 else DARK_SQUARE
                self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="")

                # --- Get the chess.Square index ---
                square = chess.square(c, 7 - r) # Flip row for python-chess

                # --- Draw Highlight ---
                if square == self.selected_square:
                    # Use a thick outline to represent the highlight
                    self.canvas.create_rectangle(x1+2, y1+2, x2-2, y2-2, 
                                                 outline=HIGHLIGHT_COLOR, width=4)

                # --- Draw the Piece ---
                piece = self.board.piece_at(square)
                if piece:
                    symbol = piece.unicode_symbol()
                    # Center the text in the square
                    self.canvas.create_text(x1 + SQUARE_SIZE // 2, 
                                            y1 + SQUARE_SIZE // 2, 
                                            text=symbol, 
                                            font=self.piece_font, 
                                            fill="black")

    def on_square_click(self, event):
        """
        Handles the logic when a square is clicked.
        """
        if self.game_over:
            return # Do nothing if game is over

        # Only allow clicks if it's the human's (White's) turn
        if self.board.turn != chess.WHITE:
            return

        square = self.get_square_from_mouse(event)

        if self.selected_square:
            # --- A piece is already selected, try to move it ---
            
            # Create a move object
            # Check for pawn promotion (default to Queen)
            promotion = None
            piece = self.board.piece_at(self.selected_square)
            if piece and piece.piece_type == chess.PAWN:
                if (chess.square_rank(self.selected_square) == 6 and chess.square_rank(square) == 7):
                    promotion = chess.QUEEN
                    
            move = chess.Move(self.selected_square, square, promotion=promotion)

            if move in self.board.legal_moves:
                # --- Valid Move ---
                self.board.push(move)
                self.selected_square = None
                self.redraw_board()
                
                # Check for game over *after* our move
                if not self.check_game_over():
                    # If game is not over, trigger AI move
                    self.trigger_ai_move()
            
            elif square == self.selected_square:
                # --- Deselect ---
                self.selected_square = None
                self.redraw_board()
            
            else:
                # --- Invalid move, check if it's a new selection ---
                piece_at_click = self.board.piece_at(square)
                if piece_at_click and piece_at_click.color == self.board.turn:
                    self.selected_square = square
                    self.redraw_board()
                else:
                    self.selected_square = None
                    self.redraw_board()
        else:
            # --- No piece is selected, try to select one ---
            piece = self.board.piece_at(square)
            if piece and piece.color == self.board.turn: # Check if it's our piece
                self.selected_square = square
                self.redraw_board()

    def trigger_ai_move(self):
        """
        Uses root.after() to make the AI move without freezing the GUI.
        """
        # Add a small delay so the player's move is visible
        self.root.after(250, self.execute_ai_move) 

    def execute_ai_move(self):
        """
        Calls the AI logic and updates the board.
        """
        if not self.game_over:
            make_ai_move(self.board)
            self.redraw_board()
            # Check for game over *after* AI's move
            self.check_game_over()

    def check_game_over(self):
        """
        Checks if the game has ended and shows a message.
        Returns True if the game is over, False otherwise.
        """
        if self.board.is_game_over():
            self.game_over = True
            result = self.board.result()
            
            if self.board.is_checkmate():
                winner = "White" if self.board.turn == chess.BLACK else "Black"
                message = f"Checkmate! {winner} wins."
            elif self.board.is_stalemate():
                message = "Stalemate! It's a draw."
            else:
                message = f"Game Over! Draw by {result}."
            
            print(message) # Also print to console
            messagebox.showinfo("Game Over", message)
            return True
        return False

# --- Main Execution ---

if __name__ == "__main__":
    root = tk.Tk()
    app = ChessApp(root)
    root.mainloop()