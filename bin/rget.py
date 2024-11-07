#!/usr/bin/env python3
import json
import os
import sys
import pickle
import re
import argparse
import tempfile
from pathlib import Path
from datetime import datetime
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google.auth.exceptions import RefreshError


def load_local_env(config_path):
    """
    config_pathの中身を環境変数に設定する

    """
    with open(config_path, 'r') as file:
        for line in file:
            if line.startswith("#") or not line.strip():
                continue
            key, value = line.replace("export ", "", 1).strip().split("=", 1)
            os.environ[key] = value.strip('"').strip("'")


# 環境変数の定義
RSEMI_CONFIG_PATH = "~/.rsemi_config"
CONFIG_PATH = os.path.expanduser(RSEMI_CONFIG_PATH)
load_local_env(CONFIG_PATH)
RSEMI_PATH = os.getenv("RSEMI_PATH")
NICKNAME = os.getenv("NICKNAME")

# ドキュメントとスプシのapi使う
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets.readonly',
    'https://www.googleapis.com/auth/documents.readonly',
]

TOKEN_FOLDER = 'rsemi_token'
TOKEN_PATH = Path.home() / TOKEN_FOLDER / 'token.pickle'
credentials = Path.home() / TOKEN_FOLDER / "credentials.json"


def get_credentials():
    """
    credentials使ってgoogleの認可サーバからトークンもらう
    """
    creds = None
    # 保存済みトークンがあれば読み込む
    if os.path.exists(TOKEN_PATH):
        with open(TOKEN_PATH, 'rb') as token:
            creds = pickle.load(token)

    # トークンが無効ならば再認証
    if not creds or not creds.valid:

        # accessがなく，refreshがある
        if creds and creds.expired and creds.refresh_token:
            try:
                # refreshしてみる
                creds.refresh(Request())

            except RefreshError:
                # refresh_tokenが無効なら取りに行く
                flow = InstalledAppFlow.from_client_secrets_file(
                    credentials, SCOPES)
                creds = flow.run_local_server(port=0)
                with open(TOKEN_PATH, 'wb') as token:
                    pickle.dump(creds, token)

        # そもそもtokenがないもしくはrefresh_tokenない
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                credentials, SCOPES)
            creds = flow.run_local_server(port=0)
            with open(TOKEN_PATH, 'wb') as token:
                pickle.dump(creds, token)

    return creds


"""
=========================================================================
ここからスプシに関する関数
==========================================================================
"""


def get_spreadsheet_id(url):
    """
    スプシのurlからスプシid取り出す
    """
    match = re.search(r'/d/([a-zA-Z0-9-_]+)', url)
    if match:
        return match.group(1)
    else:
        raise ValueError("Spreadsheet ID not found in the URL.")


def get_spreadsheet_data(spreadsheet_id):
    """
    スプシの内容取り出す
    rsemiの日にち列(dates)と合意事項，コメントのgoogle documentのurl列(urls)を出力
    """
    creds = get_credentials()
    # スプシにアクセス
    sheets_service = build('sheets', 'v4', credentials=creds)
    sheet_name = "Rゼミ"

    result = sheets_service.spreadsheets().values().batchGet(
        spreadsheetId=spreadsheet_id,
        ranges=[f"{sheet_name}!A:A", f"{sheet_name}!O:O"]).execute()

    # B列とO列のデータをそれぞれ取得
    ranges = result.get('valueRanges', [])
    dates = ranges[0].get('values', [])
    urls = ranges[1].get('values', [])

    return dates, urls


"""
=========================================================================
ここからドキュメントに関する関数
=========================================================================
"""


def get_document_id(url):
    """
    ドキュメントのurlからドキュメントid取り出す
    """
    match = re.search(r'/d/([a-zA-Z0-9-_]+)', url)
    if match:
        return match.group(1)
    else:
        raise ValueError("Document not found")


def search_agree_comment(doc_id, nickname):
    """
    合意事項，コメントのドキュメントから，nicknameの合意事項，コメントを取得
    
    ロジック丸投げわからん
    """
    creds = get_credentials()
    docs_service = build('docs', 'v1', credentials=creds)

    # ドキュメント内容の取得
    document = docs_service.documents().get(documentId=doc_id).execute()
    content = document.get('body').get('content', [])

    results = []

    capture_subitems = False
    current_item = None

    for element in content:
        if 'paragraph' in element:
            paragraph = element['paragraph']

            # 段落が箇条書きアイテムかどうか確認
            if 'bullet' in paragraph:
                level = paragraph['bullet'].get('nestingLevel', 0)

                # 最上位レベル（level 0）かつ検索文字列が含まれている場合
                if level == 0 and nickname in ''.join(
                        elem['textRun']['content']
                        for elem in paragraph['elements']
                        if 'textRun' in elem).strip():

                    # 新たな最上位レベル項目が見つかったので、下位階層のキャプチャ開始
                    current_item = {'one': nickname, 'sub_items': []}
                    results.append(current_item)
                    capture_subitems = True  # 下位階層のキャプチャ開始

                # 別の最上位レベルの箇条書きアイテムが出てきたら終了
                elif level == 0 and capture_subitems:
                    capture_subitems = False  # キャプチャ終了
                    break  # 同レベルのアイテムが出てきたらループを終了

                # 下位階層（level > 0）のアイテムをキャプチャ
                elif capture_subitems and level > 0:
                    sub_text_content = ''.join(
                        elem['textRun']['content']
                        for elem in paragraph['elements']
                        if 'textRun' in elem).strip()
                    current_item['sub_items'].append({
                        'level':
                        level,
                        'content':
                        sub_text_content
                    })

    return results


def output_org(org_file, date, agree_comment, pos):
    """
    orgに出力
    """
    lines = []

    # ここでorgの形式に整形
    for line in agree_comment:
        lines.append(f"* {date[0]}")

        for sub_line in line['sub_items']:
            level = sub_line['level']
            content = sub_line['content']
            if content == "合意事項":
                lines.append("** 合意事項")
                continue

            if content == "コメント":
                lines.append("** コメント")
                continue

            indent = "  " * (level - 1)  # 階層に応じたインデント

            if content:
                lines.append(f"{indent}- {content}")

    agree_comment_str = "\n".join(lines)

    # org_fileのどこに追記するかを指定
    # 下
    if pos == "bottom":
        with open(org_file, 'a') as f:
            f.write("\n" + agree_comment_str + "\n")
            print(agree_comment_str)

    # 上
    elif pos == "top":
        with open(org_file, 'r+') as f:
            existing_content = f.read()
            f.seek(0)
            f.write(agree_comment_str + "\n" + "\n" + existing_content)
            print(agree_comment_str)

    elif pos == "copy":
        if os.name == 'posix':
            with tempfile.NamedTemporaryFile(delete=False) as tmp:
                tmp.write(agree_comment_str.encode('utf-8'))
                tmp_path = tmp.name

            os.system(f'cat {tmp_path} | pbcopy')
            os.remove(tmp_path)
            print(agree_comment_str)
            print("Copied to clipboard!")

        else:
            pass


def main(spreadsheet_url, target_date, pos):
    # スプレッドシートIDを抽出
    spreadsheet_id = get_spreadsheet_id(spreadsheet_url)

    # 実行時の引数として指定されたtarget_dateに対応するドキュメントurl取得
    index = 0
    dates, urls = get_spreadsheet_data(spreadsheet_id)
    for i, date in enumerate(dates):
        if len(date) == 1 and target_date == date[0]:
            index = i
            break
    doc_url = urls[index]

    # ドキュメントIDを抽出
    doc_id = get_document_id(doc_url[0])
    agree_comment = search_agree_comment(doc_id, NICKNAME)

    # 合意事項を書き込む
    comment_orgfile = f"{RSEMI_PATH}/comment/{NICKNAME}.org"
    output_org(comment_orgfile, date, agree_comment, pos)

    # del os.environ["RSEMI_PATH"]
    # del os.environ["NICKNAME"]


if __name__ == "__main__":

    # スプレッドシートurl!!!!!!!!!!!!!!!!!!!
    spreadsheet_url = 'https://docs.google.com/spreadsheets/d/1TKRBC-U6ycJV4jtHz53jQ4oW_xgHOFM6we115cQk7nI/edit?gid=147889766#gid=147889766'

    # 引数設定
    parser = argparse.ArgumentParser(description="合意事項を抜き取る")
    parser.add_argument(
        "date",
        help="Date to filter by in YYYY/MM/DD format (e.g., 2024/01/01)")

    parser.add_argument(
        "--pos",
        choices=["top", "bottom", "copy"],
        default="bottom",
        help=
        "Data output position: 'top' to add at the top, 'bottom' to add at the bottom, 'copy' to copy to clipboard"
    )

    args = parser.parse_args()
    main(spreadsheet_url, args.date, args.pos)
