"""
Conversation Context Management
Handles session-based conversation history and context for follow-up questions.
Now with persistent storage using SQLite.
"""

from typing import Dict, Optional, List
from datetime import datetime, timedelta
import json
from pathlib import Path

from app.models import ConversationSession, ConversationTurn
from app.diagnostics import get_logger
from app.conversation_storage import get_conversation_storage

logger = get_logger(__name__)

class ConversationManager:
    """Manages conversation sessions and context with persistent storage"""
    
    def __init__(self):
        self.sessions: Dict[str, ConversationSession] = {}  # In-memory cache
        self.storage = get_conversation_storage()  # Persistent storage
        self.max_session_age_hours = 24  # Auto-cleanup after 24 hours
        self.max_turns_per_session = 50  # Limit memory usage
        logger.info("ConversationManager initialized with persistent storage")
        
    def get_or_create_session(self, session_id: str) -> ConversationSession:
        """Get existing session or create new one (with persistent storage)"""
        # Check in-memory cache first
        if session_id not in self.sessions:
            # Try to load from persistent storage
            stored_session = self.storage.get_session(session_id)
            
            if stored_session:
                # Load turns from storage
                stored_turns = self.storage.get_session_turns(session_id)
                
                # Reconstruct ConversationSession object
                session = ConversationSession(
                    session_id=session_id,
                    created_at=datetime.fromisoformat(stored_session["created_at"]),
                    last_active=datetime.fromisoformat(stored_session["last_active"])
                )
                
                # Add turns
                for turn_data in stored_turns:
                    turn = ConversationTurn(
                        turn_id=turn_data["turn_id"],
                        query=turn_data["query"],
                        response=turn_data["response"],
                        timestamp=datetime.fromisoformat(turn_data["timestamp"]),
                        sources=turn_data.get("sources", [])
                    )
                    session.turns.append(turn)
                
                self.sessions[session_id] = session
                logger.info(f"Loaded session {session_id} from storage with {len(session.turns)} turns")
            else:
                # Create new session
                session = ConversationSession(
                    session_id=session_id,
                    created_at=datetime.now(),
                    last_active=datetime.now()
                )
                self.sessions[session_id] = session
                
                # Persist to storage
                self.storage.save_session(
                    session_id=session_id,
                    created_at=session.created_at,
                    last_active=session.last_active
                )
                logger.info(f"Created new conversation session: {session_id}")
        else:
            # Update last active time
            self.sessions[session_id].last_active = datetime.now()
            # Persist update
            self.storage.save_session(
                session_id=session_id,
                created_at=self.sessions[session_id].created_at,
                last_active=self.sessions[session_id].last_active
            )
            
        return self.sessions[session_id]
    
    def add_turn(self, session_id: str, turn_id: str, query: str, response: str, sources: List[Dict] = None):
        """Add a conversation turn to the session (with persistent storage)"""
        session = self.get_or_create_session(session_id)
        session.add_turn(turn_id, query, response, sources or [])
        
        # Persist to storage
        turn = session.turns[-1]  # Get the turn we just added
        self.storage.save_turn(
            session_id=session_id,
            turn_id=turn_id,
            query=query,
            response=response,
            timestamp=turn.timestamp,
            sources=sources
        )
        
        # Limit the number of turns in memory to prevent memory issues
        if len(session.turns) > self.max_turns_per_session:
            # Keep only the most recent turns in memory
            # (all turns are still in persistent storage)
            session.turns = session.turns[-self.max_turns_per_session:]
        
        logger.info(f"Added turn to session {session_id}: {len(session.turns)} turns in memory, persisted to storage")
    
    def get_context_for_query(self, session_id: str, max_turns: int = 5) -> str:
        """Get conversation context for LLM processing"""
        if session_id not in self.sessions:
            return ""
        
        session = self.sessions[session_id]
        return session.get_context_for_llm(max_turns)
    
    def clear_session_context(self, session_id: str) -> bool:
        """Clear conversation history for a session (memory and storage)"""
        # Remove from memory
        if session_id in self.sessions:
            del self.sessions[session_id]
        
        # Remove from persistent storage
        deleted = self.storage.delete_session(session_id)
        
        if deleted:
            logger.info(f"Cleared context for session: {session_id}")
        return deleted
    
    def get_session_info(self, session_id: str) -> Optional[Dict]:
        """Get information about a session (from storage if not in memory)"""
        if session_id in self.sessions:
            session = self.sessions[session_id]
            return {
                "session_id": session_id,
                "turn_count": len(session.turns),
                "created_at": session.created_at.isoformat(),
                "last_active": session.last_active.isoformat()
            }
        
        # Try loading from storage
        return self.storage.get_session(session_id)
    
    def get_session_turns(self, session_id: str) -> Optional[List[Dict]]:
        """Get conversation turns for a session (from storage for complete history)"""
        # Always get from storage for complete history
        turns = self.storage.get_session_turns(session_id)
        return turns if turns else None
    
    def cleanup_old_sessions(self):
        """Remove sessions that are too old (memory and storage)"""
        # Clean up in-memory sessions
        cutoff_time = datetime.now() - timedelta(hours=self.max_session_age_hours)
        old_sessions = [
            session_id for session_id, session in self.sessions.items()
            if session.last_active < cutoff_time
        ]
        
        for session_id in old_sessions:
            del self.sessions[session_id]
            logger.info(f"Cleaned up old session from memory: {session_id}")
        
        if old_sessions:
            logger.info(f"Cleaned up {len(old_sessions)} old sessions from memory")
        
        # Clean up in persistent storage (30 days)
        deleted_count = self.storage.delete_old_sessions(days=30)
        if deleted_count > 0:
            logger.info(f"Cleaned up {deleted_count} old sessions from storage")
    
    def get_all_sessions(self) -> List[Dict]:
        """Get information about all sessions (from storage for complete list)"""
        return self.storage.get_all_sessions()
    
    def search_conversations(self, search_query: str, limit: int = 50) -> List[Dict]:
        """
        Search across all conversations for matching text.
        
        Args:
            search_query: Text to search for
            limit: Maximum number of results
            
        Returns:
            List of matching turns with session info
        """
        return self.storage.search_conversations(search_query, limit)
    
    def get_storage_stats(self) -> Dict:
        """Get statistics about conversation storage"""
        return self.storage.get_stats()
    
    async def generate_title_for_session(self, session_id: str, llm_service) -> Optional[str]:
        """
        Generate a concise title for a conversation based on its content.
        
        Args:
            session_id: Session to generate title for
            llm_service: LLM service instance
            
        Returns:
            Generated title or None if failed
        """
        # Get first few turns from the conversation
        turns = self.storage.get_session_turns(session_id, limit=3)
        
        if not turns:
            return None
        
        # Build context from first turns
        context_parts = []
        for i, turn in enumerate(turns[:2]):  # Use first 2 turns max
            context_parts.append(f"User: {turn['query']}")
            if i == 0:  # Only include first response
                context_parts.append(f"Assistant: {turn['response'][:200]}")  # Truncate response
        
        context = "\n".join(context_parts)
        
        # Create prompt for title generation
        prompt = f"""You are a title generator. Your task is to create a short, descriptive title for a conversation.

Read this conversation and generate a title that captures its main topic:

{context}

Generate a concise title (3-6 words maximum). Output ONLY the title text, nothing else. Do not include quotes, explanations, or any other text.

Title:"""

        try:
            from app.llm import GenerationRequest
            
            # Generate title using LLM
            request = GenerationRequest(prompt=prompt)
            result = await llm_service.generate(request, conversation_context="")
            
            # Clean up the title
            title = result.text.strip()
            
            # Remove quotes if present
            if title.startswith('"') and title.endswith('"'):
                title = title[1:-1]
            if title.startswith("'") and title.endswith("'"):
                title = title[1:-1]
            
            # Limit length
            if len(title) > 60:
                title = title[:57] + "..."
            
            # Update in storage
            self.storage.update_session_title(session_id, title)
            
            logger.info(f"Generated title for session {session_id}: {title}")
            return title
            
        except Exception as e:
            logger.error(f"Failed to generate title for session {session_id}: {e}")
            return None

# Global conversation manager instance
conversation_manager = ConversationManager()

def get_conversation_manager() -> ConversationManager:
    """Get the global conversation manager instance"""
    return conversation_manager
