
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

return 1;
