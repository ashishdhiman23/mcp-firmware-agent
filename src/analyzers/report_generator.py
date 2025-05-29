"""Report generator for firmware analysis results."""

import os
import uuid
from datetime import datetime
from typing import List, Optional
from pathlib import Path
import markdown2
from jinja2 import Environment, FileSystemLoader, Template

from ..models import AnalysisResponse, AnalysisResult, ParsedLog, SymbolResolution
from ..config import get_settings


class ReportGenerator:
    """Generator for analysis reports in various formats."""
    
    def __init__(self):
        """Initialize the report generator."""
        self.settings = get_settings()
        self.reports_dir = Path(self.settings.reports_dir)
        self.templates_dir = Path(self.settings.templates_dir)
        
        # Ensure directories exist
        self.reports_dir.mkdir(exist_ok=True)
        self.templates_dir.mkdir(exist_ok=True)
        
        # Initialize Jinja2 environment
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            autoescape=True
        )
        
        # Create default templates if they don't exist
        self._create_default_templates()
    
    def generate_markdown_report(
        self,
        analysis_result: AnalysisResult,
        parsed_log: ParsedLog,
        symbol_resolutions: Optional[List[SymbolResolution]] = None,
        analysis_id: Optional[str] = None
    ) -> str:
        """Generate a Markdown report from analysis results."""
        
        report_lines = []
        
        # Header
        report_lines.append("# Firmware Log Analysis Report")
        report_lines.append("")
        report_lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        if analysis_id:
            report_lines.append(f"**Analysis ID:** {analysis_id}")
        report_lines.append("")
        
        # Executive Summary
        report_lines.append("## Executive Summary")
        report_lines.append("")
        report_lines.append(f"**Criticality:** {analysis_result.criticality_level.value.upper()}")
        report_lines.append(f"**Confidence:** {analysis_result.confidence_score:.1%}")
        if analysis_result.likely_module:
            report_lines.append(f"**Likely Module:** {analysis_result.likely_module}")
        report_lines.append("")
        report_lines.append(analysis_result.summary)
        report_lines.append("")
        
        # Recommended Actions
        report_lines.append("## Recommended Actions")
        report_lines.append("")
        report_lines.append(analysis_result.suggested_fix)
        report_lines.append("")
        
        # Technical Details
        if analysis_result.technical_details:
            report_lines.append("## Technical Details")
            report_lines.append("")
            report_lines.append(analysis_result.technical_details)
            report_lines.append("")
        
        # Log Analysis
        report_lines.append("## Log Analysis")
        report_lines.append("")
        report_lines.append(f"- **Total Lines:** {parsed_log.total_lines}")
        report_lines.append(f"- **Events Detected:** {len(parsed_log.events)}")
        
        if parsed_log.parsing_errors:
            report_lines.append(f"- **Parsing Errors:** {len(parsed_log.parsing_errors)}")
        
        report_lines.append("")
        
        # Events Summary
        if parsed_log.events:
            report_lines.append("### Detected Events")
            report_lines.append("")
            
            # Group events by type
            event_counts = {}
            for event in parsed_log.events:
                event_type = event.event_type.value
                event_counts[event_type] = event_counts.get(event_type, 0) + 1
            
            for event_type, count in sorted(event_counts.items()):
                report_lines.append(f"- **{event_type.replace('_', ' ').title()}:** {count} occurrence(s)")
            
            report_lines.append("")
            
            # Detailed events (first 5)
            report_lines.append("### Event Details")
            report_lines.append("")
            
            for i, event in enumerate(parsed_log.events[:5], 1):
                report_lines.append(f"#### Event {i}: {event.event_type.value.replace('_', ' ').title()}")
                report_lines.append("")
                report_lines.append(f"- **Line:** {event.line_number}")
                if event.timestamp:
                    report_lines.append(f"- **Timestamp:** {event.timestamp}")
                if event.function_name:
                    report_lines.append(f"- **Function:** {event.function_name}")
                if event.memory_address:
                    report_lines.append(f"- **Address:** {event.memory_address}")
                
                report_lines.append("")
                report_lines.append("**Message:**")
                report_lines.append("```")
                report_lines.append(event.message)
                report_lines.append("```")
                
                if event.stack_trace:
                    report_lines.append("")
                    report_lines.append("**Stack Trace:**")
                    report_lines.append("```")
                    for trace_line in event.stack_trace:
                        report_lines.append(trace_line)
                    report_lines.append("```")
                
                report_lines.append("")
            
            if len(parsed_log.events) > 5:
                report_lines.append(f"*... and {len(parsed_log.events) - 5} more events*")
                report_lines.append("")
        
        # Symbol Resolution
        if symbol_resolutions:
            resolved_symbols = [s for s in symbol_resolutions if s.resolved]
            if resolved_symbols:
                report_lines.append("## Symbol Resolution")
                report_lines.append("")
                report_lines.append("| Address | Function | File | Line |")
                report_lines.append("|---------|----------|------|------|")
                
                for symbol in resolved_symbols:
                    file_info = f"{symbol.file_name}:{symbol.line_number}" if symbol.file_name and symbol.line_number else symbol.file_name or "N/A"
                    report_lines.append(f"| {symbol.address} | {symbol.function_name or 'N/A'} | {file_info} | {symbol.line_number or 'N/A'} |")
                
                report_lines.append("")
        
        # Related Events
        if analysis_result.related_events:
            report_lines.append("## Related Event Types")
            report_lines.append("")
            for event_type in analysis_result.related_events:
                report_lines.append(f"- {event_type.replace('_', ' ').title()}")
            report_lines.append("")
        
        # Metadata
        if parsed_log.metadata:
            report_lines.append("## Metadata")
            report_lines.append("")
            for key, value in parsed_log.metadata.items():
                report_lines.append(f"- **{key.replace('_', ' ').title()}:** {value}")
            report_lines.append("")
        
        # Footer
        report_lines.append("---")
        report_lines.append("*Report generated by MCP Firmware Log Analysis Server*")
        
        return "\n".join(report_lines)
    
    def generate_html_report(
        self,
        analysis_result: AnalysisResult,
        parsed_log: ParsedLog,
        symbol_resolutions: Optional[List[SymbolResolution]] = None,
        analysis_id: Optional[str] = None
    ) -> str:
        """Generate an HTML report from analysis results."""
        
        # First generate markdown
        markdown_content = self.generate_markdown_report(
            analysis_result, parsed_log, symbol_resolutions, analysis_id
        )
        
        # Convert to HTML
        html_content = markdown2.markdown(
            markdown_content,
            extras=["tables", "fenced-code-blocks", "code-friendly"]
        )
        
        # Use template if available
        try:
            template = self.jinja_env.get_template("report.html")
            return template.render(
                title="Firmware Log Analysis Report",
                content=html_content,
                analysis_id=analysis_id,
                timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                criticality=analysis_result.criticality_level.value,
                confidence=f"{analysis_result.confidence_score:.1%}"
            )
        except Exception:
            # Fallback to simple HTML wrapper
            return f"""
<!DOCTYPE html>
<html>
<head>
    <title>Firmware Log Analysis Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        .header {{ background-color: #f5f5f5; padding: 20px; border-radius: 5px; }}
        .criticality-high {{ color: #d32f2f; }}
        .criticality-medium {{ color: #f57c00; }}
        .criticality-low {{ color: #388e3c; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
        pre {{ background-color: #f5f5f5; padding: 10px; border-radius: 3px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Firmware Log Analysis Report</h1>
        <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p><strong>Criticality:</strong> <span class="criticality-{analysis_result.criticality_level.value}">{analysis_result.criticality_level.value.upper()}</span></p>
    </div>
    {html_content}
</body>
</html>
"""
    
    def save_report(
        self,
        content: str,
        format_type: str = "html",
        analysis_id: Optional[str] = None
    ) -> str:
        """Save a report to disk and return the file path."""
        
        if not analysis_id:
            analysis_id = str(uuid.uuid4())[:8]
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"analysis_{analysis_id}_{timestamp}.{format_type}"
        filepath = self.reports_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return str(filepath)
    
    def get_report_url(self, filepath: str) -> str:
        """Get a URL for accessing a saved report."""
        # Convert absolute path to relative URL
        relative_path = Path(filepath).relative_to(Path.cwd())
        return f"/{relative_path}"
    
    def _create_default_templates(self):
        """Create default HTML template if it doesn't exist."""
        template_path = self.templates_dir / "report.html"
        
        if not template_path.exists():
            template_content = """<!DOCTYPE html>
<html>
<head>
    <title>{{ title }}</title>
    <meta charset="utf-8">
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background-color: #f8f9fa;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 30px;
        }
        .header h1 {
            margin: 0;
            font-size: 2em;
        }
        .meta-info {
            display: flex;
            gap: 20px;
            margin-top: 10px;
            font-size: 0.9em;
        }
        .criticality-badge {
            padding: 4px 12px;
            border-radius: 20px;
            font-weight: bold;
            text-transform: uppercase;
        }
        .criticality-high {
            background-color: #ffebee;
            color: #c62828;
        }
        .criticality-medium {
            background-color: #fff3e0;
            color: #ef6c00;
        }
        .criticality-low {
            background-color: #e8f5e8;
            color: #2e7d32;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        th {
            background-color: #f5f5f5;
            font-weight: 600;
        }
        pre {
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            border-left: 4px solid #007bff;
            overflow-x: auto;
        }
        code {
            background-color: #f8f9fa;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Monaco', 'Consolas', monospace;
        }
        .footer {
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #eee;
            text-align: center;
            color: #666;
            font-size: 0.9em;
        }
        h2 {
            color: #333;
            border-bottom: 2px solid #007bff;
            padding-bottom: 5px;
        }
        h3 {
            color: #555;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{{ title }}</h1>
            <div class="meta-info">
                <span><strong>Generated:</strong> {{ timestamp }}</span>
                {% if analysis_id %}
                <span><strong>Analysis ID:</strong> {{ analysis_id }}</span>
                {% endif %}
                <span class="criticality-badge criticality-{{ criticality }}">{{ criticality.upper() }}</span>
                <span><strong>Confidence:</strong> {{ confidence }}</span>
            </div>
        </div>
        
        <div class="content">
            {{ content|safe }}
        </div>
        
        <div class="footer">
            <p>Report generated by MCP Firmware Log Analysis Server</p>
        </div>
    </div>
</body>
</html>"""
            
            with open(template_path, 'w', encoding='utf-8') as f:
                f.write(template_content) 