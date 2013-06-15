#!/usr/bin/perl -w
#
# VIT - Visual Interactive Taskwarrior
#
# @BUILD@
#

use strict;
use Curses;
use Term::ReadKey;
use Time::HiRes qw(usleep);

our $audit = 0;
our @colors2pair;
our $convergence = 'unknown';
our $cursor_position = 'unknown';
our $debug = 1;
our $display_start_idx = 0;
our $error_msg = '';
our $flash_delay = 80000;
our $next_color_pair = 5;
our $num_tasks = 0;
our $feedback_msg = '';
our @parsed_tokens = ();
our @parsed_colors_fg = ();
our @parsed_colors_bg = ();
our @parsed_attrs = ();
our $reread_needed = 0;
our $report_descr = 'unknown';
our @report_header_tokens = ();
our @report_header_colors_fg = ();
our @report_header_colors_bg = ();
our @report_header_attrs = ();
our @report_tokens = ();
our @report_colors_fg = ();
our @report_colors_bg = ();
our @report_attrs = ();
our @report2taskid = ();
our $tasks_completed = 0;
our $tasks_pending = 0;
our $task_selected_idx = 0;
our $titlebar = 0;
our $version = '@VERSION@';

our $header_win;
our $report_win;
our $prompt_win;
our $COLOR_HEADER = 1;
our $COLOR_ERRORS = 2;
our $COLOR_SELECTION = 3;
our $COLOR_SCROLLBAR = 4;
our $REPORT_LINES;
our $REPORT_COLS;

require 'args.pl';
require 'cmdline.pl';
require 'cmds.pl';
require 'color.pl';
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
&set_env();
&init_curses('init');
&read_report();
&draw_screen();
&getch_loop();
endwin();
exit();

