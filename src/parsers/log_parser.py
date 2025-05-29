"""Log parser for firmware logs and crash dumps."""

import re
import json
from typing import List, Optional, Dict, Any
from datetime import datetime

from ..models import LogEvent, LogEventType, ParsedLog


class LogParser:
    """Parser for firmware logs that detects crashes, errors, and other events."""
    
    # Regex patterns for different types of firmware events
    PATTERNS = {
        LogEventType.HARD_FAULT: [
            r"HardFault_Handler",
            r"Hard\s*Fault",
            r"HARD_FAULT",
        ],
        LogEventType.BUS_FAULT: [
            r"BusFault_Handler",
            r"Bus\s*Fault",
            r"BUS_FAULT",
        ],
        LogEventType.WATCHDOG_RESET: [
            r"Watchdog\s*Reset",
            r"WDT\s*Reset",
            r"IWDG\s*Reset",
            r"watchdog\s*timeout",
        ],
        LogEventType.ASSERTION_FAILURE: [
            r"assert\s*\(",
            r"assertion\s*failed",
            r"ASSERT",
            r"__assert_func",
        ],
        LogEventType.PANIC: [
            r"panic\s*\(",
            r"PANIC",
            r"kernel\s*panic",
        ],
        LogEventType.NULL_POINTER: [
            r"null\s*pointer",
            r"NULL\s*pointer",
            r"0x00000000",
            r"segmentation\s*fault",
        ],
        LogEventType.STACK_OVERFLOW: [
            r"stack\s*overflow",
            r"STACK_OVERFLOW",
            r"stack\s*corruption",
        ],
        LogEventType.MEMORY_ERROR: [
            r"memory\s*error",
            r"malloc\s*failed",
            r"out\s*of\s*memory",
            r"heap\s*corruption",
        ],
        LogEventType.SENSOR_FAILURE: [
            r"sensor\s*error",
            r"sensor\s*failure",
            r"I2C\s*error",
            r"SPI\s*error",
        ],
        LogEventType.BOOT_FAILURE: [
            r"boot\s*failed",
            r"bootloader\s*error",
            r"failed\s*to\s*boot",
        ],
    }
    
    # Timestamp patterns
    TIMESTAMP_PATTERNS = [
        r"\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}",  # 2023-12-01 14:30:45
        r"\d{2}:\d{2}:\d{2}\.\d{3}",               # 14:30:45.123
        r"\[\s*\d+\.\d+\]",                        # [ 1234.567]
        r"\d+ms",                                   # 1234ms
        r"\d+:\d+:\d+",                            # 14:30:45
    ]
    
    # Stack trace patterns
    STACK_TRACE_PATTERNS = [
        r"0x[0-9a-fA-F]{8}",  # Memory addresses
        r"at\s+0x[0-9a-fA-F]+",
        r"#\d+\s+0x[0-9a-fA-F]+",
        r"PC:\s*0x[0-9a-fA-F]+",
        r"LR:\s*0x[0-9a-fA-F]+",
    ]
    
    def __init__(self):
        """Initialize the log parser."""
        self.compiled_patterns = {}
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Compile regex patterns for better performance."""
        for event_type, patterns in self.PATTERNS.items():
            self.compiled_patterns[event_type] = [
                re.compile(pattern, re.IGNORECASE) for pattern in patterns
            ]
    
    def parse_log(self, log_content: str) -> ParsedLog:
        """Parse a log file and extract events."""
        lines = log_content.split('\n')
        events = []
        parsing_errors = []
        metadata = {
            "parsed_at": datetime.now().isoformat(),
            "total_lines": len(lines),
        }
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line:
                continue
                
            try:
                event = self._parse_line(line, line_num)
                if event:
                    events.append(event)
            except Exception as e:
                parsing_errors.append(f"Line {line_num}: {str(e)}")
        
        # Post-process to group stack traces
        events = self._group_stack_traces(events)
        
        return ParsedLog(
            total_lines=len(lines),
            events=events,
            metadata=metadata,
            parsing_errors=parsing_errors
        )
    
    def _parse_line(self, line: str, line_num: int) -> Optional[LogEvent]:
        """Parse a single log line."""
        # Extract timestamp
        timestamp = self._extract_timestamp(line)
        
        # Check for known event patterns
        event_type = self._detect_event_type(line)
        
        if event_type == LogEventType.UNKNOWN:
            # Check if it's a stack trace line
            if self._is_stack_trace_line(line):
                event_type = LogEventType.CRASH
            else:
                return None
        
        # Extract memory address if present
        memory_address = self._extract_memory_address(line)
        
        # Extract function name if present
        function_name = self._extract_function_name(line)
        
        return LogEvent(
            timestamp=timestamp,
            event_type=event_type,
            message=line,
            line_number=line_num,
            raw_line=line,
            memory_address=memory_address,
            function_name=function_name
        )
    
    def _extract_timestamp(self, line: str) -> Optional[str]:
        """Extract timestamp from a log line."""
        for pattern in self.TIMESTAMP_PATTERNS:
            match = re.search(pattern, line)
            if match:
                return match.group(0)
        return None
    
    def _detect_event_type(self, line: str) -> LogEventType:
        """Detect the type of event from a log line."""
        for event_type, patterns in self.compiled_patterns.items():
            for pattern in patterns:
                if pattern.search(line):
                    return event_type
        return LogEventType.UNKNOWN
    
    def _is_stack_trace_line(self, line: str) -> bool:
        """Check if a line contains stack trace information."""
        for pattern in self.STACK_TRACE_PATTERNS:
            if re.search(pattern, line):
                return True
        return False
    
    def _extract_memory_address(self, line: str) -> Optional[str]:
        """Extract memory address from a log line."""
        match = re.search(r"0x[0-9a-fA-F]{8}", line)
        return match.group(0) if match else None
    
    def _extract_function_name(self, line: str) -> Optional[str]:
        """Extract function name from a log line."""
        # Look for function names in various formats
        patterns = [
            r"in\s+(\w+)\s*\(",
            r"at\s+(\w+)\s*\(",
            r"(\w+)\s*\(\)",
            r"function\s+(\w+)",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, line)
            if match:
                return match.group(1)
        return None
    
    def _group_stack_traces(self, events: List[LogEvent]) -> List[LogEvent]:
        """Group consecutive stack trace lines with their parent event."""
        if not events:
            return events
        
        grouped_events = []
        current_event = None
        stack_trace_lines = []
        
        for event in events:
            if event.event_type == LogEventType.CRASH and self._is_stack_trace_line(event.message):
                # This is a stack trace line
                stack_trace_lines.append(event.message)
            else:
                # This is a regular event
                if current_event and stack_trace_lines:
                    # Attach accumulated stack trace to previous event
                    current_event.stack_trace = stack_trace_lines
                    stack_trace_lines = []
                
                current_event = event
                grouped_events.append(event)
        
        # Handle any remaining stack trace
        if current_event and stack_trace_lines:
            current_event.stack_trace = stack_trace_lines
        
        return grouped_events
    
    def parse_json_log(self, json_content: str) -> ParsedLog:
        """Parse JSON-formatted logs."""
        try:
            data = json.loads(json_content)
            events = []
            
            if isinstance(data, list):
                # Array of log entries
                for i, entry in enumerate(data, 1):
                    event = self._parse_json_entry(entry, i)
                    if event:
                        events.append(event)
            elif isinstance(data, dict):
                # Single log entry or structured log
                if "logs" in data:
                    # Structured format with logs array
                    for i, entry in enumerate(data["logs"], 1):
                        event = self._parse_json_entry(entry, i)
                        if event:
                            events.append(event)
                else:
                    # Single entry
                    event = self._parse_json_entry(data, 1)
                    if event:
                        events.append(event)
            
            return ParsedLog(
                total_lines=len(events),
                events=events,
                metadata={"format": "json", "parsed_at": datetime.now().isoformat()}
            )
            
        except json.JSONDecodeError as e:
            return ParsedLog(
                total_lines=0,
                events=[],
                parsing_errors=[f"JSON parsing error: {str(e)}"]
            )
    
    def _parse_json_entry(self, entry: Dict[str, Any], line_num: int) -> Optional[LogEvent]:
        """Parse a single JSON log entry."""
        if not isinstance(entry, dict):
            return None
        
        message = entry.get("message", str(entry))
        timestamp = entry.get("timestamp") or entry.get("time")
        level = entry.get("level", "").lower()
        
        # Detect event type from message or level
        event_type = self._detect_event_type(message)
        if event_type == LogEventType.UNKNOWN and level in ["error", "fatal", "critical"]:
            event_type = LogEventType.CRASH
        
        return LogEvent(
            timestamp=timestamp,
            event_type=event_type,
            message=message,
            line_number=line_num,
            raw_line=json.dumps(entry),
            function_name=entry.get("function"),
            file_name=entry.get("file")
        ) 