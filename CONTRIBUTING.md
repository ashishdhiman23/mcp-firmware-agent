# Contributing to MCP Firmware Agent

Thank you for your interest in contributing to the MCP Firmware Agent! This document provides guidelines and information for contributors.

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- Git
- OpenAI API key (for testing GPT-4 features)

### Setting Up Development Environment

1. **Fork and clone the repository**
```bash
git clone https://github.com/ashishdhiman23/mcp-firmware-agent.git
cd mcp-firmware-agent
```

2. **Create a virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install development dependencies**
```bash
pip install -r requirements.txt
pip install pytest pytest-asyncio pytest-cov black flake8 mypy
```

4. **Set up environment**
```bash
cp .env.example .env
# Edit .env with your OpenAI API key
```

5. **Run tests to verify setup**
```bash
pytest tests/
```

## 📝 Development Guidelines

### Code Style
- Follow PEP 8 style guide
- Use type hints for all function parameters and return values
- Maximum line length: 100 characters
- Use descriptive variable and function names

### Code Formatting
We use `black` for code formatting:
```bash
black src/ tests/
```

### Linting
We use `flake8` for linting:
```bash
flake8 src/ tests/
```

### Type Checking
We use `mypy` for type checking:
```bash
mypy src/
```

### Documentation
- Add docstrings to all public functions and classes
- Use Google-style docstrings
- Update README.md for new features
- Add inline comments for complex logic

Example docstring:
```python
def analyze_log(log_content: str, elf_binary: Optional[bytes] = None) -> AnalysisResult:
    """Analyze firmware log content for issues and anomalies.
    
    Args:
        log_content: Raw log content as string
        elf_binary: Optional ELF binary for symbol resolution
        
    Returns:
        AnalysisResult containing parsed events and AI analysis
        
    Raises:
        ValueError: If log content is empty or invalid
        OpenAIError: If GPT-4 analysis fails
    """
```

## 🧪 Testing

### Test Structure
```
tests/
├── unit/           # Unit tests for individual modules
├── integration/    # Integration tests for API endpoints
├── fixtures/       # Test data and mock objects
└── conftest.py     # Pytest configuration
```

### Writing Tests
- Write tests for all new functionality
- Aim for >90% code coverage
- Use descriptive test names
- Include both positive and negative test cases

Example test:
```python
def test_log_parser_detects_hard_fault():
    """Test that log parser correctly identifies hard fault events."""
    log_content = "[00:00:01.123] PANIC: Hard fault detected at PC=0x08001234"
    parser = LogParser()
    
    result = parser.parse(log_content)
    
    assert len(result.events) == 1
    assert result.events[0].event_type == EventType.HARD_FAULT
    assert result.events[0].memory_address == "0x08001234"
```

### Running Tests
```bash
# All tests
pytest

# Unit tests only
pytest tests/unit/

# Integration tests only
pytest tests/integration/

# With coverage report
pytest --cov=src --cov-report=html

# Specific test file
pytest tests/unit/test_log_parser.py

# Specific test function
pytest tests/unit/test_log_parser.py::test_parse_hard_fault
```

## 🔄 Pull Request Process

### Before Submitting
1. **Create a feature branch**
```bash
git checkout -b feature/your-feature-name
```

2. **Make your changes**
- Follow coding guidelines
- Add tests for new functionality
- Update documentation

3. **Run the full test suite**
```bash
# Code formatting
black src/ tests/

# Linting
flake8 src/ tests/

# Type checking
mypy src/

# Tests
pytest --cov=src
```

4. **Commit your changes**
```bash
git add .
git commit -m "feat: add support for new log format"
```

### Commit Message Format
Use conventional commits format:
- `feat:` new feature
- `fix:` bug fix
- `docs:` documentation changes
- `style:` formatting changes
- `refactor:` code refactoring
- `test:` adding tests
- `chore:` maintenance tasks

### Pull Request Template
When creating a PR, please include:

**Description**
Brief description of the changes and motivation.

**Type of Change**
- [ ] Bug fix (non-breaking change that fixes an issue)
- [ ] New feature (non-breaking change that adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

**Testing**
- [ ] Tests pass locally
- [ ] New tests added for new functionality
- [ ] Coverage maintained/improved

**Checklist**
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No merge conflicts

## 🐛 Bug Reports

When reporting bugs, please include:

1. **Environment details**
   - Python version
   - Operating system
   - Package versions

2. **Steps to reproduce**
   - Minimal code example
   - Input data (if applicable)
   - Expected vs actual behavior

3. **Error messages**
   - Full stack traces
   - Log outputs

## 💡 Feature Requests

For feature requests, please include:

1. **Use case description**
   - What problem does this solve?
   - Who would benefit?

2. **Proposed solution**
   - High-level implementation approach
   - API changes (if applicable)

3. **Alternatives considered**
   - Other approaches evaluated
   - Why this solution is preferred

## 📚 Architecture Overview

### Core Components

1. **Log Parsers** (`src/parsers/`)
   - Extract events from various log formats
   - Handle timestamps, error codes, stack traces

2. **AI Analyzers** (`src/analyzers/`)
   - GPT-4 integration for intelligent analysis
   - Rule-based fallback analysis

3. **Symbol Resolution** (`src/parsers/elf_parser.py`)
   - ELF binary parsing
   - Address-to-symbol mapping

4. **API Layer** (`src/api/`)
   - FastAPI endpoints
   - File upload handling
   - Response formatting

5. **Report Generation** (`src/analyzers/report_generator.py`)
   - HTML/Markdown report creation
   - Templating engine integration

### Adding New Features

#### New Log Format Support
1. Extend `LogParser` class
2. Add format detection logic
3. Implement event extraction
4. Add tests with sample logs

#### New Analysis Engine
1. Create analyzer class in `src/analyzers/`
2. Implement `analyze_log()` method
3. Integrate with main analysis service
4. Add configuration options

#### New API Endpoint
1. Add route in `src/api/main.py`
2. Implement request/response models
3. Add input validation
4. Write integration tests

## 🤝 Community

- **GitHub Discussions**: For questions and general discussion
- **GitHub Issues**: For bug reports and feature requests
- **Pull Requests**: For code contributions

## 📄 License

By contributing to this project, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to make firmware debugging easier for everyone! 🚀 