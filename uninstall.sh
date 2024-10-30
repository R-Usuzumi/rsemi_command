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
if grep -q "alias cd_comment='source cd_comment'" "$shell_config"; then
    sed -i '' "/alias cd_comment='source cd_comment'/d" "$shell_config"
    echo "Removed alias 'cd_comment' from $shell_config"
fi

if grep -q "alias cd_material='source cd_material'" "$shell_config"; then
    sed -i '' "/alias cd_material='source cd_material'/d" "$shell_config"
    echo "Removed alias 'cd_material' from $shell_config"
fi

echo "Alias removal complete."

echo "Uninstallation complete."
