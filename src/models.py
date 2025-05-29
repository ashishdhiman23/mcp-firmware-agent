"""Data models for the MCP Firmware Log Analysis Server."""

from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class CriticalityLevel(str, Enum):
    """Severity levels for firmware issues."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class LogEventType(str, Enum):
    """Types of log events that can be detected."""
    CRASH = "crash"
    WATCHDOG_RESET = "watchdog_reset"
    ASSERTION_FAILURE = "assertion_failure"
    SENSOR_FAILURE = "sensor_failure"
    MEMORY_ERROR = "memory_error"
    STACK_OVERFLOW = "stack_overflow"
    NULL_POINTER = "null_pointer"
    BUS_FAULT = "bus_fault"
    HARD_FAULT = "hard_fault"
    PANIC = "panic"
    BOOT_FAILURE = "boot_failure"
    UNKNOWN = "unknown"


class LogEvent(BaseModel):
    """Represents a parsed log event."""
    timestamp: Optional[str] = None
    event_type: LogEventType
    message: str
    line_number: int
    raw_line: str
    stack_trace: Optional[List[str]] = None
    memory_address: Optional[str] = None
    function_name: Optional[str] = None
    file_name: Optional[str] = None


class ParsedLog(BaseModel):
    """Represents a fully parsed log file."""
    total_lines: int
    events: List[LogEvent]
    metadata: Dict[str, Any] = Field(default_factory=dict)
    parsing_errors: List[str] = Field(default_factory=list)


class AnalysisResult(BaseModel):
    """Result of GPT-4 analysis."""
    summary: str
    suggested_fix: str
    confidence_score: float = Field(ge=0.0, le=1.0)
    likely_module: Optional[str] = None
    criticality_level: CriticalityLevel
    technical_details: Optional[str] = None
    related_events: List[str] = Field(default_factory=list)


class SymbolResolution(BaseModel):
    """Result of ELF symbol resolution."""
    address: str
    function_name: Optional[str] = None
    file_name: Optional[str] = None
    line_number: Optional[int] = None
    resolved: bool = False


class AnalysisRequest(BaseModel):
    """Request model for log analysis."""
    log_content: str
    elf_content: Optional[bytes] = None
    analysis_options: Dict[str, Any] = Field(default_factory=dict)


class AnalysisResponse(BaseModel):
    """Response model for log analysis."""
    analysis_id: str
    timestamp: datetime
    analysis_result: AnalysisResult
    parsed_log: ParsedLog
    symbol_resolutions: List[SymbolResolution] = Field(default_factory=list)
    report_url: Optional[str] = None
    markdown_report: Optional[str] = None
    processing_time_ms: float


class HealthCheck(BaseModel):
    """Health check response model."""
    status: str
    timestamp: datetime
    version: str
    openai_configured: bool 