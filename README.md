# 🔧 MCP Firmware Log Analysis Server

An intelligent, AI-powered firmware log analysis system built with GPT-4 integration for embedded systems debugging. This comprehensive tool helps firmware developers quickly identify, analyze, and resolve critical issues in embedded systems through automated log parsing and expert-level analysis.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.8+-green.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-red.svg)
![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4-orange.svg)

## 🌟 Features

### 🤖 AI-Powered Analysis
- **GPT-4 Integration**: Expert-level firmware debugging insights
- **Root Cause Analysis**: Identifies specific issues and failure patterns
- **Actionable Recommendations**: Provides concrete debugging steps
- **Confidence Scoring**: 90-95% accuracy for critical issues
- **Module Identification**: Pinpoints likely source files and functions

### 🔍 Comprehensive Log Parsing
- **Multi-Format Support**: `.log`, `.txt`, `.json` files
- **Event Detection**: Hard faults, watchdog resets, sensor failures, assertions, panics
- **Timeline Analysis**: Correlates events across time sequences
- **Memory Address Parsing**: Extracts stack traces and memory addresses
- **Metadata Extraction**: System info, timestamps, error codes

### 🛠️ Advanced Debugging Features
- **Symbol Resolution**: ELF binary analysis with `addr2line` integration
- **Stack Trace Analysis**: Detailed call stack examination
- **Hardware Fault Detection**: Bus faults, memory errors, peripheral failures
- **Boot Sequence Analysis**: Startup and initialization issue detection

### 📊 Rich Reporting
- **HTML Reports**: Beautiful, styled analysis reports
- **JSON API**: Structured data for integration
- **Markdown Export**: Documentation-ready format
- **Event Timelines**: Visual event correlation
- **Technical Details**: Memory addresses, register states, system context

### 🌐 Multiple Interfaces
- **Web Interface**: Drag-and-drop file upload at `http://localhost:8000`
- **REST API**: Programmatic integration endpoints
- **CLI Tool**: Command-line analysis for automation
- **Batch Processing**: Multiple file analysis support

## 🚀 Quick Start

### Prerequisites
- Python 3.8+ 
- OpenAI API key (for GPT-4 analysis)
- Optional: `addr2line` tool (for ELF symbol resolution)

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/ashishdhiman23/mcp-firmware-agent.git
cd mcp-firmware-agent
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure environment**
```bash
# Create .env file
echo "OPENAI_API_KEY=your_openai_api_key_here" > .env
```

4. **Start the server**
```bash
# Easy method (recommended)
python run_server.py

# Or using uvicorn directly
python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000
```

5. **Open web interface**
```bash
open http://localhost:8000
```

## 📚 Usage Examples

### Web Interface
1. Navigate to `http://localhost:8000`
2. Upload your firmware log file
3. View comprehensive analysis results
4. Download HTML/Markdown reports

### REST API
```bash
# Analyze a log file
curl -X POST "http://localhost:8000/analyze-log" \
     -F "log_file=@firmware_crash.log"

# Check server health
curl http://localhost:8000/health
```

### CLI Tool
```bash
# Basic analysis
python -m src.cli analyze firmware_crash.log

# JSON output
python -m src.cli analyze firmware_crash.log --format json

# With ELF binary for symbol resolution
python -m src.cli analyze firmware_crash.log --elf firmware.elf
```

## 🔧 API Documentation

### Endpoints

#### `POST /analyze-log`
Analyze firmware log files with optional ELF binaries.

**Parameters:**
- `log_file`: Log file (`.log`, `.txt`, `.json`)
- `elf_file`: Optional ELF binary for symbol resolution

**Response:**
```json
{
  "analysis_id": "abc123",
  "timestamp": "2024-01-01T12:00:00Z",
  "analysis_result": {
    "summary": "Hard fault due to I2C sensor failure",
    "suggested_fix": "Check sensor at I2C address 0x48",
    "confidence_score": 0.95,
    "likely_module": "sensor_driver.c",
    "criticality_level": "high",
    "technical_details": "Detailed technical analysis...",
    "related_events": ["hard_fault", "sensor_failure"]
  },
  "parsed_log": {
    "total_lines": 26,
    "events": [...],
    "metadata": {...}
  },
  "symbol_resolutions": [...],
  "processing_time_ms": 1250
}
```

#### `GET /health`
Check server health and configuration status.

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "openai_configured": true,
  "timestamp": "2024-01-01T12:00:00Z"
}
```

## 🔍 Supported Log Formats

### Traditional Logs
```
[00:00:01.123] INFO: System startup complete
[00:00:02.234] ERROR: I2C error reading sensor at address 0x48
[00:00:02.235] PANIC: Hard fault detected
```

### JSON Logs
```json
{
  "timestamp": "00:00:02.234",
  "level": "ERROR",
  "message": "Assertion failed",
  "file": "sensor_init.c",
  "line": 45,
  "function": "sensor_init"
}
```

### Stack Traces
```
Stack trace:
  0x08001000 in main()
  0x08002000 in sensor_init()
  0x08003000 in i2c_read()
```

## 🧠 AI Analysis Examples

### Hard Fault Analysis
**GPT-4 Analysis:**
- **Summary**: Hard fault due to repeated I2C sensor failures  
- **Root Cause**: Sensor at I2C address 0x48 becoming unresponsive
- **Recommendation**: Check sensor hardware, verify I2C bus integrity
- **Module**: `sensor_driver.c`
- **Confidence**: 90%

### Watchdog Reset Analysis  
**GPT-4 Analysis:**
- **Summary**: System became unresponsive, likely infinite loop
- **Root Cause**: Blocking operation preventing watchdog refresh
- **Recommendation**: Add watchdog refresh points, review timeout values
- **Technical Details**: Watchdog reset mechanism explanation
- **Confidence**: 85%

### Assertion Failure Analysis
**GPT-4 Analysis:**
- **Summary**: Assertion failure in sensor initialization
- **Root Cause**: Precondition not met in `sensor_init()` at line 45
- **Recommendation**: Review assertion condition, check initialization sequence
- **Module**: `sensor_init.c`  
- **Confidence**: 95%

## 🛠️ Configuration

### Environment Variables
```bash
# OpenAI Configuration
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-4                    # Default: gpt-4
OPENAI_MAX_TOKENS=2000               # Default: 2000
OPENAI_TEMPERATURE=0.3               # Default: 0.3

# Server Configuration  
HOST=0.0.0.0                         # Default: 0.0.0.0
PORT=8000                            # Default: 8000
DEBUG=false                          # Default: false

# Analysis Configuration
MAX_LOG_LINES=10000                  # Default: 10000
CONFIDENCE_THRESHOLD=0.5             # Default: 0.5
```

### File Limits
- **Max file size**: 50MB
- **Supported extensions**: `.log`, `.txt`, `.json`, `.elf`, `.bin`
- **Max log lines**: 10,000 (configurable)

## 📁 Project Structure

```
mcp_firmware_agent/
├── src/
│   ├── api/                 # FastAPI web server
│   │   ├── main.py         # Main API application
│   │   └── routes.py       # API route definitions
│   ├── analyzers/          # Analysis engines
│   │   ├── gpt_analyzer.py # GPT-4 integration
│   │   └── report_generator.py # Report generation
│   ├── parsers/            # Log parsing modules
│   │   ├── log_parser.py   # Main log parser
│   │   └── elf_parser.py   # ELF binary parser
│   ├── utils/              # Utility modules
│   │   ├── file_handler.py # File operations
│   │   └── analysis_service.py # Analysis orchestration
│   ├── models.py           # Pydantic data models
│   ├── config.py           # Configuration management
│   └── cli.py              # Command-line interface
├── test_logs/              # Sample log files
│   ├── sample_crash.log    # Hard fault example
│   ├── sample_watchdog.log # Watchdog reset example
│   └── sample_json.log     # JSON format example
├── tests/                  # Unit and integration tests
├── templates/              # HTML report templates
├── reports/                # Generated analysis reports
├── requirements.txt        # Python dependencies
├── .env                    # Environment configuration
└── README.md              # This documentation
```

## 🧪 Testing

### Run Tests
```bash
# All tests
pytest tests/

# Unit tests only
pytest tests/unit/

# Integration tests
pytest tests/integration/

# With coverage
pytest --cov=src tests/
```

### Sample Log Analysis
```bash
# Test with provided samples
python -m src.cli analyze test_logs/sample_crash.log
python -m src.cli analyze test_logs/sample_watchdog.log  
python -m src.cli analyze test_logs/sample_json.log
```

## 🔧 Development

### Setup Development Environment
```bash
# Install development dependencies
pip install -r requirements.txt pytest pytest-asyncio pytest-cov

# Run with auto-reload
python -m uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

### Architecture Overview
1. **Log Parsing**: Multi-format log parsing with event detection
2. **AI Analysis**: GPT-4 integration for intelligent insights  
3. **Symbol Resolution**: ELF binary analysis for memory addresses
4. **Report Generation**: Multi-format output with rich styling
5. **Web Interface**: Modern React-like UI for file uploads
6. **API Layer**: RESTful endpoints for programmatic access

## 🚀 Deployment

### Docker Deployment
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["python", "-m", "uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Production Considerations
- Set `DEBUG=false` in production
- Use environment variables for sensitive configuration
- Configure proper logging levels
- Set up reverse proxy (nginx/traefik)
- Enable HTTPS/TLS termination

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines
- Follow PEP 8 style guide
- Add tests for new features
- Update documentation
- Ensure type hints are present
- Add docstrings for public functions

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **OpenAI GPT-4**: Powering intelligent firmware analysis
- **FastAPI**: Modern, fast web framework
- **Pydantic**: Data validation and settings management
- **Uvicorn**: Lightning-fast ASGI server
- **Jinja2**: Template engine for report generation

## 📞 Support

- **Documentation**: [GitHub Wiki](https://github.com/ashishdhiman23/mcp-firmware-agent/wiki)
- **Issues**: [GitHub Issues](https://github.com/ashishdhiman23/mcp-firmware-agent/issues)
- **Discussions**: [GitHub Discussions](https://github.com/ashishdhiman23/mcp-firmware-agent/discussions)

---

**Built with ❤️ for embedded systems developers** 