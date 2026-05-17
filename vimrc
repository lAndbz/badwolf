" Vim configuration for Ubuntu 26.04 development environments.
" Install as ~/.vimrc, or start Vim with: vim -Nu /path/to/badwolf/vimrc

set nocompatible

" Load this repository as a runtime directory when the file is used in place, so
" colors/badwolf.vim is available without copying it into ~/.vim/colors.
let s:badwolf_root = expand('<sfile>:p:h')
if filereadable(s:badwolf_root . '/colors/badwolf.vim')
  execute 'set runtimepath^=' . fnameescape(s:badwolf_root)
endif

" Use UTF-8 everywhere.
set encoding=utf-8
set fileencodings=utf-8,ucs-bom,gb18030,gbk,gb2312,latin1
set fileformats=unix,dos,mac

" Enable syntax highlighting, language detection, filetype plugins, and
" language-aware indentation for Bash, Python, and other common languages.
syntax enable
filetype plugin indent on

" Make colors work well in modern Ubuntu terminals.
if has('termguicolors')
  set termguicolors
endif
set t_Co=256
set background=dark
silent! colorscheme badwolf
if !exists('g:colors_name') || g:colors_name !=# 'badwolf'
  colorscheme desert
endif

" Editing defaults.
set number
set relativenumber
set cursorline
set showcmd
set showmatch
set ruler
set laststatus=2
set wildmenu
set wildmode=longest:full,full
set hidden
set mouse=a
set backspace=indent,eol,start
set clipboard=unnamedplus

" Search defaults.
set ignorecase
set smartcase
set incsearch
set hlsearch

" Whitespace defaults.
set expandtab
set tabstop=4
set shiftwidth=4
set softtabstop=4
set smartindent
set autoindent
set nowrap
set list
set listchars=tab:>-,trail:·,extends:>,precedes:<,nbsp:+

" Keep swap/backup files out of project directories when possible.
set backup
set writebackup
set undofile
if isdirectory(expand('~/.vim/tmp')) || mkdir(expand('~/.vim/tmp'), 'p')
  set backupdir^=~/.vim/tmp//
  set directory^=~/.vim/tmp//
  set undodir^=~/.vim/tmp//
endif

" Recognize common file extensions that older Vim builds may miss.
augroup badwolf_filetypes
  autocmd!
  autocmd BufNewFile,BufRead *.bash,*.bashrc,*.bash_profile,*.bash_aliases setfiletype sh
  autocmd BufNewFile,BufRead *.zsh,*.zshrc setfiletype zsh
  autocmd BufNewFile,BufRead *.py,*.pyw,*.pyi setfiletype python
  autocmd BufNewFile,BufRead *.js,*.mjs,*.cjs setfiletype javascript
  autocmd BufNewFile,BufRead *.ts,*.tsx setfiletype typescript
  autocmd BufNewFile,BufRead *.json,*.jsonc setfiletype json
  autocmd BufNewFile,BufRead *.yaml,*.yml setfiletype yaml
  autocmd BufNewFile,BufRead *.md,*.markdown setfiletype markdown
  autocmd BufNewFile,BufRead Dockerfile,*.Dockerfile setfiletype dockerfile
  autocmd BufNewFile,BufRead *.service,*.timer,*.socket setfiletype systemd
augroup END

" Language-specific indentation and formatting.
augroup badwolf_language_settings
  autocmd!
  autocmd FileType sh,zsh,bash setlocal expandtab tabstop=2 shiftwidth=2 softtabstop=2
  autocmd FileType python setlocal expandtab tabstop=4 shiftwidth=4 softtabstop=4 textwidth=88 colorcolumn=89
  autocmd FileType javascript,typescript,typescriptreact,json,html,css,yaml setlocal expandtab tabstop=2 shiftwidth=2 softtabstop=2
  autocmd FileType markdown setlocal wrap linebreak spell textwidth=80
  autocmd FileType make setlocal noexpandtab tabstop=4 shiftwidth=4 softtabstop=0
augroup END
