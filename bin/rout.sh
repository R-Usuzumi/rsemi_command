#!/bin/zsh

source ~/.zshrc

# 設定ファイルを読み込み
config_file="$HOME/.rsemi_config"

if [ -f "$config_file" ]; then
    source "$config_file"
else
    echo "Error: $config_file not found."
    exit 1
fi

output_pdf_name=""

# オプション引数を追加できる，--name pdf_file名のようにする
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --name)
            shift
            output_pdf_name="$1"
            ;;
        *)
            html_file="$1"
            ;;
    esac
    shift
done

# HTMLファイルが指定されているかと拡張子の確認
if [[ -z "$html_file" || ("$html_file" != *.html && "$html_file" != *.htm) ]]; then
    echo "Error: Please provide an HTML file as input."
    exit 1
fi

# 出力ファイル名の設定
file_name="${html_file##*/}" 
base_name="${file_name%.*}"
pdf_file="$RSEMI_PATH/material/${output_pdf_name:-$base_name}.pdf"

# HTMLをPDFに変換
google-chrome --headless --disable-gpu --run-all-compositor-stages-before-draw --virtual-time-budget=10000 --print-to-pdf="$pdf_file" "$html_file"
open "$pdf_file"
