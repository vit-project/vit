#!/usr/bin/perl -w
#
# VIT - Visual Interactive Taskwarrior
#
# @BUILD@
#

use strict;
use Curses;
use Time::HiRes qw(usleep);

our $commands_file = '/usr/local/etc/vit-commands';

our $audit = 0;
our @colors2pair;
our $convergence = 'unknown';
our $current_command = 'unknown';
our $cursor_position = 'unknown';
our $debug = 1;
our $default_command = 'next';
our $display_start_idx = 0;
our $error_msg = '';
our $flash_delay = 80000;
our $header_win;
our $num_tasks = 0;
our $feedback_msg = '';
our @parsed_tokens = ();
our @parsed_colors_fg = ();
our @parsed_colors_bg = ();
our @parsed_attrs = ();
our $prev_command = 'next';
our $prev_display_start_idx;
our $prev_task_selected_idx;
our $prompt_win;
our $reread_needed = 0;
our $report_descr = 'unknown';
our $report_win;
our @report_header_tokens = ();
our @report_header_colors_fg = ();
our @report_header_colors_bg = ();
our @report_header_attrs = ();
our @report_tokens = ();
our @report_types = ();
our @report_colors_fg = ();
our @report_colors_bg = ();
our @report_attrs = ();
our @report2taskid = ();
our @taskid2report = ();
our $tasks_completed = 0;
our $tasks_pending = 0;
our $task_selected_idx = 0;
our $titlebar = 0;
our $version = '@VERSION@';
our $REPORT_LINES;
our $REPORT_COLS;

our $COLOR_HEADER = 1;
our $COLOR_ERRORS = 2;
our $COLOR_SELECTION = 3;
our $COLOR_EMPTY_LINE = 4;
our $next_color_pair = 5;

require 'args.pl';
require 'cmdline.pl';
require 'cmds.pl';
require 'color.pl';
require 'exec.pl';
require 'curses.pl';
require 'draw.pl';
require 'env.pl';
require 'getch.pl';
require 'misc.pl';
require 'prompt.pl';
require 'read.pl';
require 'screen.pl';

###################################################################
## main...

&parse_args();
&init_shell_env();
&init_curses('init');
&init_task_env();
&read_report('init');
&draw_screen();
&getch_loop();
endwin();
exit();

