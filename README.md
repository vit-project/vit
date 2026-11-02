[![Test status](https://github.com/vit-project/vit/actions/workflows/tests.yml/badge.svg)](https://github.com/vit-project/vit/actions/workflows/tests.yml)
[![CodeQL](https://github.com/vit-project/vit/actions/workflows/github-code-scanning/codeql/badge.svg)](https://github.com/vit-project/vit/actions/workflows/github-code-scanning/codeql)

# VIT

<img src="images/great-tit-square-small.png" alt="Logo" width="150" height="150" align="right" />

Visual Interactive Taskwarrior full-screen terminal interface.

*For VIT 1.3, [visit here](https://github.com/vit-project/vit/tree/1.3)*


## Features

 * Fully-customizable key bindings *(default Vim-like)*
 * Uncluttered display
 * No mouse
 * Speed
 * Per-column colorization
 * Advanced tab completion
 * Multiple/customizable themes
 * Override/customize column formatters
 * Intelligent sub-project indenting

## Requirements

 * [Taskwarrior](https://taskwarrior.org)
 * [Python](https://www.python.org) 3.11–3.15
 * [pip](https://pypi.org/project/pip)

## Installation

Follow the directions in [INSTALL.md](https://github.com/vit-project/vit/blob/2.x/INSTALL.md)

## Quick start

Run ```vit --help``` from the command line for basic usage instructions.

Run ```vit``` from the command line to start VIT with default config, report, and filters.

While VIT is running, type ```:help``` followed by enter to review basic command/navigation actions.

#### Recommendations:

 * VIT will suggest to install a default user config file if none exists -- it's fully commented with all configuration options, check it out.
 * Do ```vit --help``` *(know the vit command line arguments)*
 * Do ```:help``` in vit *(look over the "commands")*
 * Use an xterm terminal *(for full color support)*
 * For suggestions on further tweaks, see [CUSTOMIZE.md](https://github.com/vit-project/vit/blob/2.x/CUSTOMIZE.md)
 * VIT handles task coloring differently than Taskwarrior, see [COLOR.md](https://github.com/vit-project/vit/blob/2.x/COLOR.md) for more details

#### Troubleshooting:

See [FAQ.md](https://github.com/vit-project/vit/blob/2.x/FAQ.md)

#### Upgrading

Follow the directions in [UPGRADE.md](https://github.com/vit-project/vit/blob/2.x/UPGRADE.md)

#### Development:

Interested in the architecture, or in helping out with development? See [DEVELOPMENT.md](https://github.com/vit-project/vit/blob/2.x/DEVELOPMENT.md)

##### In tribute

 Our friend and collaborator Steve Rader passed away in May 2013.  We owe a lot to Steve for his excellent work, and so vit is preserved, maintained and continued.

 Taskwarrior Team
 support@taskwarrior.org
