# File Generator MCP Server

このMCPサーバーは、構造化されたMarkdownファイルからファイルを生成するためのツールを提供します。

## 機能

- Markdownファイルから複数のファイルを一括生成
- ファイル構造とコンテンツの管理
- エラーハンドリングと詳細なレポート

## 使用方法

### MCPサーバーとして実行

```bash
python server.py
```

### ツールの使用

MCPクライアントから以下のツールを使用できます：

#### generate_files_from_markdown

Markdownファイルから構造化されたファイルを生成します。

**パラメータ:**
- `input_file_path`: 入力ファイルのフルパス
- `root_directory`: ファイル生成のルートディレクトリ

**例:**
```json
{
  "name": "generate_files_from_markdown",
  "arguments": {
    "input_file_path": "/path/to/input.md",
    "root_directory": "/path/to/output"
  }
}
```

## Markdownファイルの形式

入力Markdownファイルは以下の形式に従う必要があります：

```markdown
## ./path/to/file.ext

### 変更内容
ファイルの変更内容の説明（オプション）

### ./path/to/file.ext
```language
ファイルの内容
```

## 依存関係

- Python 3.12+
- mcp >= 0.5.0

## インストール

```bash
pip install mcp
```

## 設定

Claude DesktopのMCP設定例：

```json
{
  "mcpServers": {
    "file-generator": {
      "command": "python",
      "args": ["/path/to/mcp_server/server.py"]
    }
  }
}
```
