from dataclasses import dataclass
from tokenize import String
from typing import List, Optional
from openai import OpenAI

def noop(*args, **kwargs):
    pass

@dataclass
class ConversationMessage:
    """
    Represents a single message in the multi-party conversation.
    """
    speaker: str 
    content: str
    role: str = "user"


class Character:
    """
    Represents an LLM-backed character in the conversation.
    """

    def __init__(
        self,
        name: str,
        system_prompt: str,
        client: OpenAI,
        model: str = "gpt-4.1-mini",
        emit=None
    ) -> None:
        """
        :param name: A human-readable name for the character (speaker label).
        :param system_prompt: System prompt that defines the character's behavior.
        :param client: An initialized OpenAI client instance.
        :param model: Model name to use for this character.
        """
        self.name = name
        self.system_prompt = system_prompt
        self.client = client
        self.model = model
        self.emit = emit or noop

    def _build_user_prompt(self, messages: List[ConversationMessage]) -> str:
        """
        Turn the existing conversation messages into a single user prompt that
        clearly identifies who said what.
        """
        lines = []
        for msg in messages:
            lines.append(f"{msg.speaker}: {msg.content}")
        history_text = "\n".join(lines)

        prompt = (
            "Here is the conversation so far:\n\n"
            f"{history_text}\n\n"
            f"You are {self.name}. Reply with your next message in this conversation."
        )
        return prompt

    def respond(
        self,
        conversation_messages: List[ConversationMessage],
        conversation_system_prompt: Optional[str] = None,
    ) -> ConversationMessage:
        """
        Generate this character's next message given the entire conversation so far.
        Returns a new ConversationMessage instance.
        """
        if conversation_system_prompt:
            system_content = (
                conversation_system_prompt.strip() + "\n\n" + self.system_prompt.strip()
            )
        else:
            system_content = self.system_prompt.strip()

        user_prompt = self._build_user_prompt(conversation_messages)

        self.emit(user_prompt)
        completion = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_content},
                {"role": "user", "content": user_prompt},
            ],
        )

        reply_text = completion.choices[0].message.content.strip()

        return ConversationMessage(
            speaker=self.name,
            content=reply_text,
            role="assistant",
        )


class Conversation:
    """
    Manages a multi-character conversation and runs round-robin turns.
    """

    def __init__(self, system_prompt: str, characters: List[Character], emit=None) -> None:
        """
        :param system_prompt: System prompt describing the overall conversation context.
        :param characters: List of Character instances that take part in the conversation.
        """
        if not characters:
            raise ValueError("Conversation must be constructed with at least one Character.")

        self.system_prompt = system_prompt
        self.characters = characters
        self.messages: List[ConversationMessage] = []
        self._round_start_index = 0  # which character starts the next round
        self.emit = emit or noop 

    def add_message(
        self,
        speaker: str,
        content: str,
        role: str = "user",
    ):
        """
        Add an external or initial message into the conversation.
        Useful for seeding the dialogue.
        """
        msg = ConversationMessage(speaker=speaker, content=content, role=role)
        self.messages.append(msg)  
        self.emit(f"message: {msg.content}")      

    def round(self) -> List[ConversationMessage]:
        """
        Execute one 'round' of the conversation.

        Each character gets exactly one turn to respond, in round-robin order.
        Across successive calls to `round()`, the *starting* character rotates,
        so everyone gets a chance to lead.

        Returns the list of new messages generated in this round.
        """
        new_messages: List[ConversationMessage] = []
        num_chars = len(self.characters)

        indices = [
            (self._round_start_index + offset) % num_chars
            for offset in range(num_chars)
        ]

        for idx in indices:
            character = self.characters[idx]
            reply = character.respond(
                conversation_messages=self.messages,
                conversation_system_prompt=self.system_prompt,
            )
            self.emit(f"response from {character.name}: {reply.content}")
            self.messages.append(reply)
            new_messages.append(reply)

        # Advance the starting index for the next round
        self._round_start_index = (self._round_start_index + 1) % num_chars

        return new_messages
