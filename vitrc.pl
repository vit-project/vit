# Copyright 2013, Scott Kostyshak

sub parse_vitrc {
  my $vitrc = glob("~/.vitrc");
  if ( open(IN,"<$vitrc") ) {
    while (<IN>) {
      chop;
      my $parse_error = "ERROR: incorrect key bind line in .vitrc:\n  $_";
      if ( $_ =~ s/^map// ) {
        my($scut, $cmd) = split(/=/, $_, 2);

        my $skey;
        if ($scut =~ s/ ([^ ]+)$//) {
          $skey = $1;
        }
        else {
          print STDERR "$parse_error";
          exit(1);
        }

        $skey = eval "\"$skey\"";
        $cmd =~ s/<Return>/\n/g;

        $shortcuts{$skey} = $cmd;
      }
    }
    close(IN);
  }
}

return 1;

