"""
Mastermind Game - Core game logic and UI components
"""

import random
import gradio as gr

class MastermindGame:
    """Core game logic for Mastermind"""
    
    COLORS = ["Red", "Blue", "Green", "Yellow", "Orange", "Purple"]
    COLOR_HEX = {
        "Red": "#dc3545",
        "Blue": "#0d6efd",
        "Green": "#198754",
        "Yellow": "#ffc107",
        "Orange": "#fd7e14",
        "Purple": "#6f42c1"
    }
    
    def __init__(self, code_length=4, max_guesses=10):
        self.code_length = code_length
        self.max_guesses = max_guesses
        self.secret_code = []
        self.guesses = []
        self.feedback = []
        self.game_over = False
        self.won = False
        
    def start_new_game(self):
        """Initialize a new game"""
        self.secret_code = random.choices(self.COLORS, k=self.code_length)
        self.guesses = []
        self.feedback = []
        self.game_over = False
        self.won = False
        return "New game started! Select your colors!"
    
    def make_guess(self, guess):
        """Process a guess and return feedback"""
        if self.game_over:
            return "Game is over! Start a new game."
        
        if len(guess) != self.code_length or None in guess or "" in guess:
            return f"Please select all {self.code_length} colors!"
        
        # Calculate feedback
        black_pegs = sum(1 for i in range(self.code_length) if guess[i] == self.secret_code[i])
        
        # For white pegs, count remaining colors
        secret_remaining = list(self.secret_code)
        guess_remaining = list(guess)
        
        # Remove exact matches
        for i in range(self.code_length - 1, -1, -1):
            if guess[i] == self.secret_code[i]:
                secret_remaining.pop(i)
                guess_remaining.pop(i)
        
        # Count color matches in wrong positions
        white_pegs = 0
        for color in guess_remaining:
            if color in secret_remaining:
                white_pegs += 1
                secret_remaining.remove(color)
        
        self.guesses.append(guess)
        self.feedback.append({"black": black_pegs, "white": white_pegs})
        
        # Check win condition
        if black_pegs == self.code_length:
            self.game_over = True
            self.won = True
            return f"🎉 Congratulations! You cracked the code in {len(self.guesses)} guesses!"
        
        # Check lose condition
        if len(self.guesses) >= self.max_guesses:
            self.game_over = True
            return f"💔 Game Over! The secret code was: {', '.join(self.secret_code)}"
        
        return f"Guess {len(self.guesses)}/{self.max_guesses} - Keep going!"
    
    def get_game_state_summary(self):
        """Return a text summary of the current game state"""
        summary = f"Game State: Guess {len(self.guesses)}/{self.max_guesses}\n"
        summary += f"Available colors: {', '.join(self.COLORS)}\n\n"
        
        if self.guesses:
            summary += "Previous Guesses:\n"
            for idx, (guess, feedback) in enumerate(zip(self.guesses, self.feedback)):
                summary += f"  Guess {idx + 1}: {guess}\n"
                summary += f"  Feedback: {feedback['black']} black, {feedback['white']} white\n\n"
        else:
            summary += "No previous guesses yet.\n"
        
        return summary
    
def create_game_board_html(game, current_guess, status=""):
    html = f"""
    <div id='mastermind-board' class='mastermind-board'>
         <div id='status-line'>
            {status}
            <div class="current-guess-title">
    """
    if game.won:
        html += f'Won in {len(game.guesses)} guesses!'
    elif game.game_over:
        html += 'Game Over'
    else:
        html += f'🎯 Guess {len(game.guesses)}/{game.max_guesses}'
        
    html += """
        </div>
    """
        
    
    # Current Guess Section (only if game not over)
    if not game.game_over:
        html += """
        <div class="current-guess-section">
            <div class="current-guess-title">Your Current Guess</div>
            <div class="current-guess-pegs">
        """
        
        for i in range(4):
            if current_guess[i]:
                color_hex = game.COLOR_HEX[current_guess[i]]
                html += f'<div class="current-peg filled" style="background-color: {color_hex};"><div class="position-label">{i+1}</div></div>'
            else:
                html += f'<div class="current-peg">?<div class="position-label">{i+1}</div></div>'
        
        html += """
            </div>
        </div>
        """
    
    # History Section
    html += """
        <div class="guess-history">
            <div class="history-title">📋 GUESS HISTORY</div>
    """
    
    if not game.guesses:
        html += '<div class="no-guesses">No guesses yet. Select colors below!</div>'
    else:
        for idx in range(len(game.guesses) - 1, -1, -1):
            guess = game.guesses[idx]
            feedback = game.feedback[idx]
            
            html += '<div class="guess-row">'
            html += f'<div class="guess-number">#{idx + 1}</div>'
            html += '<div class="pegs-container">'
            
            for color in guess:
                color_hex = game.COLOR_HEX[color]
                html += f'<div class="peg" style="background-color: {color_hex};"></div>'
            
            html += f'</div><div class="feedback">⚫ {feedback["black"]} &nbsp; ⚪ {feedback["white"]}</div>'
            html += '</div>'
    
    html += '</div>'
    
    # Secret Code Section
    html += '<div class="secret-section">'
    html += '<div class="secret-title">🔒 SECRET CODE</div>'
    html += '<div class="secret-pegs">'
    
    if game.game_over:
        for color in game.secret_code:
            color_hex = game.COLOR_HEX[color]
            html += f'<div class="peg" style="background-color: {color_hex};"></div>'
    else:
        for _ in range(game.code_length):
            html += '<div class="peg peg-hidden">?</div>'
    
    html += '</div></div></div><div>'
    
    return html
    
def load_css(path: str) -> str:
    with open(path, "r") as f:
        return f"<style>{f.read()}</style>"