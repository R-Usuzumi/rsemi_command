#!/bin/bash

config_file="$HOME/.rsemi_config"

# 設定値の取得
function get_config() {
    key=$1
    value=$(grep -E "^export $key=" "$config_file" | cut -d'=' -f2-)

    
    if [ -z "$value" ]; then
        echo "Error: Key '$key' not found"
        exit 1
    fi
    echo "$value"
}

# 設定値の表示
function show_config() {
    echo "RSEMI_PATH: $(get_config RSEMI_PATH)"
    echo "NICKNAME: $(get_config NICKNAME)"    
    echo "SHEET_URL: $(get_config SHEET_URL)"
    echo "SHEET_NAME: $(get_config SHEET_NAME)"
    echo "COMMENTFILE_PATH: $(get_config COMMENTFILE_PATH)"
}

# 設定値の設定
function set_config() {
    key=$1
    value=$2
    
    if ! grep -q "^export $key=" "$config_file"; then
        echo "Error: Key '$key' does not exist"
        exit 1
    fi

    sed -i '' "/^export $key=/d" "$config_file"
    echo "export $key=\"$value\"" >> "$config_file"
}

# 第一引数に set get showが来たときの処理
case "$1" in
    set)
        if [ -n "$2" ] && [ -n "$3" ]; then
            set_config "$2" "$3"
        else
            echo "Usage: $0 set <key> <value>"
        fi
        ;;
    get)
        if [ -n "$2" ]; then
            value=$(get_config "$2")
            if [ -n "$value" ]; then
                echo "$value"
            else
                echo "$2 is not set."
            fi
        else
            echo "Usage: $0 get <key>"
        fi
        ;;
    show)
        show_config
        ;;
    *)

        echo "Usage: $0 {set|get|show}"
        echo "  set <key> <value>  - Set a configuration value"
        echo "  get <key>          - Get a configuration value"
        echo "  show               - Show all configurations"
        ;;
esac

