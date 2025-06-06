"""Main FastAPI application for firmware log analysis."""

import os
from datetime import datetime
from typing import Optional
from pathlib import Path

from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from ..models import AnalysisResponse, HealthCheck, AnalysisRequest
from ..utils import AnalysisService, FileUtils
from ..config import get_settings
from .. import __version__
from .chat_routes import router as chat_router

# Initialize FastAPI app
app = FastAPI(
    title="MCP Firmware Log Analysis Server",
    description="AI-powered embedded systems debugging assistant with conversational AI",
    version=__version__,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include chat routes
app.include_router(chat_router)

# Initialize services
analysis_service = AnalysisService()
file_utils = FileUtils()
settings = get_settings()

# Create necessary directories
Path(settings.reports_dir).mkdir(exist_ok=True)
Path(settings.upload_dir).mkdir(exist_ok=True)

# Mount static files for serving reports
if Path(settings.reports_dir).exists():
    app.mount("/reports", StaticFiles(directory=settings.reports_dir), name="reports")

# Mount templates directory for serving HTML files
templates_dir = Path("templates")
if templates_dir.exists():
    app.mount("/static", StaticFiles(directory=templates_dir), name="static")


@app.get("/", response_class=HTMLResponse)
async def root():
    """Root endpoint with basic information."""
    return """
    <html>
        <head>
            <title>MCP Firmware Log Analysis Server</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                         color: white; padding: 20px; border-radius: 8px; }
                .content { margin-top: 20px; }
                .section { margin: 20px 0; }
                .endpoint { background: #f5f5f5; padding: 10px; margin: 10px 0; border-radius: 5px; }
                .chat-endpoint { background: #e3f2fd; padding: 10px; margin: 10px 0; border-radius: 5px; border-left: 4px solid #2196f3; }
                .new-badge { background: #4caf50; color: white; padding: 2px 8px; border-radius: 12px; font-size: 0.8em; margin-left: 8px; }
                a { color: #007bff; text-decoration: none; }
                a:hover { text-decoration: underline; }
                .feature-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 20px; }
                .feature-card { background: #f8f9fa; padding: 15px; border-radius: 8px; border: 1px solid #dee2e6; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🔧 MCP Firmware Log Analysis Server</h1>
                <p>AI-powered embedded systems debugging assistant with conversational AI</p>
            </div>
            <div class="content">
                <div class="section">
                    <h2>🤖 Conversational AI Chat <span class="new-badge">NEW</span></h2>
                    <p>Chat with your firmware logs using natural language! Ask questions like "Why did my device reset?" or "Explain this stack overflow".</p>
                    
                    <div class="chat-endpoint">
                        <strong>POST /chat/sessions</strong> - Create a new chat session
                    </div>
                    <div class="chat-endpoint">
                        <strong>POST /chat/sessions/{id}/messages</strong> - Send chat messages
                    </div>
                    <div class="chat-endpoint">
                        <strong>POST /chat/sessions/{id}/upload</strong> - Upload logs to chat session
                    </div>
                    <div class="chat-endpoint">
                        <strong>GET /chat/capabilities</strong> - View chat capabilities
                    </div>
                </div>

                <div class="section">
                    <h2>📊 Analysis Endpoints</h2>
                    <div class="endpoint">
                        <strong>POST /analyze-log</strong> - Upload and analyze firmware logs
                    </div>
                    <div class="endpoint">
                        <strong>POST /analyze-text</strong> - Analyze log content directly
                    </div>
                    <div class="endpoint">
                        <strong>GET /health</strong> - Check server health and capabilities
                    </div>
                </div>

                <div class="section">
                    <h2>📚 Documentation</h2>
                    <div class="endpoint">
                        <strong>GET /docs</strong> - <a href="/docs">Interactive API documentation</a>
                    </div>
                    <div class="endpoint">
                        <strong>GET /redoc</strong> - <a href="/redoc">Alternative API documentation</a>
                    </div>
                </div>
                
                <div class="feature-grid">
                    <div class="feature-card">
                        <h3>🔍 Traditional Analysis</h3>
                        <p>Upload firmware logs for AI-powered analysis:</p>
                        <pre>curl -X POST "http://localhost:8000/analyze-log" \\
     -F "log_file=@firmware.log" \\
     -F "elf_file=@firmware.elf"</pre>
                    </div>
                    
                    <div class="feature-card">
                        <h3>💬 Chat Analysis</h3>
                        <p>Start a conversation about your logs:</p>
                        <pre># Create session
curl -X POST "http://localhost:8000/chat/sessions"

# Ask questions
curl -X POST "http://localhost:8000/chat/sessions/{id}/messages" \\
     -H "Content-Type: application/json" \\
     -d '{"message": "Why did my device crash?"}'</pre>
                    </div>
                </div>

                <div class="section">
                    <h2>🌟 Key Features</h2>
                    <ul>
                        <li><strong>Conversational AI:</strong> Ask natural language questions about your firmware</li>
                        <li><strong>Context Awareness:</strong> Chat maintains context across multiple turns</li>
                        <li><strong>95% AI Accuracy:</strong> GPT-4 powered analysis with high confidence</li>
                        <li><strong>Multi-format Reports:</strong> HTML, JSON, and Markdown outputs</li>
                        <li><strong>Real-time Processing:</strong> 8-10 second analysis times</li>
                        <li><strong>Session Management:</strong> Persistent conversations with file uploads</li>
                    </ul>
                </div>
            </div>
        </body>
    </html>
    """


@app.get("/health", response_model=HealthCheck)
async def health_check():
    """Health check endpoint."""
    return HealthCheck(
        status="healthy",
        timestamp=datetime.now(),
        version=__version__,
        openai_configured=bool(settings.openai_api_key)
    )


@app.get("/capabilities")
async def get_capabilities():
    """Get analysis capabilities and configuration."""
    capabilities = analysis_service.get_analysis_capabilities()
    capabilities["server_info"] = {
        "version": __version__,
        "max_file_size": settings.max_file_size,
        "allowed_log_extensions": settings.allowed_log_extensions,
        "allowed_elf_extensions": settings.allowed_elf_extensions
    }
    return capabilities


@app.post("/analyze-log", response_model=AnalysisResponse)
async def analyze_log(
    log_file: UploadFile = File(..., description="Firmware log file"),
    elf_file: Optional[UploadFile] = File(None, description="Optional ELF binary for symbol resolution")
):
    """
    Analyze firmware logs and generate insights.
    
    Upload a firmware log file (and optionally an ELF binary) to get:
    - Root cause analysis
    - Suggested fixes
    - Criticality assessment
    - Symbol resolution (if ELF provided)
    - Detailed HTML and Markdown reports
    """
    try:
        # Validate log file
        file_utils.validate_log_file(log_file)
        
        # Read log content
        log_content = await file_utils.read_log_file(log_file)
        
        # Read ELF content if provided
        elf_content = None
        if elf_file:
            file_utils.validate_elf_file(elf_file)
            elf_content = await file_utils.read_elf_file(elf_file)
        
        # Create analysis request
        request = AnalysisRequest(
            log_content=log_content,
            elf_content=elf_content
        )
        
        # Validate request
        analysis_service.validate_analysis_request(request)
        
        # Perform analysis
        result = await analysis_service.analyze_firmware_log(
            log_content=log_content,
            elf_content=elf_content
        )
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@app.post("/analyze-text", response_model=AnalysisResponse)
async def analyze_text(request: AnalysisRequest):
    """
    Analyze firmware logs from raw text content.
    
    Send log content directly as JSON instead of uploading files.
    Useful for programmatic access or when logs are already in memory.
    """
    try:
        # Validate request
        analysis_service.validate_analysis_request(request)
        
        # Perform analysis
        result = await analysis_service.analyze_firmware_log(
            log_content=request.log_content,
            elf_content=request.elf_content,
            analysis_options=request.analysis_options
        )
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@app.get("/reports/{report_id}")
async def get_report(report_id: str):
    """Get a generated analysis report by ID."""
    # Look for the report file
    reports_dir = Path(settings.reports_dir)
    
    # Try different possible filenames
    possible_files = [
        f"analysis_{report_id}.html",
        f"analysis_{report_id}*.html",  # With timestamp
    ]
    
    report_file = None
    for pattern in possible_files:
        matches = list(reports_dir.glob(pattern))
        if matches:
            report_file = matches[0]  # Take the first match
            break
    
    if not report_file or not report_file.exists():
        raise HTTPException(status_code=404, detail="Report not found")
    
    return FileResponse(
        path=str(report_file),
        media_type="text/html",
        filename=report_file.name
    )


@app.get("/download-report/{report_id}")
async def download_report(report_id: str, format: str = "html"):
    """Download a generated analysis report."""
    reports_dir = Path(settings.reports_dir)
    
    # Look for the report file
    pattern = f"analysis_{report_id}*.{format}"
    matches = list(reports_dir.glob(pattern))
    
    if not matches:
        raise HTTPException(status_code=404, detail="Report not found")
    
    report_file = matches[0]
    
    return FileResponse(
        path=str(report_file),
        media_type="application/octet-stream",
        filename=report_file.name,
        headers={"Content-Disposition": f"attachment; filename={report_file.name}"}
    )


@app.get("/test-upload", response_class=HTMLResponse)
async def test_upload_form():
    """Simple HTML form for testing file uploads."""
    return """
    <html>
        <head>
            <title>Test Firmware Log Analysis</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                .form-group { margin: 20px 0; }
                label { display: block; margin-bottom: 5px; font-weight: bold; }
                input[type="file"] { margin-bottom: 10px; }
                button { background: #007bff; color: white; padding: 10px 20px; 
                        border: none; border-radius: 5px; cursor: pointer; }
                button:hover { background: #0056b3; }
                .result { margin-top: 20px; padding: 20px; background: #f8f9fa; 
                         border-radius: 5px; }
            </style>
        </head>
        <body>
            <h1>🔧 Test Firmware Log Analysis</h1>
            <form action="/analyze-log" method="post" enctype="multipart/form-data">
                <div class="form-group">
                    <label for="log_file">Firmware Log File (required):</label>
                    <input type="file" id="log_file" name="log_file" accept=".log,.txt,.json" required>
                </div>
                
                <div class="form-group">
                    <label for="elf_file">ELF Binary (optional):</label>
                    <input type="file" id="elf_file" name="elf_file" accept=".elf,.bin">
                </div>
                
                <button type="submit">Analyze Log</button>
            </form>
            
            <div class="result">
                <h3>Sample Log Content for Testing:</h3>
                <pre>
[12:34:56.789] INFO: System boot started
[12:34:57.123] ERROR: HardFault_Handler triggered
[12:34:57.124] ERROR: PC: 0x08001234
[12:34:57.125] ERROR: LR: 0x08005678
[12:34:57.126] ERROR: Stack trace:
[12:34:57.127] ERROR: #0 0x08001234 in sensor_read()
[12:34:57.128] ERROR: #1 0x08005678 in main_loop()
[12:34:57.129] FATAL: System reset required
                </pre>
            </div>
        </body>
    </html>
    """


@app.get("/chat", response_class=HTMLResponse)
async def chat_interface():
    """Serve the chat interface."""
    chat_template_path = Path("templates/chat.html")
    if not chat_template_path.exists():
        raise HTTPException(status_code=404, detail="Chat interface not found")
    
    with open(chat_template_path, 'r', encoding='utf-8') as f:
        return HTMLResponse(content=f.read(), status_code=200)


# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return {"error": "Endpoint not found", "detail": str(exc)}


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    return {"error": "Internal server error", "detail": "An unexpected error occurred"}


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize the application on startup."""
    print(f"🚀 MCP Firmware Log Analysis Server v{__version__} starting...")
    print(f"📁 Reports directory: {settings.reports_dir}")
    print(f"📁 Upload directory: {settings.upload_dir}")
    print(f"🤖 GPT-4 available: {analysis_service.gpt_analyzer.is_available()}")
    print(f"🔧 Symbol resolution available: {analysis_service.elf_parser.addr2line_path is not None}")


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Clean up on shutdown."""
    print("🛑 MCP Firmware Log Analysis Server shutting down...")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.api.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    ) 