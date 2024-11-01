#!/bin/zsh

#  設定ファイルを読み込み
config_file="$HOME/.rsemi_config"
if [ -f "$config_file" ]; then
    source "$config_file"
else
    echo "Error: $config_file not found."
    exit 1
fi

RED='\033[0;31m'
NC='\033[0m'

cd "$RSEMI_PATH"
tracked_files=($(git status --porcelain | grep '^ M' | awk '{print $2}'))
untracked_files=($(git status --porcelain | grep '^??' | awk '{print $2}'))

echo -e "${RED}変更されたファイル${NC}"
for file in "${tracked_files[@]}"; do
    echo "・$file"
done

echo "================================"

echo -e "${RED}追加されたファイル${NC}"
for file in "${untracked_files[@]}"; do
    echo "・$file"
done

echo

# 変更されたファイルと追加されたファイルの数をチェック
if [[ ${#tracked_files[@]} -ne 1 && ${#untracked_files[@]} -ne 1 ]]; then
    echo "comment.orgの変更とpdf資料の追加のみ行ってください"
    exit 1
fi

read "REPLY?Are you sure you want to add all changes and create a PR? (y/n): "
echo


submit_pdffile=$(git status --porcelain | awk '/^\?\?/ && /\.pdf$/ {print $2}')

if [[ $REPLY == "y" ]]; then
    git add --all
    git commit -m "add $submit_pdffile"
    git push origin HEAD
    url=$(gh pr create --title "add $submit_pdffile" --body "" --base main)
    echo "$url"
    open -a "Google Chrome" "$url"
    else
        echo "Submission canceled."
fi
