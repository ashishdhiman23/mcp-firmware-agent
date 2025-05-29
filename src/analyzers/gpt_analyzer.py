"""GPT-4 analyzer for firmware log analysis."""

import json
from typing import List, Optional, Dict, Any
from openai import OpenAI

from ..models import ParsedLog, AnalysisResult, CriticalityLevel, LogEvent, SymbolResolution
from ..config import get_settings


class GPTAnalyzer:
    """Analyzer that uses GPT-4 to provide intelligent insights on firmware logs."""
    
    def __init__(self):
        """Initialize the GPT analyzer."""
        self.settings = get_settings()
        self.client = None
        
        if self.settings.openai_api_key:
            self.client = OpenAI(api_key=self.settings.openai_api_key)
    
    def analyze_log(
        self, 
        parsed_log: ParsedLog, 
        symbol_resolutions: Optional[List[SymbolResolution]] = None
    ) -> AnalysisResult:
        """Analyze a parsed log using GPT-4.
        
        Args:
            parsed_log: The parsed log data
            symbol_resolutions: Optional symbol resolution data
            
        Returns:
            Analysis result with insights and recommendations
        """
        if not self.client:
            return self._create_fallback_analysis(parsed_log)
        
        try:
            # Prepare the analysis prompt
            prompt = self._create_analysis_prompt(parsed_log, symbol_resolutions)
            
            # Call GPT-4
            response = self.client.chat.completions.create(
                model=self.settings.openai_model,
                messages=[
                    {
                        "role": "system",
                        "content": self._get_system_prompt()
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=self.settings.openai_max_tokens,
                temperature=self.settings.openai_temperature
            )
            
            # Parse the response
            result_text = response.choices[0].message.content
            result_data = json.loads(result_text)
            
            return self._parse_gpt_response(result_data, parsed_log)
            
        except Exception as e:
            # Fallback to rule-based analysis if GPT fails
            return self._create_fallback_analysis(parsed_log, error=str(e))
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for GPT-4."""
        return """You are an expert embedded firmware debugger and systems engineer. 
        
Your task is to analyze firmware logs, crash dumps, and boot telemetry data to provide insightful debugging assistance.

You should:
1. Identify the root cause of issues based on log patterns
2. Suggest specific, actionable fixes
3. Assess the criticality level (high/medium/low)
4. Identify the likely module or component involved
5. Provide technical details when relevant

Focus on:
- Memory-related issues (null pointers, stack overflows, heap corruption)
- Hardware faults (bus faults, hard faults, watchdog resets)
- Assertion failures and panics
- Sensor and peripheral failures
- Boot sequence problems

Be concise but insightful. Provide practical recommendations that a firmware developer can act on.

Respond in JSON format with these fields:
{
  "summary": "Brief explanation of what went wrong",
  "suggested_fix": "Specific actionable recommendation",
  "confidence_score": 0.85,
  "likely_module": "module_name.c or component",
  "criticality_level": "high|medium|low",
  "technical_details": "Additional technical context",
  "related_events": ["list", "of", "related", "event", "types"]
}"""
    
    def _create_analysis_prompt(
        self, 
        parsed_log: ParsedLog, 
        symbol_resolutions: Optional[List[SymbolResolution]] = None
    ) -> str:
        """Create the analysis prompt for GPT-4."""
        prompt_parts = []
        
        # Add log summary
        prompt_parts.append(f"FIRMWARE LOG ANALYSIS REQUEST")
        prompt_parts.append(f"Total log lines: {parsed_log.total_lines}")
        prompt_parts.append(f"Events detected: {len(parsed_log.events)}")
        
        if parsed_log.parsing_errors:
            prompt_parts.append(f"Parsing errors: {len(parsed_log.parsing_errors)}")
        
        prompt_parts.append("")
        
        # Add detected events
        if parsed_log.events:
            prompt_parts.append("DETECTED EVENTS:")
            for i, event in enumerate(parsed_log.events[:10], 1):  # Limit to first 10 events
                prompt_parts.append(f"{i}. [{event.event_type.value}] Line {event.line_number}")
                if event.timestamp:
                    prompt_parts.append(f"   Time: {event.timestamp}")
                prompt_parts.append(f"   Message: {event.message}")
                
                if event.function_name:
                    prompt_parts.append(f"   Function: {event.function_name}")
                if event.memory_address:
                    prompt_parts.append(f"   Address: {event.memory_address}")
                if event.stack_trace:
                    prompt_parts.append(f"   Stack trace: {len(event.stack_trace)} frames")
                    for trace_line in event.stack_trace[:3]:  # Show first 3 stack frames
                        prompt_parts.append(f"     {trace_line}")
                prompt_parts.append("")
            
            if len(parsed_log.events) > 10:
                prompt_parts.append(f"... and {len(parsed_log.events) - 10} more events")
                prompt_parts.append("")
        
        # Add symbol resolution information
        if symbol_resolutions:
            resolved_symbols = [s for s in symbol_resolutions if s.resolved]
            if resolved_symbols:
                prompt_parts.append("SYMBOL RESOLUTION:")
                for symbol in resolved_symbols[:5]:  # Show first 5 resolved symbols
                    prompt_parts.append(f"  {symbol.address} -> {symbol.function_name}")
                    if symbol.file_name and symbol.line_number:
                        prompt_parts.append(f"    at {symbol.file_name}:{symbol.line_number}")
                prompt_parts.append("")
        
        # Add metadata
        if parsed_log.metadata:
            prompt_parts.append("METADATA:")
            for key, value in parsed_log.metadata.items():
                prompt_parts.append(f"  {key}: {value}")
            prompt_parts.append("")
        
        # Add analysis request
        prompt_parts.append("Please analyze this firmware log and provide:")
        prompt_parts.append("1. Root cause analysis")
        prompt_parts.append("2. Suggested fix or debugging steps")
        prompt_parts.append("3. Criticality assessment")
        prompt_parts.append("4. Likely module/component involved")
        
        return "\n".join(prompt_parts)
    
    def _parse_gpt_response(self, response_data: Dict[str, Any], parsed_log: ParsedLog) -> AnalysisResult:
        """Parse GPT-4 response into AnalysisResult."""
        try:
            # Extract criticality level
            criticality_str = response_data.get("criticality_level", "medium").lower()
            if criticality_str == "high":
                criticality = CriticalityLevel.HIGH
            elif criticality_str == "low":
                criticality = CriticalityLevel.LOW
            else:
                criticality = CriticalityLevel.MEDIUM
            
            # Ensure confidence score is valid
            confidence = float(response_data.get("confidence_score", 0.5))
            confidence = max(0.0, min(1.0, confidence))
            
            return AnalysisResult(
                summary=response_data.get("summary", "Analysis completed"),
                suggested_fix=response_data.get("suggested_fix", "Review the log for more details"),
                confidence_score=confidence,
                likely_module=response_data.get("likely_module"),
                criticality_level=criticality,
                technical_details=response_data.get("technical_details"),
                related_events=response_data.get("related_events", [])
            )
            
        except (KeyError, ValueError, TypeError) as e:
            # Fallback if response parsing fails
            return self._create_fallback_analysis(parsed_log, error=f"Response parsing error: {e}")
    
    def _create_fallback_analysis(self, parsed_log: ParsedLog, error: Optional[str] = None) -> AnalysisResult:
        """Create a fallback analysis when GPT-4 is not available or fails."""
        # Simple rule-based analysis
        high_severity_events = [
            "hard_fault", "bus_fault", "panic", "stack_overflow", "memory_error"
        ]
        
        critical_events = [
            event for event in parsed_log.events 
            if event.event_type.value in high_severity_events
        ]
        
        if critical_events:
            criticality = CriticalityLevel.HIGH
            summary = f"Critical firmware issue detected: {critical_events[0].event_type.value}"
            suggested_fix = "Review stack trace and check for memory corruption or hardware issues"
        elif parsed_log.events:
            criticality = CriticalityLevel.MEDIUM
            summary = f"Firmware issue detected: {parsed_log.events[0].event_type.value}"
            suggested_fix = "Investigate the reported error and check system configuration"
        else:
            criticality = CriticalityLevel.LOW
            summary = "No critical issues detected in the log"
            suggested_fix = "Log appears normal, monitor for recurring issues"
        
        technical_details = f"Fallback analysis used. Total events: {len(parsed_log.events)}"
        if error:
            technical_details += f" Error: {error}"
        
        return AnalysisResult(
            summary=summary,
            suggested_fix=suggested_fix,
            confidence_score=0.6,
            likely_module=None,
            criticality_level=criticality,
            technical_details=technical_details,
            related_events=[event.event_type.value for event in parsed_log.events[:5]]
        )
    
    def is_available(self) -> bool:
        """Check if GPT-4 analysis is available."""
        return self.client is not None and bool(self.settings.openai_api_key) 