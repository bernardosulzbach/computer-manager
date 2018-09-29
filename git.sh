#!/usr/bin/env bash

SCRIPTS_PATH="$HOME/scripts"

git config --global user.email "bernardo@bernardosulzbach.com"
git config --global user.name "Bernardo Sulzbach"

git config --global push.default simple

# Better Git pager
curl https://raw.githubusercontent.com/so-fancy/diff-so-fancy/master/third_party/build_fatpack/diff-so-fancy -o "$SCRIPTS_PATH/diff-so-fancy"
git config --global core.pager "diff-so-fancy | less --tabs=4 -RFX"

# Better Git colors
git config --global color.ui true

git config --global color.diff-highlight.oldNormal    "red bold"
git config --global color.diff-highlight.oldHighlight "red bold 52"
git config --global color.diff-highlight.newNormal    "green bold"
git config --global color.diff-highlight.newHighlight "green bold 22"
git config --global color.diff.meta                   "yellow"
git config --global color.diff.frag                   "magenta bold"
git config --global color.diff.commit                 "yellow bold"
git config --global color.diff.old                    "red bold"
git config --global color.diff.new                    "green bold"
git config --global color.diff.whitespace             "red reverse"
