# Copyright 2012 - 2013, Steve Rader
# Copyright 2013, Scott Kostyshak

sub audit {
  if ( $audit ) {
    print STDERR "$$ ";
    print STDERR @_;
    print STDERR "\r\n";
  }
}

#------------------------------------------------------------------

sub debug {
  print STDERR @_;
  print STDERR "\r\n";
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

return 1;
