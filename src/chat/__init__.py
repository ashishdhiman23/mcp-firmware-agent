"""
Conversational AI module for MCP Firmware Analysis Server.

This module provides chat-based interaction with firmware logs and analysis reports,
allowing users to ask natural language questions about their embedded systems debugging.
"""

from .chat_engine import ChatEngine
from .session_manager import SessionManager
from .chat_service import ChatService

__all__ = ['ChatEngine', 'SessionManager', 'ChatService'] 