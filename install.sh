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
    read "sheet_url?sheet_url:  "
    read "sheet_name?sheet_name:  "
    rsemi_path="$HOME/${rsemi_path#*/}"

    echo "You entered:"
    echo "nickname: $nickname"
    echo "rsemi_path: $rsemi_path"
    echo "sheet_url: $sheet_url"
    echo "sheet_name: $sheet_name"
    read "confirm? Is this correct? (y/n): "
    if [[ "$confirm" != "y" ]]; then
	echo "Installation aborted."
	exit 1
    fi   

    cat <<EOL > "$config_file"
export NICKNAME=$nickname
export RSEMI_PATH=$rsemi_path
export COMMENTFILE_PATH=$rsemi_path/comment/$nickname.org
export SHEET_URL=$sheet_url
export SHEET_NAME=$sheet_name
EOL
    
    echo "Configuration file created at $config_file"
    echo "Your nickname is set to '$nickname'"
    echo "Your rsemi path is set to '$rsemi_path'"
fi

simlink_dir="$HOME/bin"
mkdir -p "$simlink_dir"

pip install -r requirements.txt > /dev/null

# token用のフォルダをhome直下に作成
mkdir -p "$HOME/rsemi_token"

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


# commentのエイリアス
if ! grep -q "alias comment='source comment'" "$shell_config"; then
    echo "alias comment='source comment'" >> "$shell_config"
    echo "Added alias 'comment' to $shell_config."
else
    echo "Alias 'comment' is already defined in $shell_config."
fi

# materialのエイリアス
if ! grep -q "alias material='source material'" "$shell_config"; then
    echo "alias material='source material'" >> "$shell_config"
    echo "Added alias 'material' to $shell_config."
else
    echo "Alias 'material' is already defined in $shell_config."
fi

# google-chromeのエイリアス
if ! grep -q 'google-chrome="/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome"' "$shell_config"; then
    echo 'alias google-chrome="/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome"' >> "$shell_config"
    echo "Added alias 'google-chrome' to $shell_config."
else
    echo "Alias 'google-chrome' is already defined in $shell_config."
fi

echo "installation complete."
