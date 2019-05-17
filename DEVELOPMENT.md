# Development

1. Clone the repository.
2. ```vit/command_line.py``` is the entry point for the application. To run it without a full installation:
    * Set the ```PYTHONPATH``` environment variable to the root directory of the repository
    * Run it with ```python vit/command_line.py```
    * A snazzier option is to create a command line alias. For bash:
        * ```alias vit='PYTHONPATH=[path_to_root_dir] python vit/command_line.py'```

### Architecture

VIT 2.x is currently in alpha release, and the architecture is subject to change at any time. There's still quite a bit of refactoring left.

The long-term vision is:

 * Solid test coverage
 * Plenty of inline documentation
 * An interface-driven, modular design that allows most components to be overridden/customized
 * A plugin architecture where appropriate (a good example would be the elements of the top status bar -- each element could be a plugin, allowing third-party plugins to be written and used in that portion of the app)
