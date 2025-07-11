# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Code Catalyst is a modern Python application development project that includes an MCP (Model Control Protocol) server for generating files from structured Markdown content. The project serves as a comprehensive file generation platform for AI agents, featuring advanced logging, remote connectivity, and robust error handling.

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

### Testing and Quality Assurance
```bash
# Run tests with coverage
python -m pytest --cov=mcp_server --cov-report=html --cov-report=term-missing

# Run code quality checks
flake8 .
black --check .
isort --check-only .

# Security and dependency checks
bandit -r .
safety check

# Format code
black .
isort .

# Complete quality pipeline
flake8 . && black --check . && isort --check-only . && pytest --cov
```

### MCP Server Operations
```bash
# Start MCP server (stdio mode)
cd mcp_server
python server.py

# Start MCP server (TCP mode)
python server.py --host localhost --port 8000
python server.py --host 0.0.0.0 --port 8000  # All interfaces

# Start with custom logging
python server.py --log-level DEBUG --log-config logging_config.json

# Test with standalone script
python standalone.py input.md -d output_directory
```

## Architecture

### Core Components

1. **MCP Server (`mcp_server/`)**
   - `server.py`: Main MCP server implementation with asyncio and advanced logging
   - `standalone.py`: Standalone version for testing and debugging
   - `logging_config.json`: Comprehensive logging configuration
   - Provides `generate_files_from_markdown` tool for AI agents

2. **File Generation Logic**
   - Parses structured Markdown with `## ./filepath` sections
   - Extracts code blocks and file content using regex
   - Creates directory structure and writes files atomically
   - Supports change descriptions and file metadata
   - Comprehensive error handling and logging

3. **Logging System**
   - Structured logging with multiple output destinations
   - Configurable log levels and formats
   - Automatic log rotation (10MB, 5 files)
   - Separate error logs for critical issues

### MCP Server Architecture

The MCP server implements the Model Control Protocol to expose file generation capabilities to AI agents:

- **Tool**: `generate_files_from_markdown`
- **Input**: Markdown file path and root directory
- **Processing**: Regex-based parsing of structured Markdown sections
- **Output**: Generated files with detailed creation reports
- **Logging**: Comprehensive operation tracking and error reporting

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

## Development Rules and Best Practices

### Code Quality Standards

1. **Python Style**
   - Follow PEP 8 with Black formatter (88 character line length)
   - Use isort for import organization
   - Maintain type hints where applicable

2. **Testing Requirements**
   - **Target Coverage**: 80% line coverage, 75% branch coverage
   - Write unit tests for all new functions
   - Include integration tests for MCP server operations
   - Test error handling and edge cases

3. **Security Practices**
   - Run bandit security checks before commits
   - Use safety for dependency vulnerability scanning
   - Sanitize all user inputs
   - Log security-relevant events

### Development Workflow

1. **Pre-development**
   ```bash
   # Quality check before starting
   flake8 . && black --check . && isort --check-only . && pytest
   ```

2. **During development**
   ```bash
   # Auto-format and organize
   black . && isort .
   
   # Run tests frequently
   pytest -v
   ```

3. **Pre-commit**
   ```bash
   # Complete quality pipeline
   flake8 . && black --check . && isort --check-only . && pytest --cov && bandit -r . && safety check
   ```

### Branch Strategy

The project uses GitFlow with strict PR requirements:
- `main`: Production branch with tags (v1.2.0)
- `develop`: Development integration branch  
- `staging`: UAT and testing branch
- `feature/*`, `fix/*`, `refactor/*`: Working branches

**Critical**: All merges between branches must go through Pull Requests. Direct pushes to `main`, `staging`, and `release/*` branches are prohibited.

### Git Workflow Rules

1. **Branch Creation**
   - Create feature branches from `develop`
   - Use descriptive branch names: `feature/enhanced-logging`, `fix/markdown-parsing`

2. **Commit Standards**
   - Use conventional commit messages
   - Include 🤖 Generated with [Claude Code](https://claude.ai/code) footer
   - Reference issue numbers when applicable

3. **Pull Request Requirements**
   - All quality checks must pass
   - Include tests for new functionality
   - Update documentation as needed
   - Peer review required

## Development Configuration

### Python Configuration
- **Python Version**: 3.12+ required
- **Build System**: setuptools with pyproject.toml
- **Code Style**: Black (88 character line length)
- **Import Sorting**: isort (black profile)
- **Testing**: pytest with coverage reporting

### Test Configuration
- **Framework**: pytest
- **Test Discovery**: `tests/` directory
- **File Patterns**: `test_*.py`, `*_test.py`
- **Coverage**: HTML and terminal reporting
- **Mocking**: pytest-mock for complex scenarios

### Logging Configuration
- **File Locations**: `logs/mcp_server.log`, `logs/mcp_server_errors.log`
- **Rotation**: 10MB per file, 5 files maximum
- **Levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Format**: Structured with timestamp, module, function, and line number

## Important Implementation Notes

### MCP Server Specifics
- The MCP server uses regex parsing for Markdown sections - be careful with format changes
- File generation creates directories automatically but will overwrite existing files
- All MCP operations are async and support both stdio and TCP modes
- The standalone script can be used for testing without MCP infrastructure

### Error Handling
- Use structured logging for all errors
- Implement graceful degradation for non-critical failures
- Provide meaningful error messages to users
- Log stack traces for debugging purposes

### Performance Considerations
- Log file operations at appropriate levels
- Use async operations for I/O intensive tasks
- Implement connection pooling for TCP mode
- Monitor memory usage during large file operations

## Troubleshooting

### Common Issues
1. **Import Errors**: Ensure virtual environment is activated
2. **Test Failures**: Check if all dependencies are installed
3. **Logging Issues**: Verify logs directory permissions
4. **MCP Connection**: Check host/port configuration

### Debug Commands
```bash
# Enable debug logging
python server.py --log-level DEBUG

# Run specific test
pytest tests/test_specific.py -v

# Check code coverage
pytest --cov=mcp_server --cov-report=html

# View logs
tail -f logs/mcp_server.log
```

## Platform Support

Code Catalyst supports the following platforms:
- **macOS**: x64 / ARM64 (Apple Silicon)
- **Windows**: x64 / ARM64  
- **Linux**: x64 / ARM64

Ensure cross-platform compatibility when making changes to file operations and path handling.


# claude code 指示書
---
## git worktree 利用指示書
このプロジェクトでは、Gitのブランチ管理に git worktree を全面的に採用します。git stash や git checkout によるブランチ切り替えは行わず、各タスク（機能開発、バグ修正など）を独立したディレクトリで作業することで、コンテキストスイッチのコストを最小限にし、依存関係の衝突を防ぎます。

- 1タスク = 1ワークツリー: 新しい機能開発やバグ修正に着手する際は、必ず新しいワークツリーを作成してください。
- 命名規則の遵守: ワークツリーのディレクトリ名とブランチ名は、[種別]/[タスク概要] の形式で統一します。
- ベースブランチ: 新しいワークツリーは、常に最新の main または develop ブランチから作成してください。
- コマンドの厳守:
  - 新しいワークツリーの作成は、必ず以下の単一コマンドで行ってください。これにより、ブランチの新規作成とワークツリーの追加を一度に実行します。
    ```bash
    git worktree add -b <新ブランチ名> ./<新ディレクトリ名> <ベースブランチ>
    ```
  - git checkout -b で先にブランチを作成する行為は禁止します。
- クリーンアップの徹底: プルリクエストがマージされた後、その作業に使用したワークツリーとブランチは速やかに削除してください。
- 同時編集の禁止: 絶対に同じブランチを複数のワークツリーで同時に開かないでください。

---
## Gemini CLI 連携ガイド
### 目的1
ユーザーが **「Geminiと相談しながら進めて」** （または同義語）と指示した場合、claude code は以降のタスクを **Gemini CLI** と協調しながら進めること。
Gemini から得た回答はそのまま提示し、claude code 自身の解説・統合も付け加えることで、両エージェントの知見を融合する。

#### トリガー
- 正規表現: `/Gemini.*相談しながら/`
- 例:
- 「Geminiと相談しながら進めて」
- 「この件、Geminiと話しつつやりましょう」

#### 基本フロー
1. **PROMPT 生成**
claude code はユーザーからの要求を 1 つのテキストにまとめ、環境変数 `$PROMPT` に格納する。

2. **Gemini CLI 呼び出し**
```bash
gemini <<EOF
$PROMPT
EOF
```

### 目的2
claude code にて情報が不足している場合は、 **Gemini CLI** を使用してwebから最新の情報を取得することができます。

#### トリガー
- claude code が知らないことを問われた
- 例：
- 「Open AI の realtime を使用して」

#### 基本フロー
`gemini` is google gemini cli. You can use it for web search.

Run web search via Task Tool with `gemini -p 'WebSearch: ...'`.

```bash
gemini -p "WebSearch: ..."
```

---

## 開発手順

下記開発ルールに従って、ユーザーからの指示に対応して下さい。

**指示書**
```md
下記開発ルールと技術制約に従い、指示書の対応を実施してください。

# 開発手順
1. 要求を理解する
1. 必要な情報を集める
1. git worktree を使用して作業ブランチ（開発用）を作成する
1. テストコードを作成する
1. 実装する
1. コード品質保証戦略に従ってコード品質を保証する
1. テスト戦略に従って品質を保証する
1. 機能強化・改善を行なう場合は、コードだけでなくテストコードとドキュメントの修正も併せて実施する
1. 変更点を github にプッシュし、github actionsが成功するまで改善する。github actions が実施されない場合は後続のタスクを実施する
1. developブランチへのPRを作成する

# 指示書
- ＜ユーザーからの指示＞
```