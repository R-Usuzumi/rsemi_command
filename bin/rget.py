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
"""
Rゼミの合意事項をGoogleスプレッドシートとドキュメントから取得し、
指定されたorgファイルに追記、またはクリップボードにコピーするツール。
"""

# ドキュメントとスプシのapi使う
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets.readonly',
    'https://www.googleapis.com/auth/documents.readonly',
]

TOKEN_FOLDER = 'rsemi_token'
TOKEN_PATH = Path.home() / TOKEN_FOLDER / 'token.pickle'
CREDENTIALS_PATH = Path.home() / TOKEN_FOLDER / "credentials.json"


class RsemiEnv:
    """
    ~/.rsemi_config に定義された環境変数を読み込んで，
    Rゼミの設定情報を管理するクラス
    """
    def __init__(self, config_path="~/.rsemi_config"):
        self.config_path = os.path.expanduser(config_path)
        self._load_env()
        self.nickname = os.getenv("NICKNAME")
        self.rsemi_path = os.getenv("RSEMI_PATH")
        self.sheet_url = os.getenv("SHEET_URL")
        self.sheet_name = os.getenv("SHEET_NAME")
        self.commentfile_path = os.getenv("COMMENTFILE_PATH")

    def get_config_path(self):
        return self.config_path

    def get_rsemi_path(self):
        return self.rsemi_path

    def get_nickname(self):
        return self.nickname

    def get_sheet_url(self):
        return self.sheet_url

    def get_sheet_name(self):
        return self.sheet_name

    def get_commentfile_path(self):
        return self.commentfile_path

    def _load_env(self):
        """
        設定ファイルから環境変数を読み込み、os.environに反映させる
        """
        with open(self.config_path, 'r') as file:
            for line in file:
                if line.startswith("#") or not line.strip():
                    continue
                key, value = line.replace("export ", "",
                                          1).strip().split("=", 1)
                os.environ[key] = value.strip('"').strip("'")


class GoogleAuthenticator:
    def get_credentials(self):
        creds = None

        # 保存済みトークンがあれば読み込む
        if TOKEN_PATH.exists():
            with open(TOKEN_PATH, 'rb') as token:
                creds = pickle.load(token)

        # トークンが無効ならば再認証
        if not creds or not creds.valid:
            # accessがなく，refreshがある
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception:
                    creds = self._re_auth()
            # そもそもtokenがないもしくはrefresh_tokenない
            else:
                creds = self._re_auth()
        return creds

    # refresh_tokenがない場合
    def _re_auth(self):
        flow = InstalledAppFlow.from_client_secrets_file(
            str(CREDENTIALS_PATH), SCOPES)
        creds = flow.run_local_server(port=0)
        with open(TOKEN_PATH, 'wb') as token:
            pickle.dump(creds, token)
        return creds


class RsemiSpreadsheet:
    """
    Rゼミのスプレッドシートから，指定された日付に対応する
    Googleドキュメントを管理するクラス
    """
    def __init__(self, sheet_url, sheet_name):
        self.spreadsheet_id = self._extract_id(sheet_url)
        self.sheet_name = sheet_name

    def _extract_id(self, url):
        """
        スプレッドシートIDを取得
        """
        match = re.search(r'/d/([a-zA-Z0-9-_]+)', url)
        if not match:
            raise ValueError("Rsemi spreadsheet not found")
        return match.group(1)

    def get_docurl_for_date(self, date):
        # 日付とurlの列
        date_col = "A"
        url_col = "D"

        result = build('sheets', 'v4',
                       credentials=creds).spreadsheets().values().batchGet(
                           spreadsheetId=self.spreadsheet_id,
                           ranges=[
                               f"{self.sheet_name}!{date_col}:{date_col}",
                               f"{self.sheet_name}!{url_col}:{url_col}"
                           ]).execute()

        dates = result['valueRanges'][0].get('values', [])
        urls = result['valueRanges'][1].get('values', [])

        # dateが一致するsheetのurlを取得
        for i, row in enumerate(dates):
            if row and row[0] == date:
                doc_url = urls[i][0]
                return doc_url

        raise ValueError(f"Date {date} not found in sheet.")


class RsemiDocument:
    """
    RゼミのGoogleドキュメントを管理するクラス
    """
    def __init__(self, document_url):
        self.document_id = self._extract_id(document_url)

    def _extract_id(self, url):
        """
        ドキュメントIDを取得
        """
        match = re.search(r'/d/([a-zA-Z0-9-_]+)', url)
        if not match:
            raise ValueError("Rsemi document not found")
        return match.group(1)

    def get_agree_comment(self, nickname):
        document = build('docs', 'v1', credentials=creds).documents().get(
            documentId=self.document_id).execute()
        content = document.get('body', {}).get('content', [])

        agree_comment = []
        capture_subitems = False
        current_item = None

        for element in content:
            if 'paragraph' in element:
                paragraph = element['paragraph']
                if 'bullet' in paragraph:
                    level = paragraph['bullet'].get('nestingLevel', 0)
                    text = ''.join(elem['textRun']['content']
                                   for elem in paragraph.get('elements', [])
                                   if 'textRun' in elem).strip()

                    if level == 0 and nickname in text:
                        current_item = {'one': nickname, 'sub_items': []}
                        agree_comment.append(current_item)
                        capture_subitems = True

                    elif level == 0 and capture_subitems:
                        capture_subitems = False
                        break

                    elif capture_subitems and level > 0:
                        current_item['sub_items'].append({
                            'level': level,
                            'content': text
                        })

        return agree_comment

    def output_commentfile(self,
                           date,
                           agree_comment,
                           comment_file,
                           pos='copy'):
        lines = []
        for line in agree_comment:
            lines.append(f"* {date}")

            for sub_line in line['sub_items']:
                level = sub_line['level']
                content = sub_line['content']

                if content == "合意事項":
                    lines.append("** 合意事項")
                    continue
                elif content == "コメント":
                    lines.append("** コメント")
                    continue

                indent = "  " * (level - 1)
                if content:
                    lines.append(f"{indent}- {content}")

        agree_comment_str = "\n".join(lines)

        if pos == "bottom":
            with open(comment_file, 'a') as f:
                f.write("\n" + agree_comment_str + "\n")
            print(agree_comment_str)

        elif pos == "top":
            with open(comment_file, 'r+') as f:
                existing_content = f.read()
                f.seek(0)
                f.write(agree_comment_str + "\n\n" + existing_content)
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


if __name__ == "__main__":

    # .rsemi_configの中身を記載
    env = RsemiEnv()
    creds = GoogleAuthenticator().get_credentials()

    # 引数パース
    parser = argparse.ArgumentParser(description="Rゼミ合意事項の抽出")
    parser.add_argument("date", help="対象日付（例: 2025/04/10）")
    parser.add_argument("--nickname", help="ニックネーム（例: ryuto）")
    pos_group = parser.add_mutually_exclusive_group()
    pos_group.add_argument("--top", action="store_true", help="ファイルの先頭に追記")
    pos_group.add_argument("--bottom", action="store_true", help="ファイルの末尾に追記")
    pos_group.add_argument("--copy",
                           action="store_true",
                           help="クリップボードにコピー（デフォルト）")
    args = parser.parse_args()
    nickname = args.nickname if args.nickname else env.get_nickname()

    if args.top:
        pos = "top"
    elif args.bottom:
        pos = "bottom"
    else:
        pos = "copy"

    # rsemiのスプシを取得
    spreadsheet = RsemiSpreadsheet(env.get_sheet_url(), env.get_sheet_name())

    # rsemiのスプシからargs.dateで指定した日のドキュメントを取得
    document = RsemiDocument(spreadsheet.get_docurl_for_date(args.date))

    # 合意事項を取得し，nickname.orgに出力
    agree_comment = document.get_agree_comment(nickname)
    document.output_commentfile(args.date,
                                agree_comment,
                                env.get_commentfile_path(),
                                pos=pos)
