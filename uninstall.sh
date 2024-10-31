#!/bin/zsh

# シンボリックリンク貼ってるディレクトリ
simlink_dir="$HOME/bin"
config_file="$HOME/.rsemi_config"
shell_config="$HOME/.zshrc"

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

# エイリアス削除
if grep -q "alias comment='source comment'" "$shell_config"; then
    sed -i '' "/alias comment='source comment'/d" "$shell_config"
    echo "Removed alias 'comment' from $shell_config"
fi

if grep -q "alias material='source material'" "$shell_config"; then
    sed -i '' "/alias material='source material'/d" "$shell_config"
    echo "Removed alias 'material' from $shell_config"
fi

if grep -q 'alias google-chrome' "$shell_config"; then
    sed -i '' '/alias google-chrome/d' "$shell_config"
    echo "Removed alias 'google-chrome' from $shell_config"
fi


echo "Alias removal complete."

echo "Uninstallation complete."
