# Customization

### Configuration

#### VIT's configuration

VIT provides a user directory that allows for configuring basic settings *(via ```config.ini```)*, as well as custom themes, formatters, and keybindings.

VIT searches for the user directory in this order of priority:

1. The ```VIT_DIR``` environment variable
2. ```~/.vit``` (the default location)
3. A ```vit``` directory in any valid [XDG base directory](https://specifications.freedesktop.org/basedir-spec/basedir-spec-latest.html)

#### Taskwarrior configuration

By default, VIT uses the default location of the Taskwarrior configuration file to read configuration from Taskwarrior.

Use the ```taskrc``` setting in the ```taskwarrior``` section of ```config.ini``` to override this, or set the ```TASKRC``` environment variable to override both the VIT config file and the default Taskwarrior configuration file location.

### Themes

To provide your own theme:

1. Create a ```theme``` directory in the user directory
2. Copy over one of the core themes, and customize to your liking.
3. Set the ```theme``` setting in ```config.ini``` to the name of your theme without the ```.py``` extension. For example, if you created a theme at ```theme/mytheme.py```, then you would set ```theme = mytheme``` in ```config.ini```

VIT uses the [urwid](http://urwid.org) console user interface library, and the theme is essentially an urwid color palette. Check out their [tutorial](http://urwid.org/tutorial) to learn more.

### Formatters

VIT provides all the standard formatters used in Taskwarrior. If you choose, you can override any default formatter with your own:

1. Create a ```formatter``` directory in the user directory
2. Find the formatter you want to override, e.g. ```description.truncated```
3. Create the override file name by replacing dots with underscores, and adding a ```.py``` extension. For the above example, that would be ```description_truncated.py```
4. Import a [base formatter](vit/formatter/__init__.py), or one of the other more specialized formatters.
5. Name the class by CamelCasing the file name. For the above example, that would be ```class DescriptionTruncated```
6. Provide a ```format(self, value, task)``` method to the class. ```value``` is the column value for the task in question, ```task``` is the entire task object. The method should return a tuple, the first element is the total length of the formatted text, and the second element is any valid urwid [text markup](http://urwid.org/manual/displayattributes.html#text-markup)

An excellent place to use custom formatters is for UDA columns that you want formatted in some non-standard way. For example, let's suppose you have a ```notes``` UDA created, and you want to display that in reports, but in a truncated format. Here's an example of a custom formatter that would accomplish that:

```python
from vit.formatter.description_truncated import DescriptionTruncated

class Notes(DescriptionTruncated):
    def format(self, notes, task):
        if not notes:
            return self.markup_none(self.colorize())
        truncated_notes = self.format_description_truncated(notes)
        return (len(truncated_notes), self.markup_element(truncated_notes))

    def colorize(self, notes=None):
        return self.colorizer.uda_string(self.column, notes)
```

There are tons of existing formatters to use as examples, and the  [base formatters](vit/formatter/__init__.py) include the most common helper methods.

### Keybindings

VIT exposes actions to be mapped to keybindings however you like, and custom macros can also be triggered by keybindings.

By default, VIT uses the ```keybinding/vi.ini``` configuration to provide Vi-style bindings.

To see the list of actions that can be mapped, execute ```vit --list-actions```.

#### To override default keybindings:

The ```[keybinding]``` section in ```config.ini``` overrides any core keybindings or keybindings that you place in the user ```keybinding``` directory. If you just want to make some small tweaks and/or add some macros, it's probably better to take this approach.

The [config.sample.ini](vit/config/config.sample.ini) has many examples to illustrate how to customize keybindings for actions and add macros, check it out!

#### To provide your own custom variable replacements:

VIT exposes a simple API to provide your own variable replacements in keybindings.

Variables enclosed in curly brackets that VIT doesn't know about will be passed to your custom code,
where you can match against the variable, and parse the string to extract metadata in the form of
arguments that you pass to your custom replacement callback.

To provide custom variable replacement:

1. In your user ```keybinding``` directory, create ```keybinding.py```
2. Create a ```Keybinding``` class in that file
3. Expose a ```replacements``` method in that class, that returns a list of replacement configuration objects
4. Replacement configuration objects have the following keys:
  * match_callback: should be a function with one argument, which is the variable to test for a match against.
    If the variable matches your case, return a list with any arguments you want passed to your replacement callback.
  * replacement_callback: should be a function, with the task object as the first argument, followed by the other
    arguments you returned from the match callback, and should return a string replacement for the variable.

Here's a minimal example:

```python
# keybinding/keybinding.py
class Keybinding:
    def replacements(self):
        def _custom_match(variable):
            if variable == 'TEST':
                return ['pass']
        def _custom_replace(task, arg):
            return 'TEST:%s' % arg
        return [
            {
                'match_callback': _custom_match,
                'replacement_callback': _custom_replace,
            },
        ]
```

#### To provide your own default keybindings:

*NOTE: This functionality is more suited to users who want to do something completely different than a Vi-style workflow -- most users will simply want to make some tweaks in the ```[keybinding]``` section of ```config.ini```.*

1. Create a ```keybinding``` directory in the user directory
2. Copy over one of the core keybindings, and customize to your liking.
3. Set the ```default_keybindings``` setting in ```config.ini``` to the name of the keybinding file you created, without the ```.ini``` extension. For example, if you created ```keybinding/strange.ini```, you would set ```default_keybindings = strange``` in ```config.ini```

#### Keybinding suggestions

##### Jumping with digits

As jumping to tasks is central to VIT's operation, you might want to map each
digit key to an `ex` command containing that digit, by adding the following to
your keybindings:

```
1 = :1
2 = :2
3 = :3
4 = :4
5 = :5
6 = :6
7 = :7
8 = :8
9 = :9
```

Now, for example, to jump to a task whose ID is 42, you need to press `4`, `2`
and `<Enter>`, instead of `:`, `4`, `2` and `<Enter>`.
This saves a `:` keypress whenever jumping to a task.

### Auto-refreshing VIT's interface

*Note: Windows unfortunately does not support the `SIGUSR1` signal, so this feature is not currently available in that environment.*

VIT was designed to be used in a request/response manner with the underlying TaskWarrior database, and by default its interface does not refresh when there are other changes happening outside of a specific VIT instance.

However, VIT provides some basic mechanisms that, when combined, allow for an easy implementation of an auto-refreshing interface:

* **Signal handling:** Sending the `SIGUSR1` signal to a VIT process will cause it to refresh its interface (the equivalent of the `{ACTION_REFRESH}` action keybinding
* **PID management:** Configuring `pid_dir` in `config.ini` will cause VIT to manage PID files in `pid_dir`. Executing VIT with the `--list-pids` argument will output all current PIDs in `pid_dir` to standard output
* **Instance environment variable:** VIT injects the `IS_VIT_INSTANCE` environment variable into the environment of the running process. As such, processes invoked in that environment have access to the variable

#### Refresh all VIT instances example

[vit-external-refresh.sh](scripts/vit-external-refresh.sh) provides an example leveraging signals to externally refresh all local VIT interfaces. To use, make sure:

* The script is executable, and in your `PATH` environment variable
* You've properly set `pid_dir` in `config.ini`

#### Refresh VIT when TaskWarrior updates a task

[on-exit-refresh-vit.sh](scripts/hooks/on-exit-refresh-vit.sh) provides an example TaskWarrior hook that will automatically refresh all local VIT interfaces when using Taskwarrior directly. To use, make sure:

* The script is executable, [named properly](https://taskwarrior.org/docs/hooks.html), and placed in TaskWarrior's hooks directory, usually `.task/hooks`
* [vit-external-refresh.sh](scripts/vit-external-refresh.sh) is configured correctly as above

#### Other refresh scenarios

The basic tools above can be used in other more complex scenarios, such as refreshing VIT's interface after an automated script updates one or more tasks. The implementation details will vary with the use case, and are left as an exercise for the user.
