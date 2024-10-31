#!/bin/zsh

# 設定ファイルを読み込み
config_file="$HOME/.rsemi_config"
if [ -f "$config_file" ]; then
    source "$config_file"
else
    echo "Error: $config_file not found."
    exit 1
fi

# rsemi_pathが設定されているか確認
if [ -z "$RSEMI_PATH" ]; then
    echo "Error: RSEMI path is not set in the configuration."
    exit 1
fi

cd "$RSEMI_PATH/material"

