# Customization

### Configuration

VIT provides a user directory that allows for configuring basic settings *(via ```config.ini```)*, as well as custom themes, formatters, and keybindings.

By default, the directory is located at ```~/.vit```

To customize the location of the user directory, you can set the ```VIT_DIR``` environment variable.

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

To provide your own keybindings:

1. Create a ```keybinding``` directory in the user directory
2. Copy over one of the core keybindings, and customize to your liking.
3. Set the ```default_keybindings``` setting in ```config.ini``` to the name of the keybinding file you created, without the ```.ini``` extension. For example, if you created ```keybinding/strange.ini```, you would set ```default_keybindings = strange``` in ```config.ini```
4. Note that the ```[keybinding]``` section in ```config.ini``` overrides any core keybindings or keybindings that you place in the user ```keybinding``` directory. If you just want to make some small tweaks, it's probably better to use the section in ```config.ini```. This functionality is more suited to users who want to do something completely different than a Vi-style workflow.
