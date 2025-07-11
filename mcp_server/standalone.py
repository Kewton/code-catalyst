#!/usr/bin/env python3
"""
スタンドアロン版のファイル生成スクリプト
MCP機能のテストやデバッグに使用
"""

import argparse
import os
import re


def parse_input_md_sections(md_content):
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
    all_sections = re.split(r"(?=(?:^## \./|^___))", md_content, flags=re.MULTILINE)

    for section_block in all_sections:
        section_block = section_block.strip()
        if not section_block:
            continue

        # セクションの主要なファイルパスを検索 (例: ## ./README.md)
        filepath_match = re.search(r"^## \./(.+?)$", section_block, re.MULTILINE)

        if not filepath_match:
            # このセクションは '## ./' の形式ではないため、ファイル定義ではないと判断しスキップ
            continue

        current_filepath = filepath_match.group(1).strip()

        # 変更内容を検索 (オプション) (例: ### 変更内容)
        change_desc = ""
        # 変更内容は ### 変更内容 から始まり、次の ### ./filepath かコードブロックの開始の前まで
        change_desc_match = re.search(
            r"### 変更内容\n(.*?)(?=\n(?:### \./|```|$))", section_block, re.DOTALL
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
                f"'{filepath_header_marker}' が見つかりません。このファイルは作成されません。"
            )
            continue

        # ヘッダー以降の文字列 (コンテンツ候補)
        # ヘッダーの終端からセクションの終わりまで
        content_candidate = section_block[
            filepath_header_pos + len(filepath_header_marker) :
        ].strip()

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

        else:
            # コードブロックが見つからない場合、警告を出力してスキップ
            # `## ./` の形式でも、コードブロックがなければファイルは作成しない方針を維持
            print(
                f"警告: ファイル '{current_filepath}' のコンテンツブロックが"
                "見つからないか、形式が不正です。このファイルは作成されません。"
            )
            continue  # コードブロックが見つからない場合はスキップ

        if current_filepath and content:
            files_to_create.append(
                {
                    "filepath": current_filepath,
                    "content": content,
                    "change_description": change_desc,
                }
            )
        # else: コンテンツが空の場合はすでに警告を出してcontinueしているため、不要

    return files_to_create


def create_files_from_parsed_data(parsed_data, base_dir="."):
    """
    解析されたデータに基づいてファイルとディレクトリを作成します。

    Args:
        parsed_data (list): parse_input_md_sections からのファイル情報辞書のリスト。
        base_dir (str): ファイルが作成されるベースディレクトリ。
    """
    if not parsed_data:
        print("作成するファイルがありません。")
        return

    print("___")
    for file_info in parsed_data:
        relative_filepath = file_info["filepath"]
        filepath = os.path.join(base_dir, relative_filepath)
        content = file_info["content"]

        dir_name = os.path.dirname(filepath)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)

        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"# {file_info['filepath']}")
            print("ファイルを作成/更新しました")
            print(f"{filepath}")
            if file_info.get("change_description"):
                print("## 変更内容")
                print(f"{file_info['change_description']}")
                print("___")
        except IOError as e:
            print(f"ファイル '{filepath}' の書き込み中にエラーが発生しました: {e}")


def main():
    """
    メイン関数。input.md を読み込み、解析し、ファイルを作成します。
    """
    parser = argparse.ArgumentParser(
        description="input.md からファイルを生成します。",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "input_file",
        nargs="?",
        default="input.md",
        help="入力マークダウンファイルへのパス (デフォルト: input.md)",
    )
    parser.add_argument(
        "-d",
        "--directory",
        default="generated_files",
        help="ファイルの出力先ディレクトリ (デフォルト: generated_files)",
    )
    args = parser.parse_args()

    input_md_path = args.input_file
    output_directory = args.directory

    try:
        with open(input_md_path, "r", encoding="utf-8") as f:
            md_content = f.read()
    except FileNotFoundError:
        print(f"エラー: 入力ファイル '{input_md_path}' が見つかりません。")
        return
    except IOError as e:
        print(
            f"エラー: ファイル '{input_md_path}' の読み込み中にエラーが発生しました: {e}"
        )
        return

    if not os.path.exists(output_directory):
        os.makedirs(output_directory, exist_ok=True)
        print(f"出力ディレクトリを作成しました: {output_directory}")
    else:
        print(
            f"出力ディレクトリ '{output_directory}' は既に存在します。ファイルはここに作成/上書きされます。"
        )

    parsed_files = parse_input_md_sections(md_content)

    if not parsed_files:
        print(f"'{input_md_path}' からファイル情報が正常に解析されませんでした。")
        return

    create_files_from_parsed_data(parsed_files, base_dir=output_directory)
    print("\nファイル作成プロセスが完了しました。")


if __name__ == "__main__":
    main()
