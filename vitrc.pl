# Copyright 2013, Scott Kostyshak

sub parse_vitrc {
  my $vitrc = glob("~/.vitrc");
  if ( open(IN,"<$vitrc") ) {
    while (<IN>) {
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

	my $rereadflag;
        my $waitflag;
        unless (GetOptionsFromString($scut,
          "reread|r" => \$rereadflag,
          "wait|w"   => \$waitflag)) {
            print STDERR "$parse_error";
            exit(1);
        }
        my $wait = 'no-wait';
        if ($waitflag) {
          $wait = 'wait';
        }
        my $expanded = eval "\"$skey\"";
        my @attributes = ($cmd, $wait, $rereadflag);
        $shortcuts{$expanded} = \@attributes;
      }
    }
    close(IN);
  }
}

return 1;

