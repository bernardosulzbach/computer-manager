"Get Powerline
python3 from powerline.vim import setup as powerline_setup
python3 powerline_setup()
python3 del powerline_setup

"Security
set modelines=0

"Run Pathogen
execute pathogen#infect()
filetype plugin indent on

"Set spellchecking for some files
autocmd FileType latex setlocal spell
autocmd FileType markdown setlocal spell
autocmd FileType md setlocal spell
autocmd FileType tex setlocal spell
autocmd FileType gitcommit setlocal spell

"Set our color scheme
colorscheme gruvbox
