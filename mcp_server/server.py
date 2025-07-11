#!/usr/bin/env python3
"""
MCP Server for File Generation from Markdown

This MCP server provides a tool to generate files from markdown content.
It parses markdown files and creates files based on the structured content.
Can be run as stdio server or TCP server for remote connections.
"""

import argparse
import asyncio
import logging
import os
import re
import sys
from datetime import datetime
from typing import Any, Dict, List

from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolResult,
    ListToolsResult,
    TextContent,
    Tool,
)


def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """
    詳細なログ設定を行う

    Args:
        log_level: ログレベル (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Returns:
        Logger: 設定されたロガー
    """
    logger = logging.getLogger("mcp_file_generator")
    logger.setLevel(getattr(logging, log_level.upper()))

    # ハンドラーが既に存在する場合は削除
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # フォーマッターを設定
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s - %(message)s"
    )

    # コンソールハンドラー
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # ファイルハンドラー（オプション）
    try:
        file_handler = logging.FileHandler("mcp_server.log")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        logger.warning(f"ログファイルの作成に失敗しました: {e}")

    return logger


# グローバルロガー
logger = setup_logging()

# MCPサーバーの設定
server = Server("file-generator-mcp")


@server.list_tools()
async def handle_list_tools() -> ListToolsResult:
    """
    利用可能なツールのリストを返す
    """
    logger.info("ツールリストの要求を受信")
    tools = [
        Tool(
            name="generate_files_from_markdown",
            description="Markdownファイルから構造化されたファイルを生成します",
            inputSchema={
                "type": "object",
                "properties": {
                    "input_file_path": {
                        "type": "string",
                        "description": "入力ファイルのフルパス",
                    },
                    "root_directory": {
                        "type": "string",
                        "description": "ファイル生成のルートディレクトリ",
                    },
                },
                "required": ["input_file_path", "root_directory"],
            },
        )
    ]
    logger.debug(f"利用可能なツール数: {len(tools)}")
    return ListToolsResult(tools=tools)


@server.call_tool()
async def handle_call_tool(
    name: str, arguments: Dict[str, Any] | None
) -> CallToolResult:
    """
    ツールの実行を処理する
    """
    logger.info(f"ツール実行要求: {name}")
    logger.debug(f"引数: {arguments}")
    
    if name != "generate_files_from_markdown":
        error_msg = f"Unknown tool: {name}"
        logger.error(error_msg)
        raise ValueError(error_msg)

    if not arguments:
        error_msg = "Arguments are required"
        logger.error(error_msg)
        raise ValueError(error_msg)

    input_file_path = arguments.get("input_file_path")
    root_directory = arguments.get("root_directory")

    logger.debug(f"入力ファイルパス: {input_file_path}")
    logger.debug(f"ルートディレクトリ: {root_directory}")

    if not input_file_path or not root_directory:
        error_msg = "input_file_path and root_directory are required"
        logger.error(error_msg)
        raise ValueError(error_msg)

    try:
        # ファイル生成処理を実行
        logger.info("ファイル生成処理を開始")
        result = await generate_files_from_markdown(input_file_path, root_directory)
        logger.info("ファイル生成処理が完了")
        logger.debug(f"処理結果のサイズ: {len(result)} 文字")

        return CallToolResult(content=[TextContent(type="text", text=result)])
    except Exception as e:
        error_msg = f"Error: {str(e)}"
        logger.error(f"ファイル生成中にエラーが発生: {e}", exc_info=True)
        return CallToolResult(
            content=[TextContent(type="text", text=error_msg)], isError=True
        )


def parse_input_md_sections(md_content: str) -> List[Dict[str, str]]:
    """
    input.md の内容を解析し、ファイル情報を抽出します。

    Args:
        md_content (str): input.md ファイルの内容。

    Returns:
        list: 各要素が以下のキーを持つ辞書のリスト:
              'filepath': str, 作成/更新するファイルのパス。
              'content': str, ファイルの内容。
              'change_description': str, 変更内容の説明（オプション）。
    """
    logger.info("Markdownコンテンツの解析を開始")
    logger.debug(f"入力コンテンツサイズ: {len(md_content)} 文字")
    
    files_to_create = []

    # 全体のMarkdownコンテンツを、ファイル定義セクションとそれ以外のセクションに分割
    # 各セクションは、'## ./' で始まる行か、'___' で始まる行の直前で分割される
    # FLAGS: re.DOTALL は . が改行にもマッチ, re.MULTILINE は ^$ が各行の始まり/終わりにマッチ
    all_sections = re.split(r"(?=(?:^## \./|^___))", md_content, flags=re.MULTILINE)
    logger.debug(f"セクション分割結果: {len(all_sections)} 個のセクション")

    for i, section_block in enumerate(all_sections):
        section_block = section_block.strip()
        if not section_block:
            logger.debug(f"セクション {i+1}: 空のセクションをスキップ")
            continue

        logger.debug(f"セクション {i+1} を処理中 (サイズ: {len(section_block)} 文字)")

        # セクションの主要なファイルパスを検索 (例: ## ./README.md)
        filepath_match = re.search(r"^## \./(.+?)$", section_block, re.MULTILINE)

        if not filepath_match:
            # このセクションは '## ./' の形式ではないため、ファイル定義ではないと判断しスキップ
            logger.debug(f"セクション {i+1}: ファイル定義ではないためスキップ")
            continue

        current_filepath = filepath_match.group(1).strip()
        logger.info(f"ファイル定義を発見: {current_filepath}")

        # 変更内容を検索 (オプション) (例: ### 変更内容)
        change_desc = ""
        # 変更内容は ### 変更内容 から始まり、次の ### ./filepath かコードブロックの開始の前まで
        change_desc_match = re.search(
            r"### 変更内容\n(.*?)(?=\n(?:### \./|```|$))", section_block, re.DOTALL
        )
        if change_desc_match:
            change_desc = change_desc_match.group(1).strip()
            logger.debug(f"変更内容を発見: {change_desc[:100]}...")

        # ___ コンテンツブロックを検索するロジックを改善 ___
        content = ""

        # まず、ファイルパスヘッダー (### ./filepath) の開始位置を探す
        filepath_header_marker = f"### ./{current_filepath}"
        filepath_header_pos = section_block.find(filepath_header_marker)

        if filepath_header_pos == -1:
            warning_msg = (
                f"警告: ファイル '{current_filepath}' のコンテンツ開始マーカー "
                f"'{filepath_header_marker}' が見つかりません。"
                "このファイルは作成されません。"
            )
            logger.warning(warning_msg)
            print(warning_msg)
            continue

        # ヘッダー以降の文字列 (コンテンツ候補)
        # ヘッダーの終端からセクションの終わりまで
        content_candidate = section_block[
            filepath_header_pos + len(filepath_header_marker) :
        ].strip()
        logger.debug(f"コンテンツ候補サイズ: {len(content_candidate)} 文字")

        # コードブロックの正規表現をより厳密に定義
        # `(```[a-zA-Z0-9_.-]*)\n`: 開始タグ (言語指定あり/なし) と改行
        # `(.*?)`: コンテンツ本体 (非貪欲マッチ)
        # `\n(```\s*)$`: 閉じタグと、その後は空白文字か行末のみ
        code_block_regex = re.compile(
            r"^(```[a-zA-Z0-9_.-]*)\n(.*?)\n(```\s*)$", re.DOTALL
        )

        code_block_match = code_block_regex.search(content_candidate)

        if code_block_match:
            # 修正: コードブロックの中身 (group(2)) のみをコンテンツとして抽出
            content = code_block_match.group(2).strip()
            logger.debug(f"コードブロックを発見: {len(content)} 文字のコンテンツ")

        else:
            # コードブロックが見つからない場合、警告を出力してスキップ
            # `## ./` の形式でも、コードブロックがなければファイルは作成しない方針を維持
            warning_msg = (
                f"警告: ファイル '{current_filepath}' のコンテンツブロックが"
                "見つからないか、形式が不正です。このファイルは作成されません。"
            )
            logger.warning(warning_msg)
            print(warning_msg)
            continue  # コードブロックが見つからない場合はスキップ

        if current_filepath and content:
            file_info = {
                "filepath": current_filepath,
                "content": content,
                "change_description": change_desc,
            }
            files_to_create.append(file_info)
            logger.info(f"ファイル情報を追加: {current_filepath}")
        # else: コンテンツが空の場合はすでに警告を出してcontinueしているため、不要

    logger.info(f"解析完了: {len(files_to_create)} 個のファイルが処理対象")
    return files_to_create


def create_files_from_parsed_data(
    parsed_data: List[Dict[str, str]], base_dir: str = "."
) -> str:
    """
    解析されたデータに基づいてファイルとディレクトリを作成します。

    Args:
        parsed_data (list): parse_input_md_sections からのファイル情報辞書のリスト。
        base_dir (str): ファイルが作成されるベースディレクトリ。

    Returns:
        str: 作成結果の詳細
    """
    logger.info("ファイル作成処理を開始")
    logger.debug(f"ベースディレクトリ: {base_dir}")
    logger.debug(f"作成対象ファイル数: {len(parsed_data)}")
    
    if not parsed_data:
        logger.warning("作成するファイルがありません")
        return "作成するファイルがありません。"

    results = []
    results.append("___")
    created_files = 0
    failed_files = 0

    for i, file_info in enumerate(parsed_data):
        relative_filepath = file_info["filepath"]
        filepath = os.path.join(base_dir, relative_filepath)
        content = file_info["content"]

        logger.info(f"ファイル {i+1}/{len(parsed_data)} を処理中: {relative_filepath}")
        logger.debug(f"絶対パス: {filepath}")
        logger.debug(f"コンテンツサイズ: {len(content)} 文字")

        dir_name = os.path.dirname(filepath)
        if dir_name:
            logger.debug(f"ディレクトリを作成: {dir_name}")
            try:
                os.makedirs(dir_name, exist_ok=True)
                logger.debug(f"ディレクトリ作成成功: {dir_name}")
            except Exception as e:
                logger.error(f"ディレクトリ作成失敗: {dir_name}, エラー: {e}")

        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            
            logger.info(f"ファイル作成成功: {filepath}")
            created_files += 1
            
            results.append(f"# {file_info['filepath']}")
            results.append("ファイルを作成/更新しました")
            results.append(f"{filepath}")
            if file_info.get("change_description"):
                results.append("## 変更内容")
                results.append(f"{file_info['change_description']}")
                results.append("___")
                
        except IOError as e:
            error_msg = f"ファイル '{filepath}' の書き込み中にエラーが発生しました: {e}"
            logger.error(error_msg)
            failed_files += 1
            results.append(error_msg)

    logger.info(f"ファイル作成処理完了: 成功={created_files}, 失敗={failed_files}")
    return "\n".join(results)


async def generate_files_from_markdown(
    input_file_path: str, root_directory: str
) -> str:
    """
    Markdownファイルからファイルを生成するメイン処理

    Args:
        input_file_path (str): 入力ファイルのフルパス
        root_directory (str): ファイル生成のルートディレクトリ

    Returns:
        str: 処理結果
    """
    start_time = datetime.now()
    logger.info(f"ファイル生成処理を開始: {input_file_path} -> {root_directory}")
    
    try:
        # 入力ファイルの存在確認
        logger.debug(f"入力ファイルの存在確認: {input_file_path}")
        if not os.path.exists(input_file_path):
            error_msg = f"入力ファイル '{input_file_path}' が見つかりません。"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)

        # 入力ファイルの読み込み
        logger.info(f"入力ファイルを読み込み中: {input_file_path}")
        with open(input_file_path, "r", encoding="utf-8") as f:
            md_content = f.read()
        logger.debug(f"入力ファイル読み込み完了: {len(md_content)} 文字")

        # 出力ディレクトリの作成
        logger.debug(f"出力ディレクトリの確認: {root_directory}")
        if not os.path.exists(root_directory):
            logger.info(f"出力ディレクトリを作成: {root_directory}")
            os.makedirs(root_directory, exist_ok=True)
            output_msg = f"出力ディレクトリを作成しました: {root_directory}\n"
        else:
            logger.debug(f"出力ディレクトリは既に存在: {root_directory}")
            output_msg = (
                f"出力ディレクトリ '{root_directory}' は既に存在します。"
                "ファイルはここに作成/上書きされます。\n"
            )

        # Markdownの解析
        logger.info("Markdownの解析を開始")
        parsed_files = parse_input_md_sections(md_content)

        if not parsed_files:
            error_msg = f"'{input_file_path}' からファイル情報が正常に解析されませんでした。"
            logger.error(error_msg)
            return error_msg

        # ファイル作成
        logger.info("ファイル作成処理を開始")
        creation_result = create_files_from_parsed_data(
            parsed_files, base_dir=root_directory
        )

        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        logger.info(f"ファイル生成処理完了: 処理時間={processing_time:.2f}秒")

        return f"{output_msg}{creation_result}\n\nファイル作成プロセスが完了しました。"

    except Exception as e:
        error_msg = f"エラーが発生しました: {str(e)}"
        logger.error(f"ファイル生成処理中にエラーが発生: {e}", exc_info=True)
        return error_msg


async def run_stdio_server():
    """
    標準入出力を使用してMCPサーバーを起動
    """
    logger.info("標準入出力モードでMCPサーバーを起動")
    try:
        async with stdio_server() as (read_stream, write_stream):
            logger.info("MCPサーバーが標準入出力モードで起動しました")
            await server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="file-generator-mcp",
                    server_version="1.0.0",
                    capabilities=server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={},
                    ),
                ),
            )
    except Exception as e:
        logger.error(f"標準入出力サーバーでエラーが発生: {e}", exc_info=True)
        raise


async def run_tcp_server(host: str = "localhost", port: int = 8000):
    """
    TCP接続を使用してMCPサーバーを起動

    Args:
        host: バインドするIPアドレス
        port: リッスンするポート番号
    """
    logger.info(f"TCPサーバーを起動中: {host}:{port}")

    async def handle_client(reader, writer):
        """
        クライアント接続を処理
        """
        client_addr = writer.get_extra_info('peername')
        logger.info(f"クライアント接続: {client_addr}")
        
        try:
            await server.run(
                reader,
                writer,
                InitializationOptions(
                    server_name="file-generator-mcp",
                    server_version="1.0.0",
                    capabilities=server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={},
                    ),
                ),
            )
        except Exception as e:
            logger.error(f"クライアント接続エラー: {client_addr}, エラー: {e}", exc_info=True)
            print(f"クライアント接続エラー: {e}")
        finally:
            logger.info(f"クライアント接続を終了: {client_addr}")
            writer.close()
            await writer.wait_closed()

    try:
        # TCPサーバーを起動
        tcp_server = await asyncio.start_server(handle_client, host, port)

        addr = tcp_server.sockets[0].getsockname()
        logger.info(f"MCPサーバーが {addr[0]}:{addr[1]} で正常に起動しました")
        print(f"MCPサーバーが {addr[0]}:{addr[1]} で起動しました")
        print("接続を待機中...")

        async with tcp_server:
            await tcp_server.serve_forever()
    except Exception as e:
        logger.error(f"TCPサーバーの起動に失敗: {e}", exc_info=True)
        raise


async def main():
    """
    MCPサーバーを起動する
    """
    parser = argparse.ArgumentParser(description="MCP File Generator Server")
    parser.add_argument(
        "--host",
        default=None,
        help="TCPサーバーのIPアドレス (指定しない場合はstdioモード)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="TCPサーバーのポート番号 (デフォルト: 8000)",
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="ログレベル (デフォルト: INFO)",
    )

    args = parser.parse_args()

    # ログレベルを設定
    global logger
    logger = setup_logging(args.log_level)
    
    logger.info(f"MCPサーバーを起動中... ログレベル: {args.log_level}")
    logger.debug(f"コマンドライン引数: {args}")

    if args.host:
        # TCP サーバーモード
        logger.info(f"TCPサーバーモードで起動: {args.host}:{args.port}")
        await run_tcp_server(args.host, args.port)
    else:
        # stdio サーバーモード
        logger.info("標準入出力モードで起動")
        await run_stdio_server()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("サーバーが手動で停止されました")
    except Exception as e:
        logger.error(f"サーバーの起動に失敗: {e}", exc_info=True)
        sys.exit(1)
