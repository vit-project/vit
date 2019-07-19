# VIT

Visual Interactive Taskwarrior full-screen terminal interface.

**IMPORTANT:** VIT 2.x is currently in beta release, and is looking for testers/contributors. The featureset of VIT 1.x has been fully implemented, and the author is already using it for everyday interface with Taskwarrior.

*For VIT 1.3, [visit here](https://github.com/scottkosty/vit/tree/1.3)*

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
 * [Python](https://www.python.org) 3.5+
 * [pip](https://pypi.org/project/pip)

## Installation

Follow the directions in [INSTALL.md](INSTALL.md)

#### Recommendations:

 * VIT will suggest to install a default user config file if none exists -- it's fully commented with all configuration options, check it out.
 * Do ```vit --help``` *(know the vit command line arguments)*
 * Do ```:help``` in vit *(look over the "commands")*
 * Use an xterm terminal *(for full color support)*
 * For suggestions on futher tweaks, see [CUSTOMIZE.md](CUSTOMIZE.md)
 * VIT handles task coloring differently than Taskwarrior, see [COLOR.md](COLOR.md) for more details

#### Development:

Interested in the architecture, or in helping out with development? See [DEVELOPMENT.md](DEVELOPMENT.md)

##### In tribute

 Our friend and collaborator Steve Rader passed away in May 2013.  We owe a lot to Steve for his excellent work, and so vit is preserved, maintained and continued.

 Taskwarrior Team
 support@taskwarrior.org
