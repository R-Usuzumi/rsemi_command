#!/bin/zsh

source ~/.zshrc

#  設定ファイルを読み込み
config_file="$HOME/.rsemi_config"

if [ -f "$config_file" ]; then
    source "$config_file"
else
    echo "Error: $config_file not found."
    exit 1
fi

html_file=$1
if [[ "$html_file" != *.html && "$html_file" != *.htm ]]; then
    echo "Error: The provided file is not in HTML format."
    exit 1
fi

file_name="${html_file##*/}"
echo "$file_name"
base_name="${file_name%.*}"
echo "$base_name"

google-chrome --headless --print-to-pdf="$RSEMI_PATH/material/$base_name.pdf" "$html_file"
