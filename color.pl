
sub parse_report_line {
  my ($l,$str) = @_;
  &parse_line($l,$str);
  push @{ $report_tokens[$l] }, (@parsed_tokens);
  push @{ $report_colors_fg[$l] },  (@parsed_colors_fg);
  push @{ $report_colors_bg[$l] }, (@parsed_colors_bg);
  push @{ $report_attrs[$l] }, (@parsed_attrs);
}

#------------------------------------------------------------------

sub parse_line {
  my ($l,$str) = @_;
  my $fg = 999999;
  my $bg = 999999;
  my $attr = 'none';
  @parsed_tokens = ();
  @parsed_colors_fg = ();
  @parsed_colors_bg = ();
  @parsed_attrs = ();
  #debug("IN line=$l str=\"$str\"");
  my @toks = split(/\x1B/,$str);
  my $t = 0;
  for my $tok (@toks) {
    if ( $tok eq '' ) { next; }
    #debug("TOK \"$tok\"");
    CASE: {
      # 16 (ANSI) color/attr pairs...
      if ( $tok =~ s/\[(\d+);(\d+)m// ) { 
        my ($a,$b) = ($1,$2); 
        if ( $a > 30 ) {
          $fg = $a - 30;
          $bg = $b - 40;
        } else {
          if ( $a eq '1' ) { $attr = 'bold'; }
          if ( $a eq '4' ) { $attr = 'underline'; }
          # WARNING: 7 is inverse but not parsed
          # WARNING: 2,3,5-29 are not parsed without warning!
          if ( $b < 38 ) { 
            $fg = $b - 30;
          } else {
            $bg = $b - 40;
          }
        } 
        last CASE;
      }
      # 16 (ANSI) color single colors or single attrs or attrs off...
      if ( $tok =~ s/\[(\d+)m// ) {
        my $a = $1; 
        if ( $a eq '0' ) {
          $fg = $bg = 999999;
          $attr = 'none';
        } elsif ( $a eq '1' ) {
          $attr = 'bold' # not reached!
        } elsif ( $a eq '4' ) {
          $attr = 'underline';
        } elsif ( $a < 38 ) {
          # WARNING: 2,3,5-29 are not parsed without warning!
          $fg = $a - 30;
          $bg = 999999;
        } elsif ( $a > 99 ) {
          $attr = 'standout'; # aka "bright" in taskwarrior
          $bg = $a - 100;
          $fg = 999999;
        } else {
          $bg = $a - 40;
          $fg = 999999;
        }
        last CASE;
      }
      # bold 16 (ANSI) color...
      if ( $tok =~ s/\[1;(\d+);(\d+)m// ) { 
        my ($a,$b) = ($1,$2); 
        $attr = 'bold'; 
        $fg = $a - 30;  
        $bg = $b - 40;  
        last CASE;
      }
      # underline 16 (ANSI) color...
      if ( $tok =~ s/\[4;(\d+);(\d+)m// ) { 
        my ($a,$b) = ($1,$2); 
        $attr = 'bold'; 
        $fg = $a - 30;  
        $bg = $b - 40;  
        last CASE;
      }
      # 256 (xterm) color foreground...
      if ( $tok =~ s/\[38;5;(\d+)m// ) { 
        $fg = $1; 
        last CASE;
      }
      # 256 (xterm) color background...
      if ( $tok =~ s/\[48;5;(\d+)m// ) { 
        $bg = $1; 
        last CASE;
      } 
    }
    if ( $tok ne '' ) { 
      $parsed_tokens[$t] = $tok;
      $parsed_colors_fg[$t] = $fg;
      $parsed_colors_bg[$t] = $bg;
      $parsed_attrs[$t] = $attr;
      #if ( $t == 0 ) { debug("PARSE tok=$l.$t cp=$fg,$bg \"$tok\""); }
      $t++;
    }
  }
}

return 1;

