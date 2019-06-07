# VIT Task Coloring

VIT handles task coloring differently than Taskwarrior. Whereas Taskwarrior uses a row-based coloring scheme with color blending, VIT uses a column-based coloring scheme.

This alternate coloring scheme offers several major advantages:

 * Much less overall color noise
 * More meaningful context communicated via color in a single task row

These advantages come with a few tradeoffs:

 * Color cues are sometimes less obvious
 * Reports sometimes cannot display all color information for a task, if the color-related column is not displayed in the report

The first tradeoff most likely becomes less of an issue as the user gets used to the more subtle coloring.

VIT addresses the second tradeoff by introducing the concept of markers.

Markers are short text indicators that appear in the leftmost column of a report when a column *not* in a report contains data that 'triggers' the marker.

By default, markers are tied to the color configuration for the column/state in question, which means that a marker will only appear if the relevant Taskwarrior color setting is also enabled.

Markers are highly configurable, including displaying them without color, and customizing the indicator text for all markers.

For more information on marker and color settings, see the ```marker``` and ```color``` sections in the [default vit configuration file](vit/config/config.sample.ini).

### Caveats

 1. [urwid](http://urwid.org), the library VIT uses for console rendering, does not appear to support discovering the default console colors. Therefore, it becomes impractical to support TaskWarrior's ```inverse``` color attribute. As a workaround, simply replace any color configuration that uses ```inverse``` with the exact foreground/background colors desired. When parsing TaskWarrior's color config, VIT removes the ```inverse``` attribute, which will lead to unexpected color output for the user -- therefore it is recommended to remove/override it anywhere it exists in the TaskWarrior color configuration.
