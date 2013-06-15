
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
