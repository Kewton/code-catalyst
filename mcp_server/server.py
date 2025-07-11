#!/usr/bin/env python3
"""
MCP Server for File Generation from Markdown

This MCP server provides a tool to generate files from markdown content.
It parses markdown files and creates files based on the structured content.
"""

import asyncio
import os
import re
from typing import Any, Dict, List

from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolResult,
    ListToolsResult,
    TextContent,
    Tool,
)

# MCPサーバーの設定
server = Server("file-generator-mcp")


@server.list_tools()
async def handle_list_tools() -> ListToolsResult:
    """
    利用可能なツールのリストを返す
    """
    return ListToolsResult(
        tools=[
            Tool(
                name="generate_files_from_markdown",
                description="Markdownファイルから構造化されたファイルを生成します",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "input_file_path": {
                            "type": "string",
                            "description": "入力ファイルのフルパス"
                        },
                        "root_directory": {
                            "type": "string",
                            "description": "ファイル生成のルートディレクトリ"
                        }
                    },
                    "required": ["input_file_path", "root_directory"]
                }
            )
        ]
    )


@server.call_tool()
async def handle_call_tool(
    name: str, arguments: Dict[str, Any] | None
) -> CallToolResult:
    """
    ツールの実行を処理する
    """
    if name != "generate_files_from_markdown":
        raise ValueError(f"Unknown tool: {name}")

    if not arguments:
        raise ValueError("Arguments are required")

    input_file_path = arguments.get("input_file_path")
    root_directory = arguments.get("root_directory")

    if not input_file_path or not root_directory:
        raise ValueError("input_file_path and root_directory are required")

    try:
        # ファイル生成処理を実行
        result = await generate_files_from_markdown(
            input_file_path, root_directory
        )
        
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=result
                )
            ]
        )
    except Exception as e:
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=f"Error: {str(e)}"
                )
            ],
            isError=True
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
    files_to_create = []
    
    # 全体のMarkdownコンテンツを、ファイル定義セクションとそれ以外のセクションに分割
    # 各セクションは、'## ./' で始まる行か、'___' で始まる行の直前で分割される
    # FLAGS: re.DOTALL は . が改行にもマッチ, re.MULTILINE は ^$ が各行の始まり/終わりにマッチ
    all_sections = re.split(
        r'(?=(?:^## \./|^___))', md_content, flags=re.MULTILINE
    )
    
    for section_block in all_sections:
        section_block = section_block.strip()
        if not section_block:
            continue

        # セクションの主要なファイルパスを検索 (例: ## ./README.md)
        filepath_match = re.search(
            r"^## \./(.+?)$", section_block, re.MULTILINE
        )
        
        if not filepath_match:
            # このセクションは '## ./' の形式ではないため、ファイル定義ではないと判断しスキップ
            continue

        current_filepath = filepath_match.group(1).strip()

        # 変更内容を検索 (オプション) (例: ### 変更内容)
        change_desc = ""
        # 変更内容は ### 変更内容 から始まり、次の ### ./filepath かコードブロックの開始の前まで
        change_desc_match = re.search(
            r"### 変更内容\n(.*?)(?=\n(?:### \./|```|$))",
            section_block,
            re.DOTALL
        )
        if change_desc_match:
            change_desc = change_desc_match.group(1).strip()

        # ___ コンテンツブロックを検索するロジックを改善 ___
        content = ""
        
        # まず、ファイルパスヘッダー (### ./filepath) の開始位置を探す
        filepath_header_marker = f"### ./{current_filepath}"
        filepath_header_pos = section_block.find(filepath_header_marker)

        if filepath_header_pos == -1:
            print(
                f"警告: ファイル '{current_filepath}' のコンテンツ開始マーカー "
                f"'{filepath_header_marker}' が見つかりません。"
                "このファイルは作成されません。"
            )
            continue
        
        # ヘッダー以降の文字列 (コンテンツ候補)
        # ヘッダーの終端からセクションの終わりまで
        content_candidate = section_block[
            filepath_header_pos + len(filepath_header_marker):
        ].strip()

        # コードブロックの正規表現をより厳密に定義
        # `(```[a-zA-Z0-9_.-]*)\n`: 開始タグ (言語指定あり/なし) と改行
        # `(.*?)`: コンテンツ本体 (非貪欲マッチ)
        # `\n(```\s*)$`: 閉じタグと、その後は空白文字か行末のみ
        code_block_regex = re.compile(
            r"^(```[a-zA-Z0-9_.-]*)\n(.*?)\n(```\s*)$",
            re.DOTALL
        )
        
        code_block_match = code_block_regex.search(content_candidate)

        if code_block_match:
            # 修正: コードブロックの中身 (group(2)) のみをコンテンツとして抽出
            content = code_block_match.group(2).strip()
            
        else:
            # コードブロックが見つからない場合、警告を出力してスキップ
            # `## ./` の形式でも、コードブロックがなければファイルは作成しない方針を維持
            print(
                f"警告: ファイル '{current_filepath}' のコンテンツブロックが"
                "見つからないか、形式が不正です。このファイルは作成されません。"
            )
            continue  # コードブロックが見つからない場合はスキップ

        if current_filepath and content:
            files_to_create.append({
                "filepath": current_filepath,
                "content": content,
                "change_description": change_desc
            })
        # else: コンテンツが空の場合はすでに警告を出してcontinueしているため、不要

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
    if not parsed_data:
        return "作成するファイルがありません。"

    results = []
    results.append("___")
    
    for file_info in parsed_data:
        relative_filepath = file_info['filepath']
        filepath = os.path.join(base_dir, relative_filepath)
        content = file_info['content']

        dir_name = os.path.dirname(filepath)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)

        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            results.append(f"# {file_info['filepath']}")
            results.append("ファイルを作成/更新しました")
            results.append(f"{filepath}")
            if file_info.get("change_description"):
                results.append("## 変更内容")
                results.append(f"{file_info['change_description']}")
                results.append("___")
        except IOError as e:
            results.append(f"ファイル '{filepath}' の書き込み中にエラーが発生しました: {e}")

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
    try:
        # 入力ファイルの存在確認
        if not os.path.exists(input_file_path):
            raise FileNotFoundError(f"入力ファイル '{input_file_path}' が見つかりません。")
        
        # 入力ファイルの読み込み
        with open(input_file_path, "r", encoding="utf-8") as f:
            md_content = f.read()
        
        # 出力ディレクトリの作成
        if not os.path.exists(root_directory):
            os.makedirs(root_directory, exist_ok=True)
            output_msg = f"出力ディレクトリを作成しました: {root_directory}\n"
        else:
            output_msg = (
                f"出力ディレクトリ '{root_directory}' は既に存在します。"
                "ファイルはここに作成/上書きされます。\n"
            )
        
        # Markdownの解析
        parsed_files = parse_input_md_sections(md_content)
        
        if not parsed_files:
            return f"'{input_file_path}' からファイル情報が正常に解析されませんでした。"
        
        # ファイル作成
        creation_result = create_files_from_parsed_data(
            parsed_files, base_dir=root_directory
        )
        
        return f"{output_msg}{creation_result}\n\nファイル作成プロセスが完了しました。"
        
    except Exception as e:
        return f"エラーが発生しました: {str(e)}"


async def main():
    """
    MCPサーバーを起動する
    """
    # 標準入出力を使用してサーバーを起動
    async with stdio_server() as (read_stream, write_stream):
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


if __name__ == "__main__":
    asyncio.run(main())
