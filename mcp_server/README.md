# File Generator MCP Server

このMCPサーバーは、構造化されたMarkdownファイルからファイルを生成するためのツールを提供します。

## 機能

- Markdownファイルから複数のファイルを一括生成
- ファイル構造とコンテンツの管理
- エラーハンドリングと詳細なレポート

## 使用方法

### MCPサーバーとして実行

#### 標準入出力モード（デフォルト）
```bash
python server.py
```

#### リモートTCPサーバーモード
```bash
# ローカルホストで起動
python server.py --host localhost --port 8000

# 特定のIPアドレスで起動
python server.py --host 192.168.1.100 --port 8000

# 全てのネットワークインターフェースで起動
python server.py --host 0.0.0.0 --port 8000
```

#### ログ設定オプション
```bash
# ログレベルを指定
python server.py --log-level DEBUG

# カスタムログ設定ファイルを使用
python server.py --log-config my_logging_config.json

# 組み合わせ例
python server.py --host 0.0.0.0 --port 8000 --log-level DEBUG --log-config logging_config.json
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

### Claude DesktopのMCP設定例

#### 標準入出力モード
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

#### リモートTCPサーバーモード
TCPサーバーモードを使用する場合は、まずサーバーを起動してから、MCPクライアントで接続します：

```bash
# サーバーを起動
python server.py --host localhost --port 8000
```

TCPサーバーモードでは、WebSocketやSSEを使用したMCPクライアントから接続できます。

## ログ設定

### デフォルトログ設定

サーバーは以下のログファイルを自動的に作成します：

- `logs/mcp_server.log`: 全てのログメッセージ（デバッグ情報含む）
- `logs/mcp_server_errors.log`: エラーレベル以上のログメッセージのみ

### ログ設定ファイル

#### デフォルト設定ファイル（logging_config.json）

プロジェクトには `logging_config.json` が含まれており、以下の設定が可能です：

- **ログレベル**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **ログローテーション**: 10MB毎に自動ローテーション（最大5ファイル保持）
- **フォーマット**: 詳細なログフォーマット（タイムスタンプ、ファイル名、行番号、関数名を含む）
- **出力先**: コンソール、ファイル、エラーファイルの3つの出力先

#### カスタム設定ファイルの作成

独自のログ設定を作成する場合、以下のJSONフォーマットを使用してください：

```json
{
  "version": 1,
  "disable_existing_loggers": false,
  "formatters": {
    "detailed": {
      "format": "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s - %(message)s",
      "datefmt": "%Y-%m-%d %H:%M:%S"
    }
  },
  "handlers": {
    "console": {
      "class": "logging.StreamHandler",
      "level": "INFO",
      "formatter": "detailed",
      "stream": "ext://sys.stderr"
    },
    "file": {
      "class": "logging.handlers.RotatingFileHandler",
      "level": "DEBUG",
      "formatter": "detailed",
      "filename": "logs/mcp_server.log",
      "maxBytes": 10485760,
      "backupCount": 5,
      "encoding": "utf8"
    }
  },
  "loggers": {
    "mcp_file_generator": {
      "level": "DEBUG",
      "handlers": ["console", "file"],
      "propagate": false
    }
  }
}
```

### ログ設定の使用方法

1. **デフォルト設定を使用**: 追加設定不要、自動的に `logging_config.json` を使用
2. **カスタム設定ファイルを使用**: `--log-config` オプションで指定
3. **ログレベルのみ変更**: `--log-level` オプションで指定

### ログファイルの場所

- ログファイルは `logs/` ディレクトリに保存されます
- ディレクトリが存在しない場合は自動的に作成されます
- ログファイルは自動的にローテーションされ、古いファイルは圧縮されます

### トラブルシューティング

**ログファイルが作成されない場合**:
- `logs/` ディレクトリの書き込み権限を確認してください
- ディスク容量が十分にあることを確認してください

**ログレベルが反映されない場合**:
- コマンドラインオプション `--log-level` が正しく指定されているか確認してください
- 設定ファイルの JSON フォーマットが正しいことを確認してください
