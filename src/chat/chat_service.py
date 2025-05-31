"""
Chat service for integrating conversational AI with firmware analysis.

Provides high-level chat functionality and integration with existing
analysis reports, log files, and system data.
"""

import asyncio
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import json
from datetime import datetime

from .chat_engine import ChatEngine
from .session_manager import SessionManager
from ..utils.analysis_service import AnalysisService
from ..models import AnalysisResult


class ChatService:
    """High-level service for conversational AI firmware debugging."""
    
    def __init__(self, analysis_service: AnalysisService):
        """Initialize chat service.
        
        Args:
            analysis_service: Existing analysis service instance
        """
        self.analysis_service = analysis_service
        self.session_manager = SessionManager()
        self.chat_engine = ChatEngine(self.session_manager)
        
        # Cache for analysis results to provide context
        self.analysis_cache: Dict[str, AnalysisResult] = {}
        
        # Integration with existing reports directory
        self.reports_dir = Path("reports")
        self.reports_dir.mkdir(exist_ok=True)
    
    async def start_chat_session(self, user_id: Optional[str] = None) -> str:
        """Start a new chat session.
        
        Args:
            user_id: Optional user identifier
            
        Returns:
            session_id: New session identifier
        """
        session_id = self.session_manager.create_session(user_id)
        
        # Add welcome context
        welcome_context = {
            "capabilities": self.chat_engine.get_chat_capabilities(),
            "available_features": [
                "Natural language firmware debugging",
                "Analysis of uploaded crash logs", 
                "Integration with existing analysis reports",
                "Conversational follow-up questions",
                "Actionable debugging recommendations"
            ]
        }
        
        self.session_manager.update_context(session_id, welcome_context)
        
        return session_id
    
    async def chat(self, session_id: str, message: str, 
                  context_type: str = "general") -> Dict[str, Any]:
        """Process a chat message and return response.
        
        Args:
            session_id: Chat session identifier
            message: User message
            context_type: Type of context for response generation
            
        Returns:
            Dictionary with response and metadata
        """
        try:
            # Process message through chat engine
            ai_response, metadata = await self.chat_engine.process_chat_message(
                session_id, message, context_type
            )
            
            # Generate follow-up suggestions
            suggestions = await self.chat_engine.suggest_follow_up_questions(session_id)
            
            return {
                "response": ai_response,
                "suggestions": suggestions,
                "metadata": metadata,
                "session_id": session_id,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "response": f"I apologize, but I encountered an error: {str(e)}",
                "suggestions": [
                    "Try rephrasing your question",
                    "Check if your session is still active",
                    "Start a new chat session"
                ],
                "metadata": {"error": str(e)},
                "session_id": session_id,
                "timestamp": datetime.now().isoformat()
            }
    
    async def upload_log_to_session(self, session_id: str, log_file_path: str, 
                                  analyze_immediately: bool = True) -> Dict[str, Any]:
        """Upload a log file and associate it with a chat session.
        
        Args:
            session_id: Chat session identifier
            log_file_path: Path to log file
            analyze_immediately: Whether to analyze the log immediately
            
        Returns:
            Dictionary with upload result and analysis (if requested)
        """
        try:
            log_path = Path(log_file_path)
            if not log_path.exists():
                return {"error": f"Log file not found: {log_file_path}"}
            
            # Add log to session
            self.session_manager.add_uploaded_log(session_id, log_path.name)
            
            result = {
                "log_file": log_path.name,
                "uploaded_at": datetime.now().isoformat(),
                "session_id": session_id
            }
            
            if analyze_immediately:
                # Perform analysis using existing analysis service
                try:
                    # Read log content
                    with open(log_file_path, 'r') as f:
                        log_content = f.read()
                    
                    # Use the existing analysis method
                    analysis_result = await self.analysis_service.analyze_firmware_log(log_content)
                    
                    if analysis_result:
                        # Cache analysis result
                        self.analysis_cache[analysis_result.analysis_id] = analysis_result
                        
                        # Add analysis to session
                        self.session_manager.add_analysis_report(session_id, analysis_result.analysis_id)
                        
                        # Update session context with analysis summary
                        context_update = {
                            "latest_analysis": {
                                "analysis_id": analysis_result.analysis_id,
                                "summary": analysis_result.analysis_result.summary,
                                "confidence": analysis_result.analysis_result.confidence_score,
                                "criticality": analysis_result.analysis_result.criticality_level,
                                "log_file": log_path.name
                            }
                        }
                        self.session_manager.update_context(session_id, context_update)
                        
                        result["analysis"] = {
                            "analysis_id": analysis_result.analysis_id,
                            "summary": analysis_result.analysis_result.summary,
                            "confidence_score": analysis_result.analysis_result.confidence_score,
                            "processing_time_ms": analysis_result.processing_time_ms
                        }
                        
                        # Generate automatic chat message about the analysis
                        auto_message = await self._generate_analysis_summary_message(analysis_result)
                        self.session_manager.add_message(session_id, "assistant", auto_message)
                        result["auto_analysis_message"] = auto_message
                    else:
                        result["analysis"] = None
                        auto_message = f"📁 File uploaded: {log_path.name}\n\nFile uploaded successfully but analysis could not be completed. You can still ask questions about general firmware debugging topics."
                        self.session_manager.add_message(session_id, "assistant", auto_message)
                        result["auto_analysis_message"] = auto_message
                        
                except Exception as e:
                    # Handle analysis errors gracefully
                    error_message = f"📁 File uploaded: {log_path.name}\n\nFile uploaded successfully but analysis failed: {str(e)}\nYou can still ask general firmware debugging questions."
                    self.session_manager.add_message(session_id, "assistant", error_message)
                    result["auto_analysis_message"] = error_message
                    result["analysis_error"] = str(e)
            
            return result
            
        except Exception as e:
            return {"error": f"Failed to upload log: {str(e)}"}
    
    async def _generate_analysis_summary_message(self, analysis_result: AnalysisResult) -> str:
        """Generate an automatic message summarizing analysis results.
        
        Args:
            analysis_result: Analysis result to summarize
            
        Returns:
            Formatted summary message
        """
        result = analysis_result.analysis_result
        
        message_parts = [
            f"📊 **Analysis Complete** (Confidence: {result.confidence_score*100:.1f}%)",
            f"**Summary:** {result.summary}",
        ]
        
        if result.suggested_fix:
            message_parts.append(f"**Recommended Fix:** {result.suggested_fix}")
        
        if result.likely_module:
            message_parts.append(f"**Likely Module:** {result.likely_module}")
        
        if result.related_events:
            events_str = ", ".join(result.related_events)
            message_parts.append(f"**Related Events:** {events_str}")
        
        message_parts.extend([
            "",
            "💬 **Ask me anything about this analysis!** For example:",
            "• \"Can you explain this issue in more detail?\"",
            "• \"What should I check next?\"", 
            "• \"How can I prevent this from happening again?\""
        ])
        
        return "\n".join(message_parts)
    
    async def get_session_context(self, session_id: str) -> Dict[str, Any]:
        """Get comprehensive context for a chat session.
        
        Args:
            session_id: Chat session identifier
            
        Returns:
            Dictionary with session context
        """
        session = self.session_manager.get_session(session_id)
        if not session:
            return {"error": "Session not found or expired"}
        
        context = {
            "session_id": session_id,
            "created_at": session.created_at.isoformat(),
            "last_activity": session.last_activity.isoformat(),
            "message_count": len(session.messages),
            "uploaded_logs": session.uploaded_logs,
            "analysis_reports": session.analysis_reports,
            "session_context": session.context
        }
        
        # Add analysis summaries
        if session.analysis_reports:
            context["analysis_summaries"] = []
            for analysis_id in session.analysis_reports:
                if analysis_id in self.analysis_cache:
                    result = self.analysis_cache[analysis_id]
                    context["analysis_summaries"].append({
                        "analysis_id": analysis_id,
                        "summary": result.analysis_result.summary,
                        "confidence": result.analysis_result.confidence_score,
                        "timestamp": result.timestamp.isoformat()
                    })
        
        return context
    
    async def get_conversation_history(self, session_id: str, 
                                     include_metadata: bool = False) -> List[Dict[str, Any]]:
        """Get conversation history for a session.
        
        Args:
            session_id: Chat session identifier
            include_metadata: Whether to include message metadata
            
        Returns:
            List of messages with timestamps
        """
        messages = self.session_manager.get_conversation_history(session_id)
        
        conversation = []
        for msg in messages:
            message_dict = {
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat()
            }
            
            if include_metadata and msg.metadata:
                message_dict["metadata"] = msg.metadata
                
            conversation.append(message_dict)
        
        return conversation
    
    async def search_logs_and_reports(self, session_id: str, query: str) -> List[Dict[str, Any]]:
        """Search through logs and analysis reports for a session.
        
        Args:
            session_id: Chat session identifier
            query: Search query
            
        Returns:
            List of matching results
        """
        session = self.session_manager.get_session(session_id)
        if not session:
            return []
        
        results = []
        
        # Search analysis reports
        for analysis_id in session.analysis_reports:
            if analysis_id in self.analysis_cache:
                analysis = self.analysis_cache[analysis_id]
                result = analysis.analysis_result
                
                # Simple text search in analysis content
                searchable_text = f"{result.summary} {result.suggested_fix} {result.technical_details}".lower()
                if query.lower() in searchable_text:
                    results.append({
                        "type": "analysis_report",
                        "id": analysis_id,
                        "title": f"Analysis Report - {result.summary[:50]}...",
                        "relevance": "high",
                        "content_preview": result.summary,
                        "timestamp": analysis.timestamp.isoformat()
                    })
        
        # Search uploaded logs (simplified - would need to implement log content search)
        for log_file in session.uploaded_logs:
            if query.lower() in log_file.lower():
                results.append({
                    "type": "log_file",
                    "id": log_file,
                    "title": f"Log File - {log_file}",
                    "relevance": "medium",
                    "content_preview": f"Log file: {log_file}",
                    "timestamp": None  # Would need to get from file system
                })
        
        return results
    
    async def get_chat_statistics(self) -> Dict[str, Any]:
        """Get statistics about chat usage and sessions.
        
        Returns:
            Dictionary with chat statistics
        """
        session_stats = self.session_manager.get_session_stats()
        
        # Clean up expired sessions
        cleaned_sessions = self.session_manager.cleanup_expired_sessions()
        
        return {
            "session_statistics": session_stats,
            "cleaned_expired_sessions": cleaned_sessions,
            "analysis_cache_size": len(self.analysis_cache),
            "capabilities": self.chat_engine.get_chat_capabilities(),
            "timestamp": datetime.now().isoformat()
        }
    
    async def export_session(self, session_id: str, format: str = "json") -> Optional[str]:
        """Export a chat session for backup or sharing.
        
        Args:
            session_id: Chat session identifier
            format: Export format ("json" or "markdown")
            
        Returns:
            Exported content as string, or None if error
        """
        session = self.session_manager.get_session(session_id)
        if not session:
            return None
        
        export_data = {
            "session_id": session_id,
            "created_at": session.created_at.isoformat(),
            "last_activity": session.last_activity.isoformat(),
            "conversation": await self.get_conversation_history(session_id, include_metadata=True),
            "context": await self.get_session_context(session_id),
            "exported_at": datetime.now().isoformat()
        }
        
        if format == "json":
            return json.dumps(export_data, indent=2)
        elif format == "markdown":
            return self._format_session_as_markdown(export_data)
        else:
            return None
    
    def _format_session_as_markdown(self, export_data: Dict[str, Any]) -> str:
        """Format session data as markdown.
        
        Args:
            export_data: Session export data
            
        Returns:
            Markdown formatted string
        """
        lines = [
            f"# Chat Session Export",
            f"**Session ID:** {export_data['session_id']}",
            f"**Created:** {export_data['created_at']}",
            f"**Exported:** {export_data['exported_at']}",
            "",
            "## Conversation History",
            ""
        ]
        
        for msg in export_data["conversation"]:
            role_emoji = "👤" if msg["role"] == "user" else "🤖"
            lines.extend([
                f"### {role_emoji} {msg['role'].title()} - {msg['timestamp']}",
                msg["content"],
                ""
            ])
        
        lines.extend([
            "## Session Context",
            f"- **Uploaded Logs:** {', '.join(export_data['context'].get('uploaded_logs', []))}",
            f"- **Analysis Reports:** {', '.join(export_data['context'].get('analysis_reports', []))}",
            f"- **Message Count:** {export_data['context'].get('message_count', 0)}",
        ])
        
        return "\n".join(lines) 