# Frequently asked questions

### How do I fix UnknownTimeZoneError in Windows Subsystem for Linux?

If you're running VIT in
[Windows Subsystem for Linux](https://docs.microsoft.com/en-us/windows/wsl/about)
and getting errors like the following:

```sh
  pytz.exceptions.UnknownTimeZoneError: 'local'
```

You'll need to properly set the ```TZ``` environment variable to your
[local time zone](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones), e.g.:

```sh
  export TZ="America/New_York"
```

It's recommended to add this to one of your shell's startup scripts.

### Running custom scripts from VIT

The easiest way to run a custom script is to make sure it's in your `$PATH`. In this example we have a custom script in `/.config/vit/scripts/set_tags` (notice: it does not end in `.sh`)

1. Create a custom script in `~/.config/vit/scripts/set_tags`
2. Setup the script, example:
   
  ```shell
  !#/bin/bash
  
  # --- Add the three tags to the task (accepts numeric ID or UUID) ---
  task rc.confirmation=off "$1" modify +tag1 +tag2 +tag3
  ```

3. Make the file executable with `chmod +x /.config/vit/scripts/set_tags`
4. Add the `script` directory to your `$PATH` by running: `export PATH="$HOME/.config/vit/scripts:$PATH"` (you can automate this by adding it to your startup shell commands in `.bashrc`, `.zshrc` or any other shell you use)
5. Add a custom keybinding to your VIT config
   
   ```shell
   # ~/.config/vit/config.ini
   ...
   p = :!wr set_tags {TASK_ID}<Enter>
   ```
   
7. You should now be able to run the script from the CLI or via VIT with your keybinding (in this case `p`)

   ```shell
   # Via CLI
   set_tags <TASK_UUID>
   ```
