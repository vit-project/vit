# Copyright 2012 - 2013, Steve Rader
# Copyright 2013 - 2016, Scott Kostyshak

sub task_exec {
  my ($cmd) = @_;
  my $es = 0;
  my $result = '';
  &audit("TASK EXEC $task $cmd 2>&1");
  open(IN,"echo -e \"yes\\n\" | $task $cmd 2>&1 |");
  while(<IN>) {
    chop;
    $_ =~ s/\x1b.*?m//g; # decolorize
    if ( $_ =~ /^\w+ override:/ ) { next; }
    $result .= "$_ ";
  }
  close(IN);
  if ( $! ) {
    $es = 1;
    &audit("FAILED \"$task $cmd\" error closing short pipe");
  }
  if ( $? != 0 ) {
    $es = $?;
    &audit("FAILED \"$task $cmd\" returned exit status $?");
  }
  return ($es,$result);
}

#------------------------------------------------------------------

sub exited_successfully {
  my $status = shift || 0;
  return 1  if  WIFEXITED($status) and WEXITSTATUS($status)==0;
  return undef;
}

sub shell_exec {
  my ($cmd,$mode) = @_;
  endwin();
  if ( $clear ne 'NOT_FOUND' ) { system("$clear"); }
  if ( $audit ) {
    print "$_[0]\r\n";
  }
  if ( ! fork() ) {
    &audit("EXEC $cmd");
    exec($cmd);
    exit();
  }
  wait();
  my $success = &exited_successfully($?);
  # two reasons to wait:
  # - an error occurred
  # - $mode is wait and the user didn't specify nowait in config file
  if ( not $success or ( $mode eq 'wait' and not $nowait ) ) {
    if (not $success) {
      print "Error while executing command `$cmd'\n";
    }
    print "Press return to continue.\r\n";
    <STDIN>;
  }
  &init_curses('refresh');
  &draw_screen();
}

return 1;

