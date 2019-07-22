## Frequently asked questions

##### How do I fix UnknownTimeZoneError in Windows Subsystem for Linux?

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
