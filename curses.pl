# Copyright 2012 - 2013, Steve Rader
# Copyright 2013 - 2014, Scott Kostyshak

sub init_curses {
  my $m = $_[0];
  initscr();
  noecho();
  curs_set(0);
  start_color();
  use_default_colors();
  init_pair($COLOR_ERRORS,COLOR_WHITE,COLOR_RED);
  if ( $m eq 'init' ) {
    init_pair($COLOR_SELECTION,COLOR_WHITE,COLOR_BLUE);
  }
  init_pair($COLOR_EMPTY_LINE,COLOR_BLUE,-1); # blue foreground
  my $HEADER_SIZE = 3;
  $REPORT_LINES = $LINES - $HEADER_SIZE - 1;
  $REPORT_COLS = $COLS - 2;
  $header_win = newwin($HEADER_SIZE, $COLS, 0, 0);
  $report_win = newwin($REPORT_LINES+$HEADER_SIZE, $REPORT_COLS+2, 3, 1);
  $prompt_win = newwin(1, $COLS, $LINES-1, 0);
  keypad($report_win, 1);
  keypad($prompt_win, 1);
}

#------------------------------------------------------------------

sub get_color_pair {
  my($fg,$bg) = @_;
  my $cp = 0;
  if ( defined $colors2pair[$fg][$bg] ) {
    $cp = $colors2pair[$fg][$bg];
  } else {
    $cp = $next_color_pair;
    $colors2pair[$fg][$bg] = $next_color_pair;
    $next_color_pair++;
    if ( $fg == 999999 ) { $fg = -1; }
    if ( $bg == 999999 ) { $bg = -1; }
    init_pair($cp,$fg,$bg);
  }
  return $cp;
}

return 1;

