##### Sat Sep 28 2019 - released v2.0.0

* **Fri Sep 27 2019:** add UPGRADE.md, include v2.0.0 upgrade instructions
* **Thu Sep 26 2019:** fix crash when shlex cannot parse a string to args
* **Wed Sep 18 2019:** fix #201: fall back to previous list position when no task found
* **Tue Sep 17 2019:** fix #202: properly group different filter types
* **Tue Sep 17 2019:** fix #203: Account for edge case with single adjusted column
* **Sun Sep 15 2019:** platform-independent temp dir, better debug file name
* **Thu Aug 22 2019:** fix crash for reports with no sort specified
* **Wed Aug 21 2019:** fix #200: change {TASKID} variable to {TASK_UUID}

##### Sun Aug 18 2019 - released v2.0.0b2

* **Thu Aug 15 2019:** Remove MAX_COLUMN_WIDTH (Closes: #190)
* **Tue Aug 06 2019:** fix #196: Add action to sync with taskd
* **Tue Aug 06 2019:** fix #197: Allow disabling mouse support
* **Sun Aug 04 2019:** Correct import of vit modules in option parser
* **Mon Jul 22 2019:** fix #187: TZ env not setup by default in WSL
* **Sun Jul 21 2019:** fix #136: Context support in vit

##### Fri Jul 19 2019 - released v2.0.0b1

* **Thu Jun 20 2019:** only activate autocomplete for autocomplete capable ops
* **Tue Jun 11 2019:** add script to generate a dummy installation
* **Mon Jun 10 2019:** fix #186: test for project column in report before updating project column header
* **Sun Jun  9 2019:** test for existence of project column when determining subproject_indentable report setting
* **Fri Jun  7 2019:** remove support for inverse color attribute, also add a caveat note to COLOR.md for a workaround
* **Wed Jun  5 2019:** try to focus by task UUID in no confirmation case
* **Wed Jun  5 2019:** fix #183: Confirmation dialog when starting a task
* **Fri May 31 2019:** fix #180: Crash when tasklib raises exception for illegal operation
* **Fri May 31 2019:** fix #182: User not returned to previous task on tasks after first page
* **Wed Jun  5 2019:** fix #183: Confirmation dialog when starting a task
* **Thu May 30 2019:** fix #178: Smarter column width formatting
* **Mon May 27 2019:** add missing color mappings for bright black/white
* **Sun May 26 2019:** id or short uuid for done
* **Sun May 26 2019:** fix endless loop on forward search with no results
* **Sun May 26 2019:** id or short uuid for delete/start/stop
* **Sat May 25 2019:** fix #179: Search forward and reverse should use same history

##### Sat May 25 2019 - released v2.0.0a1

**IMPORTANT NOTE:** This is an alpha release, no guarantees are made for stability or data integrity. While the author has used the alpha code for over a month with no data corruption issues, it is strongly recommended to back up your data prior to usage.

Complete ground up rewrite in Python, feature-complete with VIT 1.x. New features include:

 * Advanced tab completion
 * Per-column colorization with markers *(see [COLOR.md](COLOR.md))*
 * Intelligent sub-project indenting
 * Multiple/customizable themes
 * Override/customize column formatters
 * Fully-customizable key bindings
 * Table-row striping
 * Show version/context/report execution time in status area
 * Customizable config dir
 * Command line bash completion wrapper

 This release also changes the software license from GPL to MIT.

##### Mon Aug  6 2018 - released v1.3.beta1
```
 Sat Jun 14 2018 - fix "Negative repeat count does nothing" errors (GH#153)
 Sat Jun 24 2017 - introduce feature for adding/removing tags (GH#5)
 Sat Jun 24 2017 - add config option to disable wait prompts (GH#12)
 Fri Jun 23 2017 - add config option to disable confirmation (GH#4)
 Fri Jun 23 2017 - add "wait" command bound to 'w' (GH#3)
 Sun Mar 12 2017 - add ctrl+g synonym for escape
 Sun Mar 12 2017 - add start/stop toggle bound to 'b' (GH#152, part of GH#126)
 Sat Aug 30 2016 - fix handling of CJK characters (GH#142)
 Sat Aug  6 2016 - fix for multi-byte searches
 Sun Jul 24 2016 - fix for multi-byte prompt input
 Sun Jul 24 2016 - fix display of multi-byte report data
 Sun Jul 17 2016 - do not exit if terminal resized to small height
 Mon Jun 20 2016 - work around another instance of the Perl warning
 Mon May 16 2016 - work around a warning from Perl versions >= v5.21.1
 Sun Jan 10 2016 - annotations now correctly escape any character
 Sun Jan 10 2016 - do not exit when invalid regex for search string (GH#148)
 Sat Jan  9 2016 - clean up terminal on a Perl error or warning (part of GH#148)
 Fri Jan  8 2016 - do not run 'task burndown' by default
 Fri Jan  8 2016 - add config variable for 'task burndown'
 Tue Jan  5 2016 - add support for config variables. See 'man vitrc'
 Wed Sep 30 2015 - improve detection of annotations (GH#144)
 Sun Mar  8 2015 - do not beep on a 'g' keystroke
 Sat Mar  7 2015 - fix a bug where prompt text was invisible
 Wed Mar  4 2015 - add support for End and Home keys (GH#137)
 Mon Mar  2 2015 - add support for Del key in prompts (GH#120)
 Sun Mar  1 2015 - allow Taskwarrior cmds to parse for 'a' and 'm' (GH#132, GH#135)
 Sun Mar  1 2015 - in screen, VIT now highlights the entire line (GH#81, GH#129)
 Sun Mar  1 2015 - update display after sync (GH#112)
 Tue Aug 26 2014 - 'n'/'N' now work when not right after search
 Sun Aug 24 2014 - store commands file in %prefix%/share/vit/
 Wed Jul 30 2014 - update documentation URLs
 Fri Jun 27 2014 - add prompt history scrolling with arrows (GH#54, GH#58)
 Thu Jun 26 2014 - install files in more conventional paths (GH#118)
 Wed Jun 25 2014 - fix vitrc man file (GH#119)
 Wed Jun 25 2014 - Makefile no longer requires sudo (GH#118)
 Sat Jun 21 2014 - '-version' prints the git hash if available
 Fri Jun 20 2014 - all of vit's options work with two dashes
 Fri Jun 20 2014 - 'vit -help' has 0 exit code
 Fri Jun 20 2014 - 'vit -version' prints the version (GH#114)
```

##### Sun Apr  6 2014 - released v1.2
```
 Tue Apr  1 2014 - the <Esc> key can now be used in shortcuts
 Tue Apr  1 2014 - exit with informative error if shortcut too long (see GH#103)
 Thu Mar 13 2014 - fix colors for running VIT in tmux
 Sat Mar  8 2014 - do not print control characters to prompts
 Thu Mar  6 2014 - fix recognition of backspace in tmux
 Thu Mar  6 2014 - fix a prompt bug that prevented editing
 Mon Mar  3 2014 - 'vit -audit' now creates a log with debug info
```

##### Tue Feb  4 2014 - released v1.2.beta1
```
 Tue Feb  4 2014 - Add VIT man pages (#1284)
 Mon Oct 21 2013 - Implement cursor movement in prompts (#1403)
 Sun Oct  6 2013 - Clear project prompt string if escape (#1232)
 Sun Oct  6 2013 - Remove confusing behavior from arrow keys in prompts (#1363)
 Sun Sep 28 2013 - 'P' now sets priority and 'h', 'm', 'l', 'n' are freed (#1238)
 Sun Sep 27 2013 - 'c' is renamed to 'm' (#1231)
 Sun Sep 15 2013 - 't' now opens the command prompt with ":!rw task "
 Sun Sep 15 2013 - shell commands can now pass the arguments VIT is using (#1338, #1237)
 Sat Sep 14 2013 - custom keybinds can now be specified in ~/.vitrc (#1237, #1302, #1336)
 Thu Sep 12 2013 - added ':!' to execute arbitrary string in shell
 Sun Aug 12 2013 - When running an external command, VIT no longer echoes it
 Sun Aug 11 2013 - VIT now cleans the terminal before exiting
 Sun Aug 11 2013 - 'q' ('Q') now quits with(out) confirmation (#1266)
 Thu Aug  9 2013 - fix a bug where prompt text was invisible
 Mon Aug  5 2013 - 's' now runs 'task sync' if Taskwarrior >= 2.3.0 (#1301)
 Sun Aug  4 2013 - when in search mode, backspace now removes a character
 Sat Aug  3 2013 - 'D' now deletes a task when not over an annotation (#1230)
 Sat Jul  6 2013 - added Copyright 2013, Scott Kostyshak
 Sat Jul  6 2013 - added an AUTHORS file listing contributors
 Sat Jul  6 2013 - 'gg' now moves to first line (#1229)
 Sun Jun 23 2013 - added Copyright 2012 - 2013, Steve Rader
```

##### Wed Apr  3 2013 - released v1.1
```
 Wed Apr  3 2013 - fixes for not having color=on set in ~/.taskrc
 Sun Mar 31 2013 - added <enter> for task info
 Sun Mar 31 2013 - added logging error msgs when "-audit" is used
 Sun Mar 31 2013 - added support for selection effects (e.g. bold)
 Sun Mar 31 2013 - added setting the VIT header color via color.vit.header setting
 Sat Mar 30 2013 - set the VIT header color via the color.header setting
 Fri Mar 29 2013 - added support for the "inverse" and "bright" effects
 Fri Mar 29 2013 - fixed parsing some ANSI underline effect escape sequences
 Fri Mar 29 2013 - clear the screen before exec'ing external commands as per feature #1214
 Fri Mar 29 2013 - fixed a bug where some commands (e.g. ":h") incorrectly waited after exec'ing
 Fri Mar 29 2013 - added setting the default report via command line args as per feature #1216
 Fri Mar 29 2013 - added support to allow for verbose=off as per topic #2851
 Fri Mar 29 2013 - disallowed using a default.command which doesn't include an "ID" column
 Fri Mar 29 2013 - added support for multiple effects, e.g. bold underline
```

##### Sun Mar 24 2013 - released v1.0
```
 Sun Mar 24 2013 - added '=' for task info as per feature #1156
 Sun Mar 24 2013 - added 'u' for task undo
 Thu Jan  1 2013 - fixed a bug where '/' and '?' caused a crash as per bug #1152
 Wed Dec 12 2012 - added graceful handling of marking only task in current report "done"
 Wed Dec 12 2012 - added "blinking" of the convergence info when convergence changes
 Wed Dec 12 2012 - disallowed marking completed tasks as "done"
 Wed Dec 12 2012 - fixed a problem where the selection could get lost after resize and '^l'
```

##### Tue Dec 11 2012 - released v0.7
```
 Mon Dec 10 2012 - added ./configure checks for the perl Curses and Time::HiRes modules
 Mon Dec 10 2012 - added ./configure ab-end when /usr/bin/perl doesn't exist
 Mon Dec 10 2012 - added ./configure substitution for the localized path to the "task" command
 Sun Dec  9 2012 - fixed a problem where the selection color was lost after refresh
 Sun Dec  9 2012 - added '/', '?', 'n' and 'N' for searching the current report
 Sat Dec  8 2012 - added color.label to taskrc-gtk+
 Fri Dec  7 2012 - added <tab> completion when using 'p' to set project
 Thu Dec  6 2012 - added 'p' for setting project
```

##### Wed Dec  5 2012 - released v0.6
```
 Wed Dec  5 2012 - added 'n' for setting priority to none
 Wed Dec  5 2012 - added 'l' for setting priority to L
 Wed Dec  5 2012 - added 'm' for setting priority to M
 Wed Dec  5 2012 - added 'h' for setting priority to H
 Tue Dec  4 2012 - added 'f' for filter the current report
 Mon Dec  3 2012 - added checking of task command closing short pipe error
 Mon Dec  3 2012 - added checking of task command exit status
 Sun Dec  2 2012 - added 'D' for delete the current annotation (denotate)
 Sat Dec  1 2012 - added 'A' for add an annotation to the current task
 Sat Dec  1 2012 - added 'e' for edit current task
 Sat Dec  1 2012 - fixed problems with the header attributions (bold and underline)
```

##### Fri Nov 30 2012 - released v0.5
```
 Fri Nov 30 2012 - added ./configure (autoconf)  (e.g. "./configure --prefix=/usr/local/vit")
 Thu Nov 29 2012 - added support for '^w' (erase word) at the command line
 Thu Nov 29 2012 - added default.command to the list of available reports
 Wed Nov 28 2012 - added support for ":REPORT <filter>" syntax (e.g. ":minimal prio:H")
 Wed Nov 28 2012 - added support for the DEL key ('^?') as per bug #1134
```

##### Wed Nov 28 2012 - released v0.4
```
 Wed Nov 28 2012 - added ":N" for move to task number N
 Wed Nov 28 2012 - fixed problems with task reports that have no matches
 Wed Nov 28 2012 - added ":h PATTERN" for help about PATTERN (e.g. ":h help")
 Tue Nov 27 2012 - added ":h" for help
 Tue Nov 27 2012 - removed the Term::ReadKey requirement
 Tue Nov 27 2012 - removed xterm only requirement as per feature #1132
 Tue Nov 27 2012 - fixed problems with marking the last task done
 Mon Nov 26 2012 - added ":STRING<tab>" and ":<tab>" for changing the current report
 Mon Nov 26 2012 - added ":REPORT" (e.g. ":long") for changing the report
 Mon Nov 26 2012 - fixed problems with single tick and double quote
```

##### Mon Nov 26 2012 - released v0.3
```
 Mon Nov 26 2012 - added support for bold and underlines ANSI colors
 Sun Nov 25 2012 - wrote taskrc-gtk+
 Sun Nov 25 2012 - added task-native colorization
 Sat Nov 24 2012 - added ' ' for move down one line
```

##### Sat Nov 24 2012 - released v0.2
```
 Sat Nov 24 2012 - various changes for task version 2.x
 Sat Nov 24 2012 - added ":s/OLD/NEW/" for change description (e.g. ":s/opps/oops/")
 Fri Nov 23 2012 - added ":q" for quit
 Fri Nov 23 2012 - added 'c' for change current task
```

##### Fri Nov 23 2012 - released v0.1
```
 Fri Nov 23 2012 - added 'a' for add task
 Wed Nov 21 2012 - added 'd' for mark current task done
 Tue Nov 20 2012 - added the 'G' and '0'
 Mon Nov 19 2012 - added the '^f' and '^b'
 Sun Nov 18 2012 - added the 'L', 'M' and 'H'
 Sat Nov 17 2012 - added the 'j' and 'k'
 Fri Nov 16 2012 - designed the layout
```
