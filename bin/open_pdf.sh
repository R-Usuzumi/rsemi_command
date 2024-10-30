#!/bin/zsh

#  設定ファイルを読み込み
config_file="$HOME/.rsemi_config"
if [ -f "$config_file" ]; then
    source "$config_file"
else
    echo "Error: $config_file not found."
    exit 1
fi


material_path="$RSEMI_PATH/material"

if [ $# -eq 0 ]; then
    echo "Usage: $0 [nickname] [date]"
    echo "Arguments:"
    echo "  nickname  someone's nickname (required)"
    echo "  date      The date in format MMDD (optional)"
    exit 0
fi

if [ $# -eq 1 ]; then
    nickname="$1"
    target_file="$material_path/$(ls -1 *.pdf | grep -E "^[0-9]{4}-$nickname\.pdf$" | sort -r | head -n 1)"
    open "$target_file"
fi

if [ $# -eq 2 ]; then
    nickname="$1"   
    date="$2"
    
    if [ "$2" = "t" ]; then
	today=$(date +%m%d)
	target_file="$material_path/$today-$nickname.pdf"
	open "$target_file"
	exit 0
	
    else
	target_file="$material_path/$date-$nickname.pdf"
	open "$target_file"
	exit 0
    fi

fi    

    
    
