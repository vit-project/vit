
sub prompt_y {
  my ($prompt) = @_;
  my $ans = 0;
  my $ch;
  echo();
  curs_set(1);
  &draw_prompt($prompt);
  $ch = $prompt_win->getch();
  if ( $ch eq "y" || $ch eq "Y" ) { $ans = 1; }
  noecho();
  curs_set(0);
  return $ans;
}

#------------------------------------------------------------------

sub prompt_str {
  my ($prompt) = @_;
  my ($ch,$str);
  echo();
  curs_set(1);
  &draw_prompt($prompt);
  while (1) {
    $ch = $prompt_win->getch();
    if ( $ch eq "\ch" ) {
      chop $str;
      &draw_prompt("$prompt$str");
      next; 
    }
    if ( $ch eq "\cu" ) {
      $str = '';
      &draw_prompt("$prompt$str");
      next; 
    }
    if ( $ch eq "\e" ) {
      noecho();
      curs_set(0);
      return '';
    }
    if ( $ch eq "\n" ) {
      last;
    }
    $str .= $ch;
  }
  noecho();
  curs_set(0);
  if ( $str eq '' ) { beep(); }  
  return $str;
} 

return 1;
