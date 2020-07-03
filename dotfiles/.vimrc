"Don't try to be vi compatible
set nocompatible

"General
set nowrap "Wrap lines
set showbreak=+++ "Wrap-broken line prefix
set textwidth=100 "Line wrap (number of cols)
set showmatch "Highlight matching brace
 
set hlsearch "Highlight all search results
set smartcase "Enable smart-case search
set ignorecase "Always case-insensitive
set incsearch "Searches for strings incrementally
 
set autoindent "Auto-indent new lines
set expandtab "Use spaces instead of tabs
set shiftwidth=4 "Number of auto-indent spaces
set smartindent "Enable smart-indent
set smarttab "Enable smart-tabs
set softtabstop=4 "Number of spaces per Tab

"Security
set modelines=0
 
"Advanced
set ruler "Show row and column ruler information
 
set undolevels=1000 "Number of undo levels
set backspace=indent,eol,start "Backspace behaviour

set nojoinspaces

"The ' option is used to specify how many files for which you save marks (a-z).
"The < option controls how many lines are saved for each of the registers. By default, all the lines are saved.
set viminfo='10

autocmd FileType latex setlocal spell
autocmd FileType markdown setlocal spell
autocmd FileType md setlocal spell
autocmd FileType tex setlocal spell
autocmd FileType gitcommit setlocal spell
