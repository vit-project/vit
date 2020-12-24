This file contains information relevant to upgrading VIT from one version to another. Breaking changes between major versions, and significant changes between release versions will be addressed.

*Note: for upgrade issues prior to VIT 1.3, please see the [legacy changelog](https://github.com/vit-project/vit/blob/1.3/CHANGES)*.

# v2.0.0

Complete ground up rewrite in Python, feature-complete with VIT 1.x.

### New features:

 * Advanced tab completion
 * Per-column colorization with markers *(see [COLOR.md](COLOR.md))*
 * Intelligent sub-project indenting
 * Multiple/customizable themes *(see [CUSTOMIZE.md](CUSTOMIZE.md))*
 * Override/customize column formatters *(see [CUSTOMIZE.md](CUSTOMIZE.md))*
 * Fully-customizable key bindings *(see [CUSTOMIZE.md](CUSTOMIZE.md))*
 * Table-row striping
 * Show version/context/report execution time in status area
 * Customizable config dir *(see [CUSTOMIZE.md](CUSTOMIZE.md))*
 * Command line bash completion wrapper *(see [INSTALL.md](INSTALL.md))*
 * Context support

 This release also changes the software license from GPL to MIT.

### Breaking changes:

 * Configuration has been moved from ```${HOME}/.vitrc``` to ```${HOME}/.vit/config.ini``` -- the location of the config directory can be customized, see [CUSTOMIZE.md](CUSTOMIZE.md) for details.
 * The format of the configuration file has changed, customizations in the legacy ```.vitrc``` file will need to be manually ported to the new format. The [config.sample.ini](vit/config/config.sample.ini) file is *heavily* commented, and should contain reference to everything you need to migrate the legacy configuration. If no ```config.ini``` exists in the VIT configuration directory, VIT will offer the option to install the sample config upon startup -- this is the easiest way to get started with porting and customization.
 * The method of removing annotations from tasks has changed. It is now mapped to the ```ACTION_TASK_DENOTATE``` core action, which in the default keybindings is triggered by ```<Shift>e``` when the task is highlighted.
 * VIT 1.3 supports Taskd sync via the ```s``` keybinding, which was undocumented. VIT 2.x properly documents this functionality, and moves it to the keybinding ```<Shift>s``` by default.
 * The ```burndown``` configuration option and display has been removed -- it may be added again in a future release or via plugin functionality.
