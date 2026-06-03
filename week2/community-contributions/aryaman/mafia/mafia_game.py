"""
Mafia Game

A social deduction game where players have hidden roles and must work together
or against each other to achieve their team's win condition.
"""

from openai import OpenAI
from typing import Dict, List, Optional, Tuple
import random


class MafiaGame:
    """Main game class for the Mafia game."""
    
    ROLES = {
        "MAFIA": "Mafia",
        "DOCTOR": "Doctor",
        "DETECTIVE": "Detective",
        "VILLAGER": "Villager"
    }
    
    def __init__(
        self,
        moderator_model: str = "llama3.1",
        player_models: List[str] = None,
        base_url: str = "http://localhost:11434/v1"
    ):
        """
        Initialize the Mafia game.
        
        Args:
            moderator_model: Ollama model to use as moderator (default: "llama3.1")
            player_models: List of 3 Ollama models to use as players
                          (default: ["mistral:latest", "phi3:latest", "gemma3:270m"])
            base_url: Base URL for Ollama API (default: "http://localhost:11434/v1")
        """
        if player_models is None:
            player_models = ["mistral:latest", "phi3:latest", "gemma3:270m"]
        
        if len(player_models) != 3:
            raise ValueError("Must provide exactly 3 player models")
        
        self.moderator_model = moderator_model
        self.player_models = player_models
        self.base_url = base_url
        
        # Initialize OpenAI clients
        self.moderator_client = OpenAI(base_url=base_url, api_key='ollama')
        self.player_clients = {
            model: OpenAI(base_url=base_url, api_key='ollama')
            for model in player_models
        }
        
        # Game state
        self.roles = {}  # {player_model: role}
        self.living_players = []
        self.eliminated_players = {}  # {player_model: role}
        self.mafia_players = []  # List of Mafia players (they know each other)
        self.game_over = False
        self.winner = None  # "VILLAGERS" or "MAFIA"
        self.phase = "SETUP"  # SETUP, NIGHT, DAY
        self.day_number = 0
        self.night_number = 0
        
        # Conversation history (following day1.ipynb pattern)
        self.public_conversation = []  # Public discussion history
        self.mafia_private_conversation = []  # Mafia private chat
        self.player_conversations = {
            model: [] for model in player_models
        }  # Individual player conversation histories
        
        # Night action tracking
        self.night_actions = {
            "mafia_kill": None,
            "doctor_protect": None,
            "detective_investigate": None
        }
        
        # Day voting
        self.votes = {}
    
    def assign_roles(self):
        """Assign roles randomly to players. In 4-player game: 1 Mafia, 1 Doctor, 1 Detective."""
        if len(self.player_models) != 3:
            raise ValueError("Game requires exactly 3 players")
        
        # Assign roles: 1 Mafia, 1 Doctor, 1 Detective
        roles_to_assign = [self.ROLES["MAFIA"], self.ROLES["DOCTOR"], self.ROLES["DETECTIVE"]]
        random.shuffle(roles_to_assign)
        
        self.roles = {}
        self.mafia_players = []
        
        for i, player in enumerate(self.player_models):
            role = roles_to_assign[i]
            self.roles[player] = role
            if role == self.ROLES["MAFIA"]:
                self.mafia_players.append(player)
        
        self.living_players = self.player_models.copy()
        self.phase = "NIGHT"
        self.night_number = 1
    
    def get_role_info_for_player(self, player: str) -> str:
        """
        Get role information that a player knows.
        Mafia knows other Mafia, others don't know anyone's role.
        """
        player_role = self.roles[player]
        info = f"Your role is: {player_role}\n\n"
        
        if player_role == self.ROLES["MAFIA"]:
            # Mafia knows other Mafia
            other_mafia = [p for p in self.mafia_players if p != player]
            if other_mafia:
                info += f"You are in the Mafia. Your Mafia partner(s): {', '.join(other_mafia)}\n"
            else:
                info += "You are the only Mafia member.\n"
        else:
            # Non-Mafia don't know anyone's role
            info += "You do not know anyone else's role. You must deduce who the Mafia is through gameplay.\n"
        
        info += f"\nLiving players: {', '.join(self.living_players)}\n"
        if self.eliminated_players:
            eliminated_info = ", ".join([f"{p} ({role})" for p, role in self.eliminated_players.items()])
            info += f"Eliminated players: {eliminated_info}\n"
        
        return info
    
    def format_conversation_history(self, conversation: List[Dict]) -> str:
        """Format conversation history for prompts (following day1.ipynb pattern)."""
        if not conversation:
            return "No conversation history yet."
        
        formatted = "The conversation so far:\n"
        for msg in conversation:
            speaker = msg.get("speaker", "Unknown")
            content = msg.get("content", "")
            formatted += f"{speaker}: {content}\n"
        
        return formatted
    
    def moderator_announce(self, message: str) -> str:
        """Have the moderator make an announcement."""
        prompt = f"""You are the Moderator of a Mafia game. You narrate the game events in an engaging, dramatic way.
        
{message}

Respond as the Moderator, announcing this to all players. Keep it brief (2-3 sentences)."""

        try:
            response = self.moderator_client.chat.completions.create(
                model=self.moderator_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7
            )
            announcement = response.choices[0].message.content.strip()
            self.public_conversation.append({"speaker": "Moderator", "content": announcement})
            return announcement
        except Exception as e:
            return f"Moderator: {message}"
    
    def mafia_coordinate_kill(self) -> Optional[str]:
        """Mafia players coordinate privately and decide on a kill target."""
        if not self.mafia_players:
            return None
        
        living_mafia = [p for p in self.mafia_players if p in self.living_players]
        if not living_mafia:
            return None
        
        # Format Mafia private conversation
        mafia_conversation = self.format_conversation_history(self.mafia_private_conversation)
        
        # Get potential targets (all living non-Mafia players)
        potential_targets = [p for p in self.living_players if p not in living_mafia]
        
        if not potential_targets:
            return None
        
        # Ask each Mafia player for their choice
        mafia_choices = {}
        for mafia_player in living_mafia:
            system_prompt = f"""You are a Mafia member in a Mafia game. You work with your Mafia partner(s) to eliminate the Villagers.
Your role: {self.ROLES["MAFIA"]}
Your Mafia partner(s): {', '.join([p for p in living_mafia if p != mafia_player])}

Living players: {', '.join(self.living_players)}
Potential targets (non-Mafia): {', '.join(potential_targets)}

{mafia_conversation}

You must coordinate with your Mafia partner(s) to choose ONE target to kill tonight."""

            user_prompt = f"""You are in the Mafia private chat. You and your partner(s) need to agree on who to kill tonight.

{mafia_conversation}

Potential targets: {', '.join(potential_targets)}

Respond with ONLY the name of the player you want to kill (choose from: {', '.join(potential_targets)}). Just the player name, nothing else."""

            try:
                client = self.player_clients[mafia_player]
                response = client.chat.completions.create(
                    model=mafia_player,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.8
                )
                choice = response.choices[0].message.content.strip()
                # Clean up the choice
                choice = choice.strip('"\'.,!?;:')
                # Try to match to a player name
                for target in potential_targets:
                    if target.lower() in choice.lower() or choice.lower() in target.lower():
                        mafia_choices[mafia_player] = target
                        break
                else:
                    # Default to first target if no match
                    mafia_choices[mafia_player] = potential_targets[0]
                
                # Add to private conversation
                self.mafia_private_conversation.append({
                    "speaker": mafia_player,
                    "content": f"I vote to kill {mafia_choices[mafia_player]}"
                })
            except Exception as e:
                # Default choice
                mafia_choices[mafia_player] = potential_targets[0]
        
        # Majority vote (or first choice if only one Mafia)
        if len(living_mafia) == 1:
            target = mafia_choices[living_mafia[0]]
        else:
            # Count votes
            vote_counts = {}
            for choice in mafia_choices.values():
                vote_counts[choice] = vote_counts.get(choice, 0) + 1
            target = max(vote_counts.items(), key=lambda x: x[1])[0]
        
        self.night_actions["mafia_kill"] = target
        return target
    
    def doctor_protect(self) -> Optional[str]:
        """Doctor chooses a player to protect."""
        doctor = None
        for player, role in self.roles.items():
            if role == self.ROLES["DOCTOR"] and player in self.living_players:
                doctor = player
                break
        
        if not doctor:
            return None
        
        potential_targets = [p for p in self.living_players if p != doctor]
        
        system_prompt = f"""You are the Doctor in a Mafia game. Each night, you can protect one player from being killed by the Mafia.
Your role: {self.ROLES["DOCTOR"]}
Living players: {', '.join(self.living_players)}

If the Mafia tries to kill the player you protect, they will survive."""

        user_prompt = f"""It is night. The Mafia will try to kill someone. You must choose one player to protect.

Living players (you cannot protect yourself): {', '.join(potential_targets)}

Respond with ONLY the name of the player you want to protect. Just the player name, nothing else."""

        try:
            client = self.player_clients[doctor]
            response = client.chat.completions.create(
                model=doctor,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7
            )
            choice = response.choices[0].message.content.strip()
            choice = choice.strip('"\'.,!?;:')
            
            # Match to a player
            for target in potential_targets:
                if target.lower() in choice.lower() or choice.lower() in target.lower():
                    self.night_actions["doctor_protect"] = target
                    return target
            
            # Default
            self.night_actions["doctor_protect"] = potential_targets[0]
            return potential_targets[0]
        except Exception as e:
            if potential_targets:
                self.night_actions["doctor_protect"] = potential_targets[0]
                return potential_targets[0]
            return None
    
    def detective_investigate(self) -> Tuple[Optional[str], Optional[str]]:
        """Detective chooses a player to investigate."""
        detective = None
        for player, role in self.roles.items():
            if role == self.ROLES["DETECTIVE"] and player in self.living_players:
                detective = player
                break
        
        if not detective:
            return None, None
        
        potential_targets = [p for p in self.living_players if p != detective]
        
        system_prompt = f"""You are the Detective in a Mafia game. Each night, you can investigate one player to learn if they are Mafia or not.
Your role: {self.ROLES["DETECTIVE"]}
Living players: {', '.join(self.living_players)}"""

        user_prompt = f"""It is night. You must choose one player to investigate.

Living players (you cannot investigate yourself): {', '.join(potential_targets)}

Respond with ONLY the name of the player you want to investigate. Just the player name, nothing else."""

        try:
            client = self.player_clients[detective]
            response = client.chat.completions.create(
                model=detective,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7
            )
            choice = response.choices[0].message.content.strip()
            choice = choice.strip('"\'.,!?;:')
            
            # Match to a player
            for target in potential_targets:
                if target.lower() in choice.lower() or choice.lower() in target.lower():
                    investigated = target
                    # Check if they are Mafia
                    is_mafia = self.roles[investigated] == self.ROLES["MAFIA"]
                    result = "Mafia" if is_mafia else "Villager"
                    self.night_actions["detective_investigate"] = (investigated, result)
                    return investigated, result
            
            # Default
            if potential_targets:
                investigated = potential_targets[0]
                is_mafia = self.roles[investigated] == self.ROLES["MAFIA"]
                result = "Mafia" if is_mafia else "Villager"
                self.night_actions["detective_investigate"] = (investigated, result)
                return investigated, result
            
            return None, None
        except Exception as e:
            if potential_targets:
                investigated = potential_targets[0]
                is_mafia = self.roles[investigated] == self.ROLES["MAFIA"]
                result = "Mafia" if is_mafia else "Villager"
                self.night_actions["detective_investigate"] = (investigated, result)
                return investigated, result
            return None, None
    
    def execute_night_phase(self) -> Dict:
        """Execute the night phase: Mafia kill, Doctor protect, Detective investigate."""
        self.phase = "NIGHT"
        self.night_number += 1
        
        # Reset night actions
        self.night_actions = {
            "mafia_kill": None,
            "doctor_protect": None,
            "detective_investigate": None
        }
        
        # Announce night
        announcement = self.moderator_announce(f"Night {self.night_number} has fallen. Everyone close your eyes.")
        print(f"\n{announcement}\n")
        
        # Mafia coordinates kill
        kill_target = self.mafia_coordinate_kill()
        print(f"🔪 Mafia has chosen their target...")
        
        # Doctor protects
        protect_target = self.doctor_protect()
        if protect_target:
            print(f"💊 Doctor has chosen to protect someone...")
        
        # Detective investigates
        investigated, investigation_result = self.detective_investigate()
        if investigated:
            print(f"🔍 Detective has investigated someone...")
            # Store investigation result for detective (private info)
            if investigated not in self.player_conversations:
                self.player_conversations[investigated] = []
            # Add to detective's private knowledge
            detective = None
            for player, role in self.roles.items():
                if role == self.ROLES["DETECTIVE"] and player in self.living_players:
                    detective = player
                    break
            if detective:
                self.player_conversations[detective].append({
                    "speaker": "System",
                    "content": f"[PRIVATE] You investigated {investigated}. They are: {investigation_result}"
                })
        
        # Resolve actions
        eliminated = None
        if kill_target:
            if kill_target == protect_target:
                # Kill prevented
                announcement = self.moderator_announce(
                    f"The Mafia tried to kill {kill_target}, but they were protected by the Doctor!"
                )
                print(f"\n{announcement}\n")
            else:
                # Kill succeeds
                eliminated = kill_target
                eliminated_role = self.roles[eliminated]
                self.eliminate_player(eliminated, eliminated_role)
                announcement = self.moderator_announce(
                    f"Tragedy strikes! {eliminated} has been eliminated by the Mafia. Their role was: {eliminated_role}"
                )
                print(f"\n{announcement}\n")
        
        return {
            "phase": "NIGHT",
            "night_number": self.night_number,
            "kill_target": kill_target,
            "protect_target": protect_target,
            "investigated": investigated,
            "investigation_result": investigation_result if investigated else None,
            "eliminated": eliminated,
            "eliminated_role": self.roles.get(eliminated) if eliminated else None
        }
    
    def eliminate_player(self, player: str, role: str):
        """Remove a player from the game."""
        if player in self.living_players:
            self.living_players.remove(player)
        self.eliminated_players[player] = role
    
    def player_discuss(self, player: str) -> str:
        """Have a player participate in public discussion."""
        if player not in self.living_players:
            return ""
        
        player_role = self.roles[player]
        role_info = self.get_role_info_for_player(player)
        conversation_history = self.format_conversation_history(self.public_conversation)
        
        # Get detective's investigation results if they are the detective
        detective_info = ""
        if player_role == self.ROLES["DETECTIVE"]:
            for msg in self.player_conversations.get(player, []):
                if "[PRIVATE]" in msg.get("content", ""):
                    detective_info += "\n" + msg["content"] + "\n"
        
        system_prompt = f"""You are playing Mafia, a social deduction game. You are {player}.
{role_info}

You are in the public discussion phase. You can accuse, defend, share information (or lie), and try to figure out who the Mafia is.
Your goal: If you are a Villager, Doctor, or Detective, eliminate the Mafia. If you are Mafia, eliminate the Villagers without being caught.

{conversation_history}

Be strategic. You can share information, accuse others, or defend yourself. Keep your response to 2-3 sentences."""

        user_prompt = f"""You are {player} in the public discussion.

{conversation_history}

{detective_info}

What do you want to say in the discussion? Respond as {player}."""

        try:
            client = self.player_clients[player]
            response = client.chat.completions.create(
                model=player,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.8
            )
            statement = response.choices[0].message.content.strip()
            self.public_conversation.append({"speaker": player, "content": statement})
            self.player_conversations[player].append({"speaker": player, "content": statement})
            return statement
        except Exception as e:
            return f"{player}: [Error generating response]"
    
    def player_vote(self, player: str) -> Optional[str]:
        """Have a player vote to eliminate someone."""
        if player not in self.living_players:
            return None
        
        potential_targets = [p for p in self.living_players if p != player]
        if not potential_targets:
            return None
        
        player_role = self.roles[player]
        role_info = self.get_role_info_for_player(player)
        conversation_history = self.format_conversation_history(self.public_conversation)
        
        # Get detective's investigation results if they are the detective
        detective_info = ""
        if player_role == self.ROLES["DETECTIVE"]:
            for msg in self.player_conversations.get(player, []):
                if "[PRIVATE]" in msg.get("content", ""):
                    detective_info += "\n" + msg["content"] + "\n"
        
        system_prompt = f"""You are playing Mafia, a social deduction game. You are {player}.
{role_info}

It is time to vote. You must vote to eliminate one player you suspect is Mafia.

{conversation_history}

{detective_info}

Vote strategically based on the discussion and your knowledge."""

        user_prompt = f"""You are {player}. It is voting time.

{conversation_history}

{detective_info}

You must vote to eliminate one player. Choose from: {', '.join(potential_targets)}

Respond with ONLY the name of the player you want to eliminate. Just the player name, nothing else."""

        try:
            client = self.player_clients[player]
            response = client.chat.completions.create(
                model=player,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7
            )
            choice = response.choices[0].message.content.strip()
            choice = choice.strip('"\'.,!?;:')
            
            # Match to a player
            for target in potential_targets:
                if target.lower() in choice.lower() or choice.lower() in target.lower():
                    self.votes[player] = target
                    return target
            
            # Default
            if potential_targets:
                self.votes[player] = potential_targets[0]
                return potential_targets[0]
            
            return None
        except Exception as e:
            if potential_targets:
                self.votes[player] = potential_targets[0]
                return potential_targets[0]
            return None
    
    def execute_day_phase(self) -> Dict:
        """Execute the day phase: discussion and voting."""
        self.phase = "DAY"
        self.day_number += 1
        
        # Announce day
        announcement = self.moderator_announce(f"Day {self.day_number} has come. The sun rises.")
        print(f"\n{announcement}\n")
        
        # Public discussion - each player speaks
        print("-" * 80)
        print("PUBLIC DISCUSSION:")
        print("-" * 80)
        for player in self.living_players:
            statement = self.player_discuss(player)
            print(f"{player}: {statement}\n")
        
        # Voting
        print("-" * 80)
        print("VOTING:")
        print("-" * 80)
        self.votes = {}
        for player in self.living_players:
            vote = self.player_vote(player)
            if vote:
                print(f"{player} votes to eliminate: {vote}")
        
        # Count votes
        vote_counts = {}
        for voter, target in self.votes.items():
            vote_counts[target] = vote_counts.get(target, 0) + 1
        
        if vote_counts:
            # Find player with most votes
            eliminated = max(vote_counts.items(), key=lambda x: x[1])[0]
            eliminated_role = self.roles[eliminated]
            self.eliminate_player(eliminated, eliminated_role)
            
            announcement = self.moderator_announce(
                f"By majority vote, {eliminated} has been eliminated. Their role was: {eliminated_role}"
            )
            print(f"\n{announcement}\n")
            print(f"Vote counts: {vote_counts}")
        else:
            eliminated = None
            eliminated_role = None
            announcement = self.moderator_announce("No one received enough votes to be eliminated.")
            print(f"\n{announcement}\n")
        
        return {
            "phase": "DAY",
            "day_number": self.day_number,
            "discussion": self.public_conversation[-len(self.living_players):] if self.living_players else [],
            "votes": self.votes.copy(),
            "vote_counts": vote_counts if vote_counts else {},
            "eliminated": eliminated,
            "eliminated_role": eliminated_role
        }
    
    def check_win_condition(self) -> Optional[str]:
        """Check if a win condition has been met. Returns 'VILLAGERS', 'MAFIA', or None."""
        living_mafia = [p for p in self.mafia_players if p in self.living_players]
        living_villagers = [p for p in self.living_players if p not in living_mafia]
        
        # Villagers win: all Mafia eliminated
        if not living_mafia:
            return "VILLAGERS"
        
        # Mafia win: Mafia count >= Villager count
        if len(living_mafia) >= len(living_villagers):
            return "MAFIA"
        
        return None
    
    def get_game_status(self) -> Dict:
        """Get current game status."""
        return {
            "phase": self.phase,
            "day_number": self.day_number,
            "night_number": self.night_number,
            "living_players": self.living_players.copy(),
            "eliminated_players": dict(self.eliminated_players),
            "roles": {p: r for p, r in self.roles.items() if p not in self.living_players},  # Only reveal eliminated roles
            "game_over": self.game_over,
            "winner": self.winner
        }

