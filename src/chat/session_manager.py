"""
Session management for conversational AI chat interactions.

Handles user sessions, conversation history, and context persistence
for natural language queries about firmware analysis.
"""

import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
import json


@dataclass
class ChatMessage:
    """Represents a single message in a chat conversation."""
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass 
class ChatSession:
    """Represents a user's chat session with conversation history and context."""
    session_id: str
    user_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    messages: List[ChatMessage] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    analysis_reports: List[str] = field(default_factory=list)  # Analysis IDs
    uploaded_logs: List[str] = field(default_factory=list)    # Log file names


class SessionManager:
    """Manages chat sessions and conversation context."""
    
    def __init__(self, session_timeout_hours: int = 24):
        """Initialize session manager.
        
        Args:
            session_timeout_hours: Hours after which inactive sessions expire
        """
        self.sessions: Dict[str, ChatSession] = {}
        self.session_timeout = timedelta(hours=session_timeout_hours)
    
    def create_session(self, user_id: Optional[str] = None) -> str:
        """Create a new chat session.
        
        Args:
            user_id: Optional user identifier
            
        Returns:
            session_id: Unique session identifier
        """
        session_id = str(uuid.uuid4())
        session = ChatSession(
            session_id=session_id,
            user_id=user_id
        )
        self.sessions[session_id] = session
        return session_id
    
    def get_session(self, session_id: str) -> Optional[ChatSession]:
        """Get a chat session by ID.
        
        Args:
            session_id: Session identifier
            
        Returns:
            ChatSession if found and not expired, None otherwise
        """
        if session_id not in self.sessions:
            return None
            
        session = self.sessions[session_id]
        
        # Check if session has expired
        if datetime.now() - session.last_activity > self.session_timeout:
            del self.sessions[session_id]
            return None
            
        return session
    
    def add_message(self, session_id: str, role: str, content: str, 
                   metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Add a message to a chat session.
        
        Args:
            session_id: Session identifier
            role: Message role ('user' or 'assistant')
            content: Message content
            metadata: Optional message metadata
            
        Returns:
            True if message added successfully, False otherwise
        """
        session = self.get_session(session_id)
        if not session:
            return False
            
        message = ChatMessage(
            role=role,
            content=content,
            metadata=metadata or {}
        )
        
        session.messages.append(message)
        session.last_activity = datetime.now()
        
        # Keep conversation history manageable (last 50 messages)
        if len(session.messages) > 50:
            session.messages = session.messages[-50:]
            
        return True
    
    def get_conversation_history(self, session_id: str, 
                               last_n_messages: Optional[int] = None) -> List[ChatMessage]:
        """Get conversation history for a session.
        
        Args:
            session_id: Session identifier
            last_n_messages: Optional limit on number of recent messages
            
        Returns:
            List of chat messages
        """
        session = self.get_session(session_id)
        if not session:
            return []
            
        messages = session.messages
        if last_n_messages:
            messages = messages[-last_n_messages:]
            
        return messages
    
    def update_context(self, session_id: str, context_updates: Dict[str, Any]) -> bool:
        """Update session context with new information.
        
        Args:
            session_id: Session identifier
            context_updates: Dictionary of context updates
            
        Returns:
            True if updated successfully, False otherwise
        """
        session = self.get_session(session_id)
        if not session:
            return False
            
        session.context.update(context_updates)
        session.last_activity = datetime.now()
        return True
    
    def add_analysis_report(self, session_id: str, analysis_id: str) -> bool:
        """Associate an analysis report with a session.
        
        Args:
            session_id: Session identifier
            analysis_id: Analysis report identifier
            
        Returns:
            True if added successfully, False otherwise
        """
        session = self.get_session(session_id)
        if not session:
            return False
            
        if analysis_id not in session.analysis_reports:
            session.analysis_reports.append(analysis_id)
            
        session.last_activity = datetime.now()
        return True
    
    def add_uploaded_log(self, session_id: str, log_filename: str) -> bool:
        """Associate an uploaded log file with a session.
        
        Args:
            session_id: Session identifier
            log_filename: Name of uploaded log file
            
        Returns:
            True if added successfully, False otherwise
        """
        session = self.get_session(session_id)
        if not session:
            return False
            
        if log_filename not in session.uploaded_logs:
            session.uploaded_logs.append(log_filename)
            
        session.last_activity = datetime.now()
        return True
    
    def cleanup_expired_sessions(self) -> int:
        """Remove expired sessions.
        
        Returns:
            Number of sessions cleaned up
        """
        expired_sessions = []
        now = datetime.now()
        
        for session_id, session in self.sessions.items():
            if now - session.last_activity > self.session_timeout:
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            del self.sessions[session_id]
            
        return len(expired_sessions)
    
    def get_session_stats(self) -> Dict[str, Any]:
        """Get statistics about active sessions.
        
        Returns:
            Dictionary with session statistics
        """
        return {
            "active_sessions": len(self.sessions),
            "total_messages": sum(len(s.messages) for s in self.sessions.values()),
            "sessions_with_reports": len([s for s in self.sessions.values() if s.analysis_reports]),
            "sessions_with_logs": len([s for s in self.sessions.values() if s.uploaded_logs])
        } 