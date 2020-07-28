# Development

1. Clone the repository
2. Change to the root directory
3. ```pip install -r requirements.txt```
4. ```vit/command_line.py``` is the entry point for the application. To run it without a full installation:
    * Set the ```PYTHONPATH``` environment variable to the root directory of the repository
    * Run it with ```python vit/command_line.py```
    * A snazzier option is to create a command line alias. For bash:
        * ```alias vit='PYTHONPATH=[path_to_root_dir] python vit/command_line.py'```

### Tests
 * Located in the ```tests``` directory
 * Run with ```./run-tests.sh```

### Debugging

VIT comes with a simple ```debug``` class for pretty-printing variables to
console or file. The file's default location is ```vit-debug.log``` in the
system's temp directory.

Usage in any of the code is straighforward:

```python
import debug
debug.console(variable_name)
debug.file(variable_name)
```

### Architecture

Whereas VIT 1.x simply layered an
[ncurses](https://en.wikipedia.org/wiki/Ncurses)
interface over CLI calls to the ```task``` binary, VIT 2.x handles
data/reporting differently:
 * Data is read from Taskwarrior via the [export](https://taskwarrior.org/docs/commands/export.html) functionality using [tasklib](https://github.com/robgolding/tasklib)
 * Reports are generated via custom code in VIT, which allows extra features not found in Taskwarrior. Most report-related settings are read directly from the Taskwarrior configuration, which *mostly* allows a single point of configuration
 * Data is written to Taskwarrior using a combination of ```import``` commands driven by [tasklib](https://github.com/robgolding/tasklib), and CLI calls for more complex scenarios


### Roadmap

The long-term vision is:

 * Solid test coverage
 * Plenty of inline documentation
 * An interface-driven, modular design that allows most components to be overridden/customized
 * A plugin architecture where appropriate (a good example would be the elements of the top status bar -- each element could be a plugin, allowing third-party plugins to be written and used in that portion of the app)
