"""Main analysis service that orchestrates the firmware log analysis pipeline."""

import time
import uuid
from datetime import datetime
from typing import Optional, List

from ..models import AnalysisResponse, AnalysisRequest, ParsedLog, SymbolResolution
from ..parsers import LogParser, ElfParser
from ..analyzers import GPTAnalyzer, ReportGenerator
from ..utils.file_utils import FileUtils


class AnalysisService:
    """Main service for orchestrating firmware log analysis."""
    
    def __init__(self):
        """Initialize the analysis service."""
        self.log_parser = LogParser()
        self.elf_parser = ElfParser()
        self.gpt_analyzer = GPTAnalyzer()
        self.report_generator = ReportGenerator()
        self.file_utils = FileUtils()
    
    async def analyze_firmware_log(
        self,
        log_content: str,
        elf_content: Optional[bytes] = None,
        analysis_options: Optional[dict] = None
    ) -> AnalysisResponse:
        """Perform complete firmware log analysis.
        
        Args:
            log_content: Raw log content as string
            elf_content: Optional ELF binary content for symbol resolution
            analysis_options: Optional analysis configuration
            
        Returns:
            Complete analysis response
        """
        start_time = time.time()
        analysis_id = str(uuid.uuid4())[:8]
        
        try:
            # Step 1: Parse the log content
            parsed_log = await self._parse_log_content(log_content)
            
            # Step 2: Resolve symbols if ELF is provided
            symbol_resolutions = []
            if elf_content:
                symbol_resolutions = await self._resolve_symbols(log_content, elf_content)
            
            # Step 3: Analyze with GPT-4
            analysis_result = await self._analyze_with_gpt(parsed_log, symbol_resolutions)
            
            # Step 4: Generate reports
            markdown_report = self.report_generator.generate_markdown_report(
                analysis_result, parsed_log, symbol_resolutions, analysis_id
            )
            
            html_report = self.report_generator.generate_html_report(
                analysis_result, parsed_log, symbol_resolutions, analysis_id
            )
            
            # Step 5: Save HTML report and get URL
            report_path = self.report_generator.save_report(
                html_report, "html", analysis_id
            )
            report_url = self.report_generator.get_report_url(report_path)
            
            # Calculate processing time
            processing_time = (time.time() - start_time) * 1000  # Convert to milliseconds
            
            return AnalysisResponse(
                analysis_id=analysis_id,
                timestamp=datetime.now(),
                analysis_result=analysis_result,
                parsed_log=parsed_log,
                symbol_resolutions=symbol_resolutions,
                report_url=report_url,
                markdown_report=markdown_report,
                processing_time_ms=processing_time
            )
            
        except Exception as e:
            # Create error response
            processing_time = (time.time() - start_time) * 1000
            
            # Create minimal parsed log for error case
            error_parsed_log = ParsedLog(
                total_lines=len(log_content.split('\n')),
                events=[],
                parsing_errors=[f"Analysis failed: {str(e)}"]
            )
            
            # Create fallback analysis result
            from ..models import AnalysisResult, CriticalityLevel
            error_analysis = AnalysisResult(
                summary=f"Analysis failed due to error: {str(e)}",
                suggested_fix="Please check the log format and try again",
                confidence_score=0.0,
                criticality_level=CriticalityLevel.MEDIUM,
                technical_details=f"Error during analysis: {str(e)}"
            )
            
            return AnalysisResponse(
                analysis_id=analysis_id,
                timestamp=datetime.now(),
                analysis_result=error_analysis,
                parsed_log=error_parsed_log,
                symbol_resolutions=[],
                processing_time_ms=processing_time
            )
    
    async def _parse_log_content(self, log_content: str) -> ParsedLog:
        """Parse log content into structured events.
        
        Args:
            log_content: Raw log content
            
        Returns:
            Parsed log data
        """
        # Detect if content is JSON
        if self.file_utils.is_json_content(log_content):
            return self.log_parser.parse_json_log(log_content)
        else:
            return self.log_parser.parse_log(log_content)
    
    async def _resolve_symbols(self, log_content: str, elf_content: bytes) -> List[SymbolResolution]:
        """Resolve memory addresses to symbols using ELF binary.
        
        Args:
            log_content: Raw log content
            elf_content: ELF binary content
            
        Returns:
            List of symbol resolutions
        """
        try:
            # Extract addresses from log
            addresses = self.elf_parser.extract_addresses_from_log(log_content)
            
            if not addresses:
                return []
            
            # Resolve addresses to symbols
            resolutions = self.elf_parser.resolve_addresses(elf_content, addresses)
            
            return resolutions
            
        except Exception as e:
            # Return empty list if symbol resolution fails
            return []
    
    async def _analyze_with_gpt(
        self, 
        parsed_log: ParsedLog, 
        symbol_resolutions: List[SymbolResolution]
    ) -> "AnalysisResult":
        """Analyze parsed log with GPT-4.
        
        Args:
            parsed_log: Parsed log data
            symbol_resolutions: Symbol resolution data
            
        Returns:
            Analysis result
        """
        return self.gpt_analyzer.analyze_log(parsed_log, symbol_resolutions)
    
    def get_analysis_capabilities(self) -> dict:
        """Get information about analysis capabilities.
        
        Returns:
            Dictionary with capability information
        """
        return {
            "log_parsing": {
                "supported_formats": ["text", "json"],
                "detected_events": [event_type.value for event_type in self.log_parser.PATTERNS.keys()],
                "max_lines": self.log_parser.settings.max_log_lines if hasattr(self.log_parser, 'settings') else 10000
            },
            "symbol_resolution": {
                "available": self.elf_parser.addr2line_path is not None,
                "tool_path": self.elf_parser.addr2line_path,
                "supported_architectures": ["ARM", "x86_64", "i386", "RISC-V"]
            },
            "gpt_analysis": {
                "available": self.gpt_analyzer.is_available(),
                "model": self.gpt_analyzer.settings.openai_model,
                "fallback_available": True
            },
            "report_generation": {
                "formats": ["markdown", "html"],
                "templates_available": True
            }
        }
    
    def validate_analysis_request(self, request: AnalysisRequest) -> bool:
        """Validate an analysis request.
        
        Args:
            request: Analysis request to validate
            
        Returns:
            True if valid
            
        Raises:
            ValueError: If request is invalid
        """
        if not request.log_content or not request.log_content.strip():
            raise ValueError("Log content cannot be empty")
        
        if len(request.log_content) > 10 * 1024 * 1024:  # 10MB limit
            raise ValueError("Log content too large (max 10MB)")
        
        if request.elf_content and len(request.elf_content) > 50 * 1024 * 1024:  # 50MB limit
            raise ValueError("ELF content too large (max 50MB)")
        
        return True 