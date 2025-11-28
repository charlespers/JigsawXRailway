"""
Conversation Manager
Maintains conversation state and design context per session
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import uuid


class ConversationManager:
    """Manages conversation state and design context."""
    
    def __init__(self):
        """Initialize conversation manager."""
        # In-memory storage (can be replaced with database later)
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.design_states: Dict[str, Dict[str, Any]] = {}
    
    def create_session(self, session_id: Optional[str] = None) -> str:
        """
        Create a new conversation session.
        
        Args:
            session_id: Optional session ID (generates new if not provided)
        
        Returns:
            Session ID
        """
        if not session_id:
            session_id = str(uuid.uuid4())
        
        self.sessions[session_id] = {
            "session_id": session_id,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "messages": [],
            "design_id": None,
        }
        
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session by ID."""
        return self.sessions.get(session_id)
    
    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Add a message to conversation history.
        
        Args:
            session_id: Session ID
            role: "user" | "assistant" | "system"
            content: Message content
            metadata: Optional metadata (query classification, etc.)
        
        Returns:
            True if successful
        """
        if session_id not in self.sessions:
            return False
        
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        
        self.sessions[session_id]["messages"].append(message)
        self.sessions[session_id]["updated_at"] = datetime.now().isoformat()
        
        return True
    
    def get_conversation_history(self, session_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get conversation history for session."""
        if session_id not in self.sessions:
            return []
        
        messages = self.sessions[session_id]["messages"]
        if limit:
            return messages[-limit:]
        return messages
    
    def link_design(self, session_id: str, design_id: str) -> bool:
        """Link a design to a conversation session."""
        if session_id not in self.sessions:
            return False
        
        self.sessions[session_id]["design_id"] = design_id
        return True
    
    def get_design_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get design state for session."""
        if session_id not in self.sessions:
            return None
        
        design_id = self.sessions[session_id].get("design_id")
        if not design_id:
            return None
        
        return self.design_states.get(design_id)
    
    def save_design_state(self, session_id: str, design_state: Dict[str, Any]) -> str:
        """
        Save design state and link to session.
        
        Args:
            session_id: Session ID
            design_state: Design state dictionary
        
        Returns:
            Design ID
        """
        # Generate design ID if not present
        design_id = design_state.get("design_id")
        if not design_id:
            design_id = str(uuid.uuid4())
            design_state["design_id"] = design_id
        
        # Save design state
        design_state["updated_at"] = datetime.now().isoformat()
        self.design_states[design_id] = design_state
        
        # Link to session
        self.link_design(session_id, design_id)
        
        return design_id
    
    def update_design_state(self, design_id: str, updates: Dict[str, Any]) -> bool:
        """Update design state with partial updates."""
        if design_id not in self.design_states:
            return False
        
        self.design_states[design_id].update(updates)
        self.design_states[design_id]["updated_at"] = datetime.now().isoformat()
        return True
    
    def has_existing_design(self, session_id: str) -> bool:
        """Check if session has an existing design."""
        if session_id not in self.sessions:
            return False
        
        design_id = self.sessions[session_id].get("design_id")
        return design_id is not None and design_id in self.design_states
    
    def clear_session(self, session_id: str) -> bool:
        """Clear a session (but keep design state)."""
        if session_id not in self.sessions:
            return False
        
        # Clear messages but keep design link
        self.sessions[session_id]["messages"] = []
        self.sessions[session_id]["updated_at"] = datetime.now().isoformat()
        return True
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session and optionally its design state."""
        if session_id not in self.sessions:
            return False
        
        design_id = self.sessions[session_id].get("design_id")
        del self.sessions[session_id]
        
        # Optionally delete design state (for now, keep it)
        # if design_id and design_id in self.design_states:
        #     del self.design_states[design_id]
        
        return True

