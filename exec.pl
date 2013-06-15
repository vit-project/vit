
sub shell_exec {
  endwin();
  print "$_[0]\r\n";
  if ( ! fork() ) {
    &audit("EXEC @_");
    exec(@_);
    exit();
  }
  wait();
  &init_curses('refresh');
  &draw_screen();
}

return 1;

