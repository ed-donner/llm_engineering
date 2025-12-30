"""
AI Model Trivia Contest

A trivia game where 1 judge model selects words from domains and 3 player models compete
to guess them. Players earn points for correct guesses, and the first to reach the target score wins.
"""

from openai import OpenAI
from typing import Dict, List, Optional
import random


class AITriviaContest:
    """Main game class for the AI Model Trivia Contest."""
    
    def __init__(
        self,
        judge_model: str = "llama3.1",
        player_models: List[str] = None,
        target_score: int = 100,
        points_per_answer: int = 10,
        max_turns: int = None,
        base_url: str = "http://localhost:11434/v1"
    ):
        """
        Initialize the trivia contest game.
        
        Args:
            judge_model: Ollama model to use as judge (default: "llama3.1")
            player_models: List of 3 Ollama models to use as players
                          (default: ["mistral:latest", "phi3:latest", "gemma3:270m"])
            target_score: Score needed to win (default: 100)
            points_per_answer: Points awarded for correct answer (default: 10)
            max_turns: Maximum number of turns (None = no limit, default: None)
            base_url: Base URL for Ollama API (default: "http://localhost:11434/v1")
        """
        if player_models is None:
            player_models = ["mistral:latest", "phi3:latest", "gemma3:270m"]
        
        if len(player_models) != 3:
            raise ValueError("Must provide exactly 3 player models")
        
        self.judge_model = judge_model
        self.player_models = player_models
        self.target_score = target_score
        self.points_per_answer = points_per_answer
        self.max_turns = max_turns
        self.base_url = base_url
        
        # Initialize OpenAI clients
        self.judge_client = OpenAI(base_url=base_url, api_key='ollama')
        self.player_clients = {
            model: OpenAI(base_url=base_url, api_key='ollama')
            for model in player_models
        }
        
        # Game state
        self.scores = {model: 0 for model in player_models}
        self.turn_number = 0
        self.game_history = {}  # {turn_number: {player_name: guess}}
        self.current_domain = None
        self.current_word = None
        self.current_hint = None
        self.used_words = {}  # {domain: [list of used words]} to avoid repeats
        self.game_over = False
        self.winners = []
        self.game_end_reason = None  # "target_score" or "max_turns"
        
        # Available domains
        self.domains = [
            "geography (cities, countries, landmarks)",
            "animals (common animals, pets, wildlife)",
            "food (fruits, vegetables, dishes)",
            "colors",
            "nature (trees, flowers, natural phenomena)",
            "technology (devices, software, concepts)",
            "sports",
            "music (instruments, genres, artists)"
        ]
    
    def select_domain_and_word(self) -> Dict:
        """
        Judge selects a domain and picks a word from it.
        Ensures different word if domain repeats.
        
        Returns:
            Dictionary with 'domain', 'word', and 'hint'
        """
        # Select domain (can be same or different)
        selected_domain = random.choice(self.domains)
        
        # Initialize domain in used_words if not present
        if selected_domain not in self.used_words:
            self.used_words[selected_domain] = []
        
        # Generate word selection prompt
        used_words_context = ""
        if self.used_words[selected_domain]:
            used_words_context = f"\n\nIMPORTANT: Do NOT select any of these words (already used in this domain): {', '.join(self.used_words[selected_domain])}"
        
        prompt = f"""Select a single, common word from the domain: {selected_domain}.
The word should be:
- A single word (not a phrase)
- Common and well-known
- Appropriate for a trivia game
- Between 3-10 letters long
{used_words_context}

Return ONLY the word, nothing else. Just the word itself."""

        try:
            response = self.judge_client.chat.completions.create(
                model=self.judge_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.8
            )
            word = response.choices[0].message.content.strip()
            # Clean up the word
            word = word.strip('"\'.,!?;:')
            word = word.split()[0] if word.split() else word
            word = word.lower()
            
            # If word was already used, try again with explicit exclusion
            if word in self.used_words[selected_domain]:
                # Force a different word
                exclusion_list = ', '.join(self.used_words[selected_domain] + [word])
                prompt = f"""Select a single, common word from the domain: {selected_domain}.
The word should be:
- A single word (not a phrase)
- Common and well-known
- Appropriate for a trivia game
- Between 3-10 letters long

IMPORTANT: Do NOT select any of these words: {exclusion_list}

Return ONLY the word, nothing else. Just the word itself."""
                
                response = self.judge_client.chat.completions.create(
                    model=self.judge_model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.9
                )
                word = response.choices[0].message.content.strip()
                word = word.strip('"\'.,!?;:')
                word = word.split()[0] if word.split() else word
                word = word.lower()
            
            # Add to used words
            self.used_words[selected_domain].append(word)
            
            # Generate hint
            hint = self.generate_hint(word, selected_domain)
            
            self.current_domain = selected_domain
            self.current_word = word
            self.current_hint = hint
            
            return {
                "domain": selected_domain,
                "word": word,
                "hint": hint
            }
        except Exception as e:
            # Fallback
            word = "paris" if selected_domain.startswith("geography") else "apple"
            hint = f"What is a famous example from {selected_domain}?"
            self.current_domain = selected_domain
            self.current_word = word
            self.current_hint = hint
            return {
                "domain": selected_domain,
                "word": word,
                "hint": hint
            }
    
    def generate_hint(self, word: str, domain: str) -> str:
        """
        Generate a hint for the word using the judge model.
        
        Args:
            word: The word to generate a hint for
            domain: The domain the word belongs to
        
        Returns:
            A hint string
        """
        prompt = f"""Generate a creative, engaging hint for a word guessing game.
The word is: {word}
The domain is: {domain}

Create a hint that is like a riddle or question, such as:
- "What is the capital of France?"
- "What color is the sky?"
- "What do you call a baby cat?"

Make it fun and engaging! Just return the hint question, nothing else."""

        try:
            response = self.judge_client.chat.completions.create(
                model=self.judge_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"What is a famous example from {domain}?"
    
    def player_guess(self, player_model: str, domain: str, hint: str) -> str:
        """
        Have a player model generate a guess based on domain and hint.
        
        Args:
            player_model: The model name to use
            domain: The domain of the word
            hint: The hint provided by the judge
        
        Returns:
            The player's guess
        """
        prompt = f"""You are playing a trivia game! The judge has selected a word from the domain: {domain}

Here's the hint: {hint}

Make a guess! Return ONLY a single word that you think matches the hint and domain. Just the word, nothing else."""

        try:
            client = self.player_clients[player_model]
            response = client.chat.completions.create(
                model=player_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.8
            )
            guess = response.choices[0].message.content.strip()
            # Clean up the guess
            guess = guess.strip('"\'.,!?;:')
            guess = guess.split()[0] if guess.split() else guess
            return guess.lower()
        except Exception as e:
            return "[error generating guess]"
    
    def evaluate_guesses(self, guesses: Dict[str, str]) -> Dict:
        """
        Judge evaluates all player guesses and determines winners.
        
        Args:
            guesses: Dictionary mapping player_model to their guess
        
        Returns:
            Dictionary with evaluation results
        """
        correct_players = []
        
        for player, guess in guesses.items():
            # Normalize for comparison
            if guess.lower().strip() == self.current_word.lower().strip():
                correct_players.append(player)
        
        return {
            "correct_players": correct_players,
            "target_word": self.current_word,
            "all_guesses": guesses
        }
    
    def generate_commentary(self, evaluation: Dict) -> str:
        """
        Judge generates funny commentary based on all guesses in the game.
        
        Args:
            evaluation: The evaluation results from evaluate_guesses
        
        Returns:
            Commentary string
        """
        # Build history context
        history_text = ""
        for turn, turn_guesses in self.game_history.items():
            history_text += f"\nTurn {turn}: "
            for player, guess in turn_guesses.items():
                history_text += f"{player} guessed '{guess}'; "
        
        current_guesses_text = ""
        for player, guess in evaluation["all_guesses"].items():
            current_guesses_text += f"{player} guessed '{guess}'; "
        
        correct_players_text = ", ".join(evaluation["correct_players"]) if evaluation["correct_players"] else "nobody"
        
        prompt = f"""You are a funny, entertaining game show host/judge for an AI trivia contest.
The target word was: {evaluation["target_word"]}
The domain was: {self.current_domain}

Current turn guesses: {current_guesses_text}

Previous game history:
{history_text}

Players who got it correct this turn: {correct_players_text}

Generate a funny, engaging commentary about this turn. Make it entertaining and comment on the guesses (especially funny ones or interesting misses). 
Keep it brief (2-3 sentences). Just return the commentary, nothing else."""

        try:
            response = self.judge_client.chat.completions.create(
                model=self.judge_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.9
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            if evaluation["correct_players"]:
                return f"Great job {', '.join(evaluation['correct_players'])}! You got it right!"
            else:
                return "Nobody got it this time! Keep trying!"
    
    def play_turn(self) -> Dict:
        """
        Execute one turn of the game.
        - Judge selects domain and word
        - Judge generates hint
        - All players guess
        - Judge evaluates and awards points
        - Judge provides commentary
        - Check for winners
        
        Returns:
            Dictionary with turn results
        """
        if self.game_over:
            return {
                "game_over": True,
                "message": "Game is already over!",
                "winners": self.winners
            }
        
        self.turn_number += 1
        
        # Judge selects domain and word
        word_info = self.select_domain_and_word()
        
        # Display turn start and hint
        print("=" * 80)
        print(f"TURN {self.turn_number}")
        print("=" * 80)
        print()
        print(f"📚 Domain: {word_info['domain']}")
        print(f"💡 Hint: {word_info['hint']}")
        print()
        print("-" * 80)
        print("PLAYERS ARE GUESSING...")
        print("-" * 80)
        
        # All players generate guesses (show progress as they guess)
        guesses = {}
        for i, player_model in enumerate(self.player_models, 1):
            print(f"  [{i}/{len(self.player_models)}] {player_model} is thinking...", end=" ", flush=True)
            guess = self.player_guess(
                player_model,
                word_info["domain"],
                word_info["hint"]
            )
            guesses[player_model] = guess
            print(f"→ '{guess}'")
        
        print("-" * 80)
        print("All players have guessed!")
        print()
        
        # Store in history
        self.game_history[self.turn_number] = guesses.copy()
        
        # Judge evaluates
        evaluation = self.evaluate_guesses(guesses)
        
        # Award points
        for player in evaluation["correct_players"]:
            self.scores[player] += self.points_per_answer
        
        # Generate commentary
        commentary = self.generate_commentary(evaluation)
        
        # Check for winners (target score reached)
        winners = [
            player for player, score in self.scores.items()
            if score >= self.target_score
        ]
        
        # Check if max turns reached
        max_turns_reached = False
        if self.max_turns is not None and self.turn_number >= self.max_turns:
            max_turns_reached = True
        
        # Determine winners
        if winners:
            # Winners by reaching target score
            self.game_over = True
            self.winners = winners
            self.game_end_reason = "target_score"
        elif max_turns_reached:
            # Game ended due to max turns - winners are players with highest score
            max_score = max(self.scores.values())
            if max_score > 0:
                self.winners = [
                    player for player, score in self.scores.items()
                    if score == max_score
                ]
            else:
                self.winners = []  # No one scored any points
            self.game_over = True
            self.game_end_reason = "max_turns"
        
        turn_result = {
            "turn_number": self.turn_number,
            "domain": word_info["domain"],
            "word": word_info["word"],
            "hint": word_info["hint"],
            "guesses": guesses,
            "evaluation": evaluation,
            "commentary": commentary,
            "scores": self.scores.copy(),
            "winners": self.winners.copy() if self.game_over else winners,
            "game_over": self.game_over,
            "game_end_reason": self.game_end_reason if self.game_over else None,
            "max_turns_reached": max_turns_reached
        }
        
        # Display full turn results
        self.display_turn_results(turn_result)
        
        return turn_result
    
    def display_turn_results(self, turn_result: Dict):
        """
        Display the results of a turn in a formatted way.
        
        Args:
            turn_result: The result dictionary from play_turn()
        """
        print("-" * 80)
        print("GUESS RESULTS:")
        print("-" * 80)
        for player, guess in turn_result['guesses'].items():
            is_correct = player in turn_result['evaluation']['correct_players']
            status = "✅ CORRECT!" if is_correct else "❌"
            print(f"  {player}: '{guess}' {status}")
        print()
        print("-" * 80)
        print("🎯 JUDGE'S COMMENTARY:")
        print("-" * 80)
        # Format commentary with line breaks for better readability
        commentary = turn_result['commentary']
        # Split by sentence endings and print each sentence on a new line
        import re
        # Split by periods, exclamation marks, or question marks followed by space
        sentences = re.split(r'([.!?])\s+', commentary)
        if len(sentences) > 1:
            # Reconstruct sentences with their punctuation
            formatted_lines = []
            for i in range(0, len(sentences) - 1, 2):
                if i + 1 < len(sentences):
                    sentence = sentences[i].strip() + sentences[i + 1]
                    if sentence.strip():
                        formatted_lines.append(f"  {sentence.strip()}")
            # Add last part if it exists and wasn't paired
            if len(sentences) % 2 == 1 and sentences[-1].strip():
                formatted_lines.append(f"  {sentences[-1].strip()}")
            for line in formatted_lines:
                print(line)
        else:
            # If splitting didn't work, just add line breaks after periods
            formatted = commentary.replace('. ', '.\n  ').replace('! ', '!\n  ').replace('? ', '?\n  ')
            if formatted != commentary:
                print(f"  {formatted}")
            else:
                print(f"  {commentary}")
        print()
        print("-" * 80)
        print("📊 CURRENT SCORES:")
        print("-" * 80)
        for player, score in sorted(turn_result['scores'].items(), key=lambda x: x[1], reverse=True):
            progress = "█" * (score // 10) + "░" * ((self.target_score - score) // 10)
            print(f"  {player}: {score}/{self.target_score} points {progress}")
        print()
        
        if turn_result['winners']:
            print("=" * 80)
            if turn_result.get('game_end_reason') == 'max_turns':
                print("🏆 GAME OVER - MAX TURNS REACHED!")
                print("=" * 80)
                print(f"Maximum turns ({self.max_turns}) reached. Winners determined by highest score:")
                print()
                for winner in turn_result['winners']:
                    print(f"  🎉 {winner} wins with {turn_result['scores'][winner]} points!")
            else:
                print("🏆 GAME OVER - WINNERS!")
                print("=" * 80)
                for winner in turn_result['winners']:
                    print(f"  🎉 {winner} wins with {turn_result['scores'][winner]} points!")
            print("=" * 80)
        else:
            turn_info = f"Turn: {turn_result['turn_number']}"
            if self.max_turns is not None:
                turns_remaining = self.max_turns - turn_result['turn_number']
                turn_info += f" | Turns remaining: {turns_remaining}"
            print(f"Target score: {self.target_score} | {turn_info}")
            print("=" * 80)
    
    def get_status(self) -> Dict:
        """
        Get current game status.
        
        Returns:
            Dictionary with current game state
        """
        status = {
            "scores": self.scores.copy(),
            "turn_number": self.turn_number,
            "game_over": self.game_over,
            "winners": self.winners.copy(),
            "target_score": self.target_score,
            "max_turns": self.max_turns,
            "game_end_reason": self.game_end_reason
        }
        if self.max_turns is not None:
            status["turns_remaining"] = max(0, self.max_turns - self.turn_number)
        return status

