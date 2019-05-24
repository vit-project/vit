# Installation

 1. Make sure you have a supported version of [Python](https://www.python.org) installed, and [pip](https://pypi.org/project/pip), Python's package manager.
 2. Decide what Python 'environment' you want to install vit into. Projects like [Virtualenv](https://virtualenv.pypa.io) and [pyenv](https://github.com/pyenv/pyenv) allow you to run non-system Python installations, and are the recommended way to safely install additional Python packages. You may also choose to install vit as a package in your system's Python installation.
 3. Once you've decided what environment to install to, simply run:
     ```pip install vit```

##### Tab completion

Since VIT takes report/filter arguments when invoked (just like TaskWarrior), it can be helpful to leverage TaskWarrior's existing tab completion functionality when starting VIT.

[scripts/bash/vit.bash_completion](scripts/bash/vit.bash_completion) provides a wrapper to TaskWarrior's [bash completion](https://github.com/scop/bash-completion) support.

Place that file somewhere that the bash completion software can load it, and restart your shell to use.