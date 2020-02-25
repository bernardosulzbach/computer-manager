export EDITOR=/usr/bin/vim

export HISTSIZE=-1
export HISTFILESIZE=-1

PATH="$PATH:$HOME/.local/bin"
PATH="$PATH:$HOME/.cargo/bin"
PATH="$PATH:$HOME/code/computer-manager"
PATH="$PATH:$HOME/code/computer-manager"
PATH="$PATH:$HOME/code/computer-manager/cloc"
PATH="$PATH:$HOME/code/computer-manager/scripts"
PATH="$PATH:$HOME/code/computer-manager/maven/bin"

export PATH="$HOME/.yarn/bin:$HOME/.config/yarn/global/node_modules/.bin:$PATH"

# Add powerline.
powerline-daemon -q
POWERLINE_BASH_CONTINUATION=1
POWERLINE_BASH_SELECT=1
. /usr/share/powerline/bash/powerline.sh

# Define my aliases and functions.
make-and-enter() {
    mkdir "$1" && cd "$1"
}

alias computer-manager='python3 ~/code/computer-manager/manager.py'

# The next line updates PATH for the Google Cloud SDK.
if [ -f '/home/bernardo/google-cloud-sdk/path.bash.inc' ]; then . '/home/bernardo/google-cloud-sdk/path.bash.inc'; fi

# The next line enables shell command completion for gcloud.
if [ -f '/home/bernardo/google-cloud-sdk/completion.bash.inc' ]; then . '/home/bernardo/google-cloud-sdk/completion.bash.inc'; fi

# Add .NET Core SDK tools
export PATH="$PATH:/home/bernardo/.dotnet/tools"
