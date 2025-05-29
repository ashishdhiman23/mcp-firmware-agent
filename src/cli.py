"""Command-line interface for firmware log analysis."""

import argparse
import asyncio
import sys
from pathlib import Path
from typing import Optional

from .utils import AnalysisService
from .models import AnalysisRequest
from .config import get_settings


class FirmwareLogCLI:
    """Command-line interface for firmware log analysis."""
    
    def __init__(self):
        """Initialize the CLI."""
        self.analysis_service = AnalysisService()
        self.settings = get_settings()
    
    async def analyze_log_file(
        self, 
        log_path: str, 
        elf_path: Optional[str] = None,
        output_format: str = "markdown",
        output_file: Optional[str] = None
    ) -> None:
        """Analyze a log file from the command line.
        
        Args:
            log_path: Path to the log file
            elf_path: Optional path to ELF binary
            output_format: Output format (markdown, html, json)
            output_file: Optional output file path
        """
        try:
            # Read log file
            log_file = Path(log_path)
            if not log_file.exists():
                print(f"❌ Error: Log file not found: {log_path}")
                sys.exit(1)
            
            print(f"📖 Reading log file: {log_path}")
            log_content = log_file.read_text(encoding='utf-8', errors='replace')
            
            # Read ELF file if provided
            elf_content = None
            if elf_path:
                elf_file = Path(elf_path)
                if not elf_file.exists():
                    print(f"⚠️  Warning: ELF file not found: {elf_path}")
                else:
                    print(f"🔧 Reading ELF file: {elf_path}")
                    elf_content = elf_file.read_bytes()
            
            # Create analysis request
            request = AnalysisRequest(
                log_content=log_content,
                elf_content=elf_content
            )
            
            # Validate request
            self.analysis_service.validate_analysis_request(request)
            
            print("🔍 Analyzing firmware log...")
            
            # Perform analysis
            result = await self.analysis_service.analyze_firmware_log(
                log_content=log_content,
                elf_content=elf_content
            )
            
            # Display results
            self._display_results(result, output_format, output_file)
            
        except Exception as e:
            print(f"❌ Analysis failed: {str(e)}")
            sys.exit(1)
    
    def _display_results(self, result, output_format: str, output_file: Optional[str]):
        """Display analysis results."""
        print("\n" + "="*60)
        print("🎯 ANALYSIS COMPLETE")
        print("="*60)
        
        # Display summary
        analysis = result.analysis_result
        print(f"📊 Summary: {analysis.summary}")
        print(f"🔧 Suggested Fix: {analysis.suggested_fix}")
        print(f"⚡ Criticality: {analysis.criticality_level.value.upper()}")
        print(f"🎯 Confidence: {analysis.confidence_score:.1%}")
        
        if analysis.likely_module:
            print(f"📁 Likely Module: {analysis.likely_module}")
        
        print(f"⏱️  Processing Time: {result.processing_time_ms:.1f}ms")
        
        # Display events summary
        if result.parsed_log.events:
            print(f"\n📋 Events Detected: {len(result.parsed_log.events)}")
            event_counts = {}
            for event in result.parsed_log.events:
                event_type = event.event_type.value
                event_counts[event_type] = event_counts.get(event_type, 0) + 1
            
            for event_type, count in sorted(event_counts.items()):
                print(f"   • {event_type.replace('_', ' ').title()}: {count}")
        
        # Display symbol resolution summary
        if result.symbol_resolutions:
            resolved_count = sum(1 for s in result.symbol_resolutions if s.resolved)
            print(f"\n🔗 Symbol Resolution: {resolved_count}/{len(result.symbol_resolutions)} addresses resolved")
        
        # Output to file or display
        if output_format == "json":
            import json
            output_content = result.model_dump_json(indent=2)
        elif output_format == "html":
            output_content = self.analysis_service.report_generator.generate_html_report(
                analysis, result.parsed_log, result.symbol_resolutions, result.analysis_id
            )
        else:  # markdown
            output_content = result.markdown_report
        
        if output_file:
            output_path = Path(output_file)
            output_path.write_text(output_content, encoding='utf-8')
            print(f"\n💾 Report saved to: {output_file}")
        else:
            if output_format == "json":
                print(f"\n📄 JSON Output:")
                print(output_content)
            elif output_format == "html":
                print(f"\n🌐 HTML report generated (use --output to save)")
            else:
                print(f"\n📝 Markdown Report:")
                print("\n" + output_content)
    
    def check_dependencies(self):
        """Check if all dependencies are available."""
        print("🔍 Checking dependencies...")
        
        capabilities = self.analysis_service.get_analysis_capabilities()
        
        # Check GPT-4
        if capabilities["gpt_analysis"]["available"]:
            print("✅ GPT-4 analysis: Available")
        else:
            print("⚠️  GPT-4 analysis: Not configured (set OPENAI_API_KEY)")
        
        # Check symbol resolution
        if capabilities["symbol_resolution"]["available"]:
            print(f"✅ Symbol resolution: Available ({capabilities['symbol_resolution']['tool_path']})")
        else:
            print("⚠️  Symbol resolution: addr2line not found")
        
        # Check log parsing
        print("✅ Log parsing: Available")
        print("✅ Report generation: Available")
        
        print(f"\n📋 Supported log formats: {capabilities['log_parsing']['supported_formats']}")
        print(f"🎯 Detected event types: {len(capabilities['log_parsing']['detected_events'])}")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="MCP Firmware Log Analysis CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze a log file
  python -m src.cli analyze firmware.log
  
  # Analyze with ELF binary for symbol resolution
  python -m src.cli analyze firmware.log --elf firmware.elf
  
  # Save HTML report
  python -m src.cli analyze firmware.log --format html --output report.html
  
  # Check dependencies
  python -m src.cli check
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Analyze command
    analyze_parser = subparsers.add_parser("analyze", help="Analyze firmware log")
    analyze_parser.add_argument("log_file", help="Path to firmware log file")
    analyze_parser.add_argument("--elf", help="Path to ELF binary for symbol resolution")
    analyze_parser.add_argument(
        "--format", 
        choices=["markdown", "html", "json"], 
        default="markdown",
        help="Output format (default: markdown)"
    )
    analyze_parser.add_argument("--output", "-o", help="Output file path")
    
    # Check command
    check_parser = subparsers.add_parser("check", help="Check dependencies and capabilities")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    cli = FirmwareLogCLI()
    
    if args.command == "analyze":
        asyncio.run(cli.analyze_log_file(
            args.log_file,
            args.elf,
            args.format,
            args.output
        ))
    elif args.command == "check":
        cli.check_dependencies()


if __name__ == "__main__":
    main() 