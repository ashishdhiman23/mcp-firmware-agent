"""
Core chat engine for conversational AI firmware debugging.

Integrates with GPT-4 to provide natural language responses to firmware
debugging queries, with context awareness of analysis reports and logs.
"""

import asyncio
from typing import Dict, List, Optional, Any, Tuple
from openai import AsyncOpenAI
from datetime import datetime
import json

from ..analyzers.gpt_analyzer import GPTAnalyzer
from ..config import get_settings
from .session_manager import SessionManager, ChatSession, ChatMessage


class ChatEngine:
    """Core engine for conversational AI firmware debugging assistance."""
    
    def __init__(self, session_manager: SessionManager):
        """Initialize chat engine.
        
        Args:
            session_manager: Session manager instance
        """
        self.session_manager = session_manager
        self.config = get_settings()
        self.gpt_analyzer = GPTAnalyzer()
        
        # Initialize OpenAI client
        self.openai_client = AsyncOpenAI(api_key=self.config.openai_api_key)
        
        # Conversation prompts for different types of queries
        self.system_prompts = {
            "general": self._get_general_system_prompt(),
            "debug_assistant": self._get_debug_assistant_prompt(),
            "log_analysis": self._get_log_analysis_prompt(),
            "troubleshooting": self._get_troubleshooting_prompt()
        }
    
    def _get_general_system_prompt(self) -> str:
        """Get the general system prompt for chat interactions."""
        return """You are an expert firmware debugging assistant for embedded systems. 
You help developers understand crash logs, analyze hardware failures, and debug embedded systems issues.

Your responses should be:
- Clear and conversational, avoiding overly technical jargon when possible
- Specific and actionable, providing concrete debugging steps
- Contextual, referring to the user's specific logs and analysis reports
- Educational, explaining the "why" behind issues when helpful

When referencing analysis reports or logs, always mention specific details like:
- File names and line numbers
- Memory addresses and register values  
- Timestamps and event sequences
- Hardware components and peripherals

If you need more information to provide a complete answer, ask specific follow-up questions.
"""

    def _get_debug_assistant_prompt(self) -> str:
        """Get the debugging assistant system prompt."""
        return """You are a senior embedded systems engineer helping debug firmware issues.
Focus on practical debugging steps and root cause analysis.

When analyzing issues:
1. Identify the immediate cause (what triggered the error)
2. Trace back to the root cause (why it happened)
3. Suggest specific debugging techniques
4. Recommend prevention strategies

Always provide actionable next steps and reference relevant documentation or tools when possible.
"""

    def _get_log_analysis_prompt(self) -> str:
        """Get the log analysis system prompt."""
        return """You are analyzing firmware crash logs and telemetry data.
Focus on pattern recognition and event correlation.

When examining logs:
1. Identify critical events and their timing
2. Look for patterns across multiple crashes
3. Correlate hardware and software events
4. Explain cascading failures and their relationships

Provide clear explanations of what the logs reveal about system behavior.
"""

    def _get_troubleshooting_prompt(self) -> str:
        """Get the troubleshooting system prompt."""
        return """You are guiding users through systematic firmware troubleshooting.
Provide step-by-step debugging procedures.

Structure your responses as:
1. Immediate checks (what to verify first)
2. Diagnostic procedures (how to gather more data)
3. Potential solutions (ranked by likelihood)
4. Verification steps (how to confirm the fix)

Always consider both hardware and software causes.
"""
    
    async def process_chat_message(self, session_id: str, user_message: str, 
                                 context_type: str = "general") -> Tuple[str, Dict[str, Any]]:
        """Process a chat message and generate AI response.
        
        Args:
            session_id: Chat session identifier
            user_message: User's message/question
            context_type: Type of context for system prompt
            
        Returns:
            Tuple of (AI response, metadata)
        """
        # Get session and conversation history
        session = self.session_manager.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found or expired")
        
        # Add user message to session
        self.session_manager.add_message(session_id, "user", user_message)
        
        # Prepare context for GPT
        context = await self._prepare_context(session, user_message)
        
        # Generate AI response
        ai_response, metadata = await self._generate_response(
            session, user_message, context, context_type
        )
        
        # Add AI response to session
        self.session_manager.add_message(session_id, "assistant", ai_response, metadata)
        
        return ai_response, metadata
    
    async def _prepare_context(self, session: ChatSession, user_message: str) -> Dict[str, Any]:
        """Prepare context information for GPT analysis.
        
        Args:
            session: Chat session
            user_message: Current user message
            
        Returns:
            Context dictionary
        """
        context = {
            "conversation_history": [],
            "analysis_reports": [],
            "log_summaries": [],
            "session_context": session.context
        }
        
        # Get recent conversation history (last 10 messages for context)
        recent_messages = self.session_manager.get_conversation_history(
            session.session_id, last_n_messages=10
        )
        
        for msg in recent_messages[:-1]:  # Exclude current message
            context["conversation_history"].append({
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat()
            })
        
        # TODO: Load actual analysis reports and log data
        # This would integrate with the existing analysis system
        context["analysis_reports"] = session.analysis_reports
        context["log_summaries"] = session.uploaded_logs
        
        return context
    
    async def _generate_response(self, session: ChatSession, user_message: str,
                               context: Dict[str, Any], context_type: str) -> Tuple[str, Dict[str, Any]]:
        """Generate AI response using GPT-4.
        
        Args:
            session: Chat session
            user_message: User's message
            context: Prepared context
            context_type: Type of system prompt to use
            
        Returns:
            Tuple of (response text, metadata)
        """
        try:
            # Prepare messages for GPT-4
            messages = [
                {"role": "system", "content": self.system_prompts.get(context_type, self.system_prompts["general"])}
            ]
            
            # Add context information
            if context["conversation_history"]:
                context_summary = self._format_conversation_context(context)
                messages.append({
                    "role": "system", 
                    "content": f"Conversation context:\n{context_summary}"
                })
            
            # Add recent conversation history
            for msg in context["conversation_history"]:
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
            
            # Add current user message
            messages.append({"role": "user", "content": user_message})
            
            # Call GPT-4
            response = await self.openai_client.chat.completions.create(
                model=self.config.openai_model,
                messages=messages,
                max_tokens=self.config.openai_max_tokens,
                temperature=0.7,  # Slightly higher for conversational responses
                stream=False
            )
            
            ai_response = response.choices[0].message.content.strip()
            
            metadata = {
                "model_used": self.config.openai_model,
                "context_type": context_type,
                "tokens_used": response.usage.total_tokens if response.usage else 0,
                "response_time": datetime.now().isoformat(),
                "confidence": "high",  # Could implement confidence scoring
                "references": self._extract_references(ai_response, context)
            }
            
            return ai_response, metadata
            
        except Exception as e:
            error_response = f"I apologize, but I encountered an error processing your request: {str(e)}. Please try rephrasing your question or contact support if the issue persists."
            error_metadata = {
                "error": str(e),
                "context_type": context_type,
                "response_time": datetime.now().isoformat()
            }
            return error_response, error_metadata
    
    def _format_conversation_context(self, context: Dict[str, Any]) -> str:
        """Format context information for GPT prompt.
        
        Args:
            context: Context dictionary
            
        Returns:
            Formatted context string
        """
        context_parts = []
        
        if context["analysis_reports"]:
            reports_list = ", ".join(context["analysis_reports"])
            context_parts.append(f"Available analysis reports: {reports_list}")
        
        if context["log_summaries"]:
            logs_list = ", ".join(context["log_summaries"])
            context_parts.append(f"Uploaded log files: {logs_list}")
        
        if context["session_context"]:
            for key, value in context["session_context"].items():
                context_parts.append(f"{key}: {value}")
        
        return "\n".join(context_parts) if context_parts else "No additional context available."
    
    def _extract_references(self, response: str, context: Dict[str, Any]) -> List[Dict[str, str]]:
        """Extract references from AI response.
        
        Args:
            response: AI response text
            context: Context used for response
            
        Returns:
            List of reference dictionaries
        """
        references = []
        
        # Look for file names, report IDs, etc. in the response
        # This is a simplified version - could be enhanced with NLP
        
        for report_id in context.get("analysis_reports", []):
            if report_id in response:
                references.append({
                    "type": "analysis_report",
                    "id": report_id,
                    "description": f"Analysis report {report_id}"
                })
        
        for log_file in context.get("log_summaries", []):
            if log_file in response:
                references.append({
                    "type": "log_file", 
                    "id": log_file,
                    "description": f"Log file {log_file}"
                })
        
        return references
    
    async def suggest_follow_up_questions(self, session_id: str) -> List[str]:
        """Generate follow-up question suggestions based on conversation context.
        
        Args:
            session_id: Chat session identifier
            
        Returns:
            List of suggested follow-up questions
        """
        session = self.session_manager.get_session(session_id)
        if not session or not session.messages:
            return [
                "Can you analyze my latest crash log?",
                "What are the most common causes of watchdog resets?",
                "How can I debug a hard fault?",
                "Show me memory corruption patterns to look for."
            ]
        
        # Get last assistant message to understand context
        last_assistant_msg = None
        for msg in reversed(session.messages):
            if msg.role == "assistant":
                last_assistant_msg = msg
                break
        
        if not last_assistant_msg:
            return []
        
        # Generate contextual suggestions based on last response
        # This could be enhanced with GPT-4 to generate smarter suggestions
        suggestions = []
        
        response_lower = last_assistant_msg.content.lower()
        
        if "stack overflow" in response_lower:
            suggestions.extend([
                "How can I prevent stack overflows in the future?",
                "What tools can help me monitor stack usage?",
                "Show me the call stack that led to this overflow."
            ])
        
        if "memory corruption" in response_lower:
            suggestions.extend([
                "What debugging tools can detect memory corruption?",
                "How do I trace the source of this corruption?",
                "Are there patterns in when this corruption occurs?"
            ])
        
        if "hard fault" in response_lower:
            suggestions.extend([
                "Can you explain the CPU registers at the time of fault?",
                "What's the most likely cause of this hard fault?",
                "How do I set up debugging for hard faults?"
            ])
        
        if "i2c" in response_lower or "sensor" in response_lower:
            suggestions.extend([
                "How can I diagnose I2C bus issues?",
                "What are common sensor communication problems?",
                "Should I check the hardware connections?"
            ])
        
        # Default suggestions if no specific patterns found
        if not suggestions:
            suggestions = [
                "Can you explain this issue in more detail?",
                "What should I check next?",
                "Are there similar issues in my other logs?",
                "How can I prevent this from happening again?"
            ]
        
        return suggestions[:4]  # Return top 4 suggestions
    
    def get_chat_capabilities(self) -> Dict[str, Any]:
        """Get information about chat capabilities and supported queries.
        
        Returns:
            Dictionary describing chat capabilities
        """
        return {
            "supported_queries": [
                "Firmware crash analysis and root cause identification",
                "Hardware troubleshooting and component diagnosis", 
                "Memory corruption and stack overflow debugging",
                "Watchdog reset and timeout issue analysis",
                "Boot sequence and initialization problem diagnosis",
                "Sensor and peripheral communication failures"
            ],
            "context_types": list(self.system_prompts.keys()),
            "features": [
                "Conversational follow-up questions",
                "Reference to specific logs and analysis reports",
                "Actionable debugging recommendations",
                "Educational explanations of firmware concepts",
                "Integration with existing analysis reports"
            ],
            "example_queries": [
                "Why did my device reset at 3AM?",
                "Show me common assertion failures for the last week.",
                "Explain the root cause of crash log #123.",
                "What's causing the I2C sensor timeouts?",
                "How do I debug this stack overflow?",
                "Are there patterns in my memory corruption issues?"
            ]
        } 