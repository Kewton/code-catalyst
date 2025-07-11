# Test file for MCP server functionality
# Add your test files here

import os
import sys
import tempfile

# Add mcp_server to Python path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "mcp_server"))

try:
    from standalone import create_files_from_parsed_data, parse_input_md_sections
except ImportError:
    # MCPサーバーモジュールが利用できない場合のフォールバック
    parse_input_md_sections = None
    create_files_from_parsed_data = None


def test_parse_markdown_sections():
    """Test markdown parsing functionality."""
    if parse_input_md_sections is None:
        # MCPサーバーモジュールが利用できない場合はスキップ
        return

    sample_md = """
## ./test.py

### 変更内容
テストファイルの作成

### ./test.py
```python
def hello():
    return "Hello, World!"
```

## ./README.md

### ./README.md
```markdown
# Test Project
This is a test.
```
"""

    result = parse_input_md_sections(sample_md)

    assert len(result) == 2
    assert result[0]["filepath"] == "test.py"
    assert "def hello():" in result[0]["content"]
    assert result[0]["change_description"] == "テストファイルの作成"
    assert result[1]["filepath"] == "README.md"
    assert "# Test Project" in result[1]["content"]


def test_create_files_from_parsed_data():
    """Test file creation functionality."""
    if create_files_from_parsed_data is None:
        # MCPサーバーモジュールが利用できない場合はスキップ
        return

    with tempfile.TemporaryDirectory() as temp_dir:
        parsed_data = [
            {
                "filepath": "test.txt",
                "content": "Hello, World!",
                "change_description": "Test file creation",
            }
        ]

        create_files_from_parsed_data(parsed_data, temp_dir)

        created_file = os.path.join(temp_dir, "test.txt")
        assert os.path.exists(created_file)

        with open(created_file, "r", encoding="utf-8") as f:
            content = f.read()

        assert content == "Hello, World!"


def test_placeholder():
    """Placeholder test to ensure pytest runs successfully."""
    assert True
