#!/bin/zsh

echo "Updating..."
git checkout main > /dev/null 2>&1
git pull origin main

./install.sh | sed 's/installation/update/g'
