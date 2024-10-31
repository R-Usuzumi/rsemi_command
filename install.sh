#!/bin/zsh

config_file="$HOME/.rsemi_config"
shell_config="$HOME/.zshrc"

# インストール済みの処理
if [ -f "$config_file" ]; then
    echo "Configuration file $config_file already exists."
    echo "Using existing settings."   
    source "$config_file"
    echo "nickname: $NICKNAME"
    echo "rsemi_path: $RSEMI_PATH"

# まだインストールしてないとき   
else   
    read "nickname?nickname: "
    read "rsemi_path?rsemi_path: "
    rsemi_path="$HOME/${rsemi_path#*/}"

    echo "You entered:"
    echo "nickname: $nickname"
    echo "rsemi_path: $rsemi_path"
    read "confirm? Is this correct? (y/n): "
    if [[ "$confirm" != "y" ]]; then
	echo "Installation aborted."
	exit 1
    fi   

    cat <<EOL > "$config_file"
export NICKNAME="$nickname"
export RSEMI_PATH="$rsemi_path"
EOL
    
    echo "Configuration file created at $config_file"
    echo "Your nickname is set to '$nickname'"
    echo "Your rsemi path is set to '$rsemi_path'"
fi

simlink_dir="$HOME/bin"
mkdir -p "$simlink_dir"

# シンボリックリンク貼る
for file in ./bin/*; do
    file_name="${file##*/}"
    base_name="${file_name%.*}"
    
    exec_file="$(pwd)/${file#*/}"
    link_path="$simlink_dir/$base_name"

    [ -L "$link_path" ] && unlink "$link_path"

    chmod +x "$exec_file"
    ln -s "$exec_file" "$link_path"
    echo "Created symlink: $exec_file -> $simlink_dir/$base_name"
done


# cd_commentエイリアスが存在しない場合に追加
if ! grep -q "alias comment='source comment'" "$shell_config"; then
    echo "alias comment='source comment'" >> "$shell_config"
    echo "Added alias 'comment' to $shell_config."
else
    echo "Alias 'comment' is already defined in $shell_config."
fi

# cd_materialエイリアスが存在しない場合に追加
if ! grep -q "alias material='source material'" "$shell_config"; then
    echo "alias material='source material'" >> "$shell_config"
    echo "Added alias 'material' to $shell_config."
else
    echo "Alias 'material' is already defined in $shell_config."
fi
  
echo "installation complete."
