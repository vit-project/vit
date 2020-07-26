## Creating a test case

If you file an issue that requires some TaskWarrior setup to replicate, the
developers may ask you to create a 'test case' script in order to aid in
the troubleshooting.

Doing so is fairly straightforward:

1. Use the [dummy install script](scripts/generate-dummy-install.sh) as a
   starting place
2. Adjust the script by editing the the task commands
   * You can remove the default ones if needed
   * You can add any new task command needed to set up the data necessary to
     reproduce your issue
3. Once you have the script complete, run it locally to make sure you can
   reproduce the issue you're reporting
4. Attach the script to the issue you've filed
