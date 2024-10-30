#!/bin/zsh

# シンボリックリンク貼ってるディレクトリ
simlink_dir="$HOME/bin"
config_file="$HOME/.rsemi_config"

# .rsemi_configを削除
if [ -f "$config_file" ]; then
    rm "$config_file"
    echo "Deleted config file: $config_file"
fi

# シンボリックリンクを削除
for file in ./bin/*; do
    file_name="${file##*/}"
    base_name="${file_name%.*}"

    link_path="$simlink_dir/$base_name"
    
    if [ -L "$link_path" ]; then
        unlink "$link_path"
        echo "Deleted symlink: $link_path"
    fi
done

echo "Uninstallation complete."
