Bad Wolf
========

A color scheme for Vim, pieced together by [Steve Losh](http://stevelosh.com/).

There's still quite a lot of room for improvement (particularly in HTML) so feel
free to send me ideas through the [issue tracker][] or pull requests.

It's MIT/X11 licensed, so feel free to hack it apart if you like.

**If you're going to send a pull request that you want me to merge, please post
a comment in it with before/after screenshots!**

[issue tracker]: http://github.com/sjl/badwolf/issues

Screenshots
-----------

These screenshots may be out of date, but they'll at least give you a taste of
what you're in for.

### Python

![Screenshot](http://i.imgur.com/fQGGC.png)

### HTML (Django Templates)

![Screenshot](http://i.imgur.com/LgLar.png)

### Clojure

![Screenshot](http://i.imgur.com/THHz7.png)

### Markdown

![Screenshot](http://i.imgur.com/J56VS.png)


Ubuntu 26.04 Vim configuration
------------------------------

This repository includes a plugin-free `vimrc` suitable for Ubuntu 26.04 development hosts.  It enables Vim syntax highlighting, filetype detection, filetype plugins, and language-aware indentation for Bash, Python, JavaScript/TypeScript, JSON, YAML, Markdown, Dockerfiles, systemd unit files, and other common formats.

Install it with:

```bash
cp vimrc ~/.vimrc
mkdir -p ~/.vim/colors
cp colors/badwolf.vim ~/.vim/colors/
```

Or test it directly from this checkout without installing:

```bash
vim -Nu ./vimrc path/to/file.py
```

Configuration
-------------

There are a few settings you can use to tweak how Bad Wolf looks.

### g:badwolf\_darkgutter

Determines whether the line number, sign column, and fold column are rendered
darker than the normal background, or the same.

    " Make the gutters darker than the background.
    let g:badwolf_darkgutter = 1

Default: `0` (off, gutters are the same as the background)

### g:badwolf\_tabline

Determines how light to render the background of the tab line (the line at the
top of the screen containing the various tabs (only in console mode)).

Can be set to `0`, `1`, `2`, or `3`.

    " Make the tab line darker than the background.
    let g:badwolf_tabline = 0

    " Make the tab line the same color as the background.
    let g:badwolf_tabline = 1

    " Make the tab line lighter than the background.
    let g:badwolf_tabline = 2

    " Make the tab line much lighter than the background.
    let g:badwolf_tabline = 3

Default: `1` (same color as the background)

### g:badwolf\_html\_link\_underline

Determines whether text inside `a` tags in HTML files will be underlined.

    " Turn off HTML link underlining
    let g:badwolf_html_link_underline = 0

Default: `1` (on)

### g:badwolf\_css\_props\_highlight

Determines whether CSS properties should be highlighted.

    " Turn on CSS properties highlighting
    let g:badwolf_css_props_highlight = 1

Default: `0` (off)

Contributing
------------

I'd love pull requests, but won't necessarily merge all of them.  Color schemes
are a very subjective topic -- we don't all have the same taste.

**If you're going to send a pull request that you want me to merge, please post
a comment in it with before/after screenshots!**

## Network Auto-Diagnosis MVP (Python)

This repository now includes a Python MVP under `main.py` + `netdiag/` for factory/campus network diagnosis.

### Quick start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py 192.168.1.10 --port 443 --tracert --https
```

### SSH read-only diagnosis (Huawei first)

```bash
python main.py 10.0.0.2 --ssh --ssh-username ops --ssh-password '***' --ssh-ports GigabitEthernet0/0/1
```

### Notes

- Read-only command whitelist is enforced in `netdiag/ssh_reader.py`.
- Dangerous configuration commands are explicitly blocked.
- A TXT report is generated under `reports/`.
