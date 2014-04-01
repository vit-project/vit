# Copyright 2012 - 2013, Steve Rader
# Copyright 2013 - 2014, Scott Kostyshak

sub audit {
  if ( $audit ) {
    print AUDIT "$$ ";
    print AUDIT @_;
    print AUDIT "\r\n";
  }
}

#------------------------------------------------------------------

sub clean_exit {
  unless( $audit ) {
    &shell_exec("clear", 'no-wait');
  }
  if ( $audit ) {
      close(AUDIT) or die "$!";
  }

  endwin();
  exit();
}

#------------------------------------------------------------------

sub error_exit {
  unless( $audit ) {
    &shell_exec("clear", 'no-wait');
  }

  endwin();
  print STDERR "VIT fatal error: @_\r\n";

  if ( $audit ) {
      close(AUDIT) or die "$!";
  }

  exit(1);
}

#------------------------------------------------------------------

sub debug {
  print AUDIT @_;
  print AUDIT "\r\n";
}

#------------------------------------------------------------------

sub is_printable {
  my $char = $_[0];
  if ( $char =~ /^[0-9]+$/ && $char >= KEY_MIN ) {
    return 0;
  }
  if ( $char =~ /[[:cntrl:]]/ ) {
    return 0;
  }
  return 1;
}

#------------------------------------------------------------------

sub task_version {
  my $request = $_[0];
  my $version;
  open(IN,"task --version 2>&1 |");
  while(<IN>) {
    chop;
    $version = $_;
  }
  close(IN);
  if ( $request eq "major.minor" ) {
    my @v_ = split(/\./,$version);
    return "$v_[0].$v_[1]";
  }
  return $version;
}

#------------------------------------------------------------------

sub task_info {
  my $n = $_[0];
  my $id = $report2taskid[$task_selected_idx];
  &audit("EXEC $task $id info 2>&1");
  open(IN,"task $id info 2>&1 |");
  while(<IN>) {
    chop;
    $_ =~ s/\x1b.*?m//g; # decolorize
    if ( $_ =~ /^$n\s+(.*)/ ) {
      my $v = $1;
      $v =~ s/\s+$//;
      close(IN);
      return $v;
    }
  }
  close(IN);
  return '';
}

#------------------------------------------------------------------

sub ungetstr {
  my $str = $_[0];
  my $err;
  foreach my $ch (reverse split('', $str)) {
    $err = ungetch($ch);
    if ( $err != 0 ) {
      error_exit("Shortcut is too long.");
    }
  }
  return '';
}

return 1;
