# Development

1. Clone the repository and change to its root directory.
2. Create and activate a virtual environment using Python 3.11–3.15. For example, with Python 3.14:

   ```bash
   python3.14 -m venv .venv
   source .venv/bin/activate
   python -m pip install --upgrade pip
   ```

3. Install VIT in editable mode with its development dependencies:

   ```bash
   python -m pip install -e '.[dev]'
   ```

4. Run `vit`. The installed command uses `vit/command_line.py`, and edits to the source take effect without reinstalling.

Runtime dependencies, package metadata, test configuration, the `dev` extra, and the `release` dependency group are defined in `pyproject.toml`. The release dependency group requires pip 25.1 or newer. Taskwarrior must also be installed to run VIT.

### Tests
 * Located in the `test` directory.
 * Run with `python -m pytest` or `./run-tests.sh`. Both accept pytest options, for example `./run-tests.sh -q`.
 * CI tests Python 3.11 through 3.15, including prereleases when necessary.
 * Install the `task` executable to run integration tests. They use private
   Taskwarrior and VIT configuration directories and temporary databases;
   they do not use your tasks, hooks, or synchronization settings. CI installs
   Taskwarrior from Ubuntu 24.04 and runs the complete suite.
 * `python -m pytest -m 'not integration'` runs the fast component tests without
   Taskwarrior. Integration tests are skipped if `task` is unavailable.
 * `python -m pytest -m integration` runs user workflows with real Taskwarrior,
   tasklib, and Urwid widgets. Only terminal lifecycle operations are replaced.
   The shared fixtures live in `test/conftest.py` and `test/support.py`.

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

### Release checklist

For any developer managing VIT releases, here's a simple checklist:

#### Pre-release

 * Check the dependencies and `requires-python` in `pyproject.toml`, and update them if necessary.
 * Keep the Python classifiers, README requirements, and CI test matrix in sync with the supported versions.

#### Release

 * Bump the release number in `vit/version.py`
 * Generate changelog entries using `scripts/generate-changelog-entries.sh`
 * Add changelog entries to `CHANGES.md`
 * Commit
 * Add a `v`-prefixed tag matching the package version (for example, `v2.3.5` for `2.3.5`) and push it.
 * PyPI releases are automated via [PyPI Trusted Publishing](https://docs.pypi.org/trusted-publishers/adding-a-publisher/).
 * Create a Github release for the tag, use the generated changelog entries in the description

#### Post-release

 * Announce on all relevant channels

### Roadmap

The long-term vision is:

 * Plenty of inline documentation
 * An interface-driven, modular design that allows most components to be overridden/customized
 * A plugin architecture where appropriate (a good example would be the elements of the top status bar -- each element could be a plugin, allowing third-party plugins to be written and used in that portion of the app)
