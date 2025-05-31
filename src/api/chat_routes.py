"""
FastAPI routes for conversational AI chat functionality.

Provides REST endpoints for chat interactions, session management,
and integration with firmware analysis.
"""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from fastapi.responses import JSONResponse
from typing import Dict, List, Optional, Any
from pydantic import BaseModel
import asyncio
from pathlib import Path
import tempfile
import os

from ..chat.chat_service import ChatService
from ..utils.analysis_service import AnalysisService


# Pydantic models for request/response
class ChatRequest(BaseModel):
    message: str
    context_type: Optional[str] = "general"


class ChatResponse(BaseModel):
    response: str
    suggestions: List[str]
    session_id: str
    timestamp: str
    metadata: Dict[str, Any]


class SessionRequest(BaseModel):
    user_id: Optional[str] = None


class SessionResponse(BaseModel):
    session_id: str
    message: str


class UploadResponse(BaseModel):
    log_file: str
    uploaded_at: str
    session_id: str
    analysis: Optional[Dict[str, Any]] = None
    auto_analysis_message: Optional[str] = None


# Initialize router
router = APIRouter(prefix="/chat", tags=["chat"])

# Initialize services - we'll create these when the router is included
analysis_service = None
chat_service = None


def get_analysis_service():
    """Get or create analysis service instance."""
    global analysis_service
    if analysis_service is None:
        analysis_service = AnalysisService()
    return analysis_service


def get_chat_service():
    """Get or create chat service instance."""
    global chat_service
    if chat_service is None:
        chat_service = ChatService(get_analysis_service())
    return chat_service


@router.post("/sessions", response_model=SessionResponse)
async def create_chat_session(
    request: SessionRequest,
    chat_service: ChatService = Depends(get_chat_service)
):
    """Create a new chat session.
    
    Args:
        request: Session creation request
        chat_service: Chat service dependency
        
    Returns:
        New session information
    """
    try:
        session_id = await chat_service.start_chat_session(request.user_id)
        
        return SessionResponse(
            session_id=session_id,
            message="Chat session created successfully. You can now ask questions about firmware debugging!"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create session: {str(e)}")


@router.post("/sessions/{session_id}/messages", response_model=ChatResponse)
async def send_chat_message(
    session_id: str,
    request: ChatRequest,
    chat_service: ChatService = Depends(get_chat_service)
):
    """Send a message to a chat session.
    
    Args:
        session_id: Chat session identifier
        request: Chat message request
        chat_service: Chat service dependency
        
    Returns:
        AI response with suggestions
    """
    try:
        response_data = await chat_service.chat(
            session_id=session_id,
            message=request.message,
            context_type=request.context_type
        )
        
        if "error" in response_data:
            raise HTTPException(status_code=400, detail=response_data["error"])
        
        return ChatResponse(**response_data)
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat processing failed: {str(e)}")


@router.post("/sessions/{session_id}/upload", response_model=UploadResponse)
async def upload_log_file(
    session_id: str,
    file: UploadFile = File(...),
    analyze_immediately: bool = True,
    chat_service: ChatService = Depends(get_chat_service)
):
    """Upload a log file to a chat session.
    
    Args:
        session_id: Chat session identifier
        file: Uploaded log file
        analyze_immediately: Whether to analyze the log immediately
        chat_service: Chat service dependency
        
    Returns:
        Upload result with optional analysis
    """
    try:
        # Validate file type
        allowed_extensions = ['.log', '.txt', '.json']
        file_extension = Path(file.filename).suffix.lower()
        
        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid file type. Allowed extensions: {', '.join(allowed_extensions)}"
            )
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        try:
            # Process upload through chat service
            result = await chat_service.upload_log_to_session(
                session_id=session_id,
                log_file_path=temp_file_path,
                analyze_immediately=analyze_immediately
            )
            
            if "error" in result:
                raise HTTPException(status_code=400, detail=result["error"])
            
            return UploadResponse(**result)
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.get("/sessions/{session_id}/context")
async def get_session_context(
    session_id: str,
    chat_service: ChatService = Depends(get_chat_service)
):
    """Get context information for a chat session.
    
    Args:
        session_id: Chat session identifier
        chat_service: Chat service dependency
        
    Returns:
        Session context and metadata
    """
    try:
        context = await chat_service.get_session_context(session_id)
        
        if "error" in context:
            raise HTTPException(status_code=404, detail=context["error"])
        
        return context
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get context: {str(e)}")


@router.get("/sessions/{session_id}/history")
async def get_conversation_history(
    session_id: str,
    include_metadata: bool = False,
    chat_service: ChatService = Depends(get_chat_service)
):
    """Get conversation history for a chat session.
    
    Args:
        session_id: Chat session identifier
        include_metadata: Whether to include message metadata
        chat_service: Chat service dependency
        
    Returns:
        List of conversation messages
    """
    try:
        history = await chat_service.get_conversation_history(
            session_id=session_id,
            include_metadata=include_metadata
        )
        
        return {"conversation_history": history}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get history: {str(e)}")


@router.get("/sessions/{session_id}/suggestions")
async def get_follow_up_suggestions(
    session_id: str,
    chat_service: ChatService = Depends(get_chat_service)
):
    """Get follow-up question suggestions for a chat session.
    
    Args:
        session_id: Chat session identifier
        chat_service: Chat service dependency
        
    Returns:
        List of suggested follow-up questions
    """
    try:
        suggestions = await chat_service.chat_engine.suggest_follow_up_questions(session_id)
        
        return {"suggestions": suggestions}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get suggestions: {str(e)}")


@router.get("/sessions/{session_id}/search")
async def search_session_content(
    session_id: str,
    query: str,
    chat_service: ChatService = Depends(get_chat_service)
):
    """Search through logs and analysis reports in a session.
    
    Args:
        session_id: Chat session identifier
        query: Search query
        chat_service: Chat service dependency
        
    Returns:
        Search results
    """
    try:
        results = await chat_service.search_logs_and_reports(session_id, query)
        
        return {"search_results": results, "query": query}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.get("/sessions/{session_id}/export")
async def export_session(
    session_id: str,
    format: str = "json",
    chat_service: ChatService = Depends(get_chat_service)
):
    """Export a chat session.
    
    Args:
        session_id: Chat session identifier
        format: Export format ("json" or "markdown")
        chat_service: Chat service dependency
        
    Returns:
        Exported session data
    """
    try:
        if format not in ["json", "markdown"]:
            raise HTTPException(status_code=400, detail="Format must be 'json' or 'markdown'")
        
        exported_content = await chat_service.export_session(session_id, format)
        
        if exported_content is None:
            raise HTTPException(status_code=404, detail="Session not found")
        
        media_type = "application/json" if format == "json" else "text/markdown"
        filename = f"chat_session_{session_id}.{format}"
        
        return JSONResponse(
            content={"content": exported_content, "filename": filename},
            media_type=media_type
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@router.get("/capabilities")
async def get_chat_capabilities(
    chat_service: ChatService = Depends(get_chat_service)
):
    """Get information about chat capabilities and supported queries.
    
    Args:
        chat_service: Chat service dependency
        
    Returns:
        Chat capabilities and features
    """
    try:
        capabilities = chat_service.chat_engine.get_chat_capabilities()
        
        return capabilities
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get capabilities: {str(e)}")


@router.get("/statistics")
async def get_chat_statistics(
    chat_service: ChatService = Depends(get_chat_service)
):
    """Get statistics about chat usage and sessions.
    
    Args:
        chat_service: Chat service dependency
        
    Returns:
        Chat usage statistics
    """
    try:
        stats = await chat_service.get_chat_statistics()
        
        return stats
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    chat_service: ChatService = Depends(get_chat_service)
):
    """Delete a chat session.
    
    Args:
        session_id: Chat session identifier
        chat_service: Chat service dependency
        
    Returns:
        Deletion confirmation
    """
    try:
        session = chat_service.session_manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Remove session
        if session_id in chat_service.session_manager.sessions:
            del chat_service.session_manager.sessions[session_id]
        
        return {"message": f"Session {session_id} deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete session: {str(e)}")


@router.post("/sessions/{session_id}/reset")
async def reset_session(
    session_id: str,
    chat_service: ChatService = Depends(get_chat_service)
):
    """Reset a chat session (clear conversation history).
    
    Args:
        session_id: Chat session identifier
        chat_service: Chat service dependency
        
    Returns:
        Reset confirmation
    """
    try:
        session = chat_service.session_manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Clear messages but keep context
        session.messages.clear()
        
        return {"message": f"Session {session_id} conversation history cleared"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reset session: {str(e)}") 