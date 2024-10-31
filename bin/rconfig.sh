#!/bin/bash

config_file="$HOME/.rsemi_config"

# 設定値の取得
function get_config() {
    key=$1
    grep -E "^export $key=" "$config_file" | cut -d'=' -f2-
}

# 設定値の表示
function show_config() {
    echo "Nickname: $(get_config NICKNAME)"
    echo "RSEMI_PATH: $(get_config RSEMI_PATH)"
}

# 設定値の設定
function set_config() {
    key=$1
    value=$2

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

