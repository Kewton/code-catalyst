# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Code Catalyst is a Python application development project that includes an MCP (Model Control Protocol) server for generating files from structured Markdown content. The project is designed to help AI agents create and manage files through a standardized interface.

## Key Commands

### Development Setup
```bash
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install dev dependencies
pip install -e ".[dev]"
```

### Testing and Quality
```bash
# Run tests
pytest

# Run linting
flake8 .

# Run security checks
bandit -r .
safety check

# Format code
black .
isort .
```

### MCP Server Operations
```bash
# Start MCP server (stdio mode)
cd mcp_server
python server.py

# Start MCP server (TCP mode)
python server.py --host localhost --port 8000
python server.py --host 0.0.0.0 --port 8000  # All interfaces

# Test with standalone script
python standalone.py input.md -d output_directory
```

## Architecture

### Core Components

1. **MCP Server (`mcp_server/`)**
   - `server.py`: Main MCP server implementation using asyncio
   - `standalone.py`: Standalone version for testing and debugging
   - Provides `generate_files_from_markdown` tool for AI agents

2. **File Generation Logic**
   - Parses structured Markdown with `## ./filepath` sections
   - Extracts code blocks and file content
   - Creates directory structure and writes files
   - Supports change descriptions and file metadata

### MCP Server Architecture

The MCP server implements the Model Control Protocol to expose file generation capabilities to AI agents:

- **Tool**: `generate_files_from_markdown`
- **Input**: Markdown file path and root directory
- **Processing**: Regex-based parsing of structured Markdown sections
- **Output**: Generated files with detailed creation reports

### Markdown Format Requirements

Input Markdown files must follow this structure:
```markdown
## ./path/to/file.ext

### 変更内容
Optional change description

### ./path/to/file.ext
```language
File content here
```
```

## Branch Strategy

The project uses GitFlow with strict PR requirements:
- `main`: Production branch with tags (v1.2.0)
- `develop`: Development integration branch  
- `staging`: UAT and testing branch
- `feature/*`, `fix/*`, `refactor/*`: Working branches

**Critical**: All merges between branches must go through Pull Requests. Direct pushes to `main`, `staging`, and `release/*` branches are prohibited.

## Development Configuration

### Python Configuration
- **Python Version**: 3.12+ required
- **Build System**: setuptools with pyproject.toml
- **Code Style**: Black (88 character line length)
- **Import Sorting**: isort (black profile)

### Test Configuration
- **Framework**: pytest
- **Test Discovery**: `tests/` directory
- **File Patterns**: `test_*.py`, `*_test.py`

## Important Notes

- The MCP server uses regex parsing for Markdown sections - be careful with format changes
- File generation creates directories automatically but will overwrite existing files
- All MCP operations are async and use stdio for communication
- The standalone script can be used for testing without MCP infrastructure