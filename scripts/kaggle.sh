#!/usr/bin/env bash

mkdir -p ~/.kaggle && cd ~/.kaggle || exit
rm -f .kaggle.json
ln -s ~/Dropbox/kaggle/kaggle.json .kaggle.json
echo "Done."
ls -la ~/.kaggle
