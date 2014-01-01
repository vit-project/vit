# Copyright 2012 - 2013, Steve Rader
# Copyright 2013 - 2014, Scott Kostyshak

sub parse_report_line {
  my ($l,$str) = @_;
  &parse_line($l,$str);
  if ( $current_command eq 'summary' && $parsed_tokens[0] =~ /^(\d+) project/ ) {
    $num_projects = $1;
    return;
  }
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
  my $attr = '';
  @parsed_tokens = ();
  @parsed_colors_fg = ();
  @parsed_colors_bg = ();
  @parsed_attrs = ();
  my @toks = split(/\x1B/,$str);
  my $t = 0;
  #debug("PARSE IN $str");
  for my $tok (@toks) {
    if ( $tok eq '' ) { next; }
    $attr = '';
    CASE: {
      # ANSI 16 color attr pairs...
      if ( $tok =~ s/\[(\d+);(\d+)m// ) {
        my ($a,$b) = ($1,$2);
        if ( $a > 30 ) {
          $fg = $a - 30;
          $bg = $b - 40;
        } else {
          if ( $a eq '1' ) { $attr .= 'bold '; }
          if ( $b eq '4' ) { $attr .= 'underline' ; }
          if ( $a eq '7' ) { $attr .= 'inverse '; }
          if ( $b < 38 ) {
            $fg = $b - 30;
          } else {
            $bg = $b - 40;
          }
        }
        last CASE;
      }
      # ANSI 16 color single colors or single attrs or attrs off...
      if ( $tok =~ s/\[(\d+)m// ) {
        my $a = $1;
        if ( $a eq '0' ) {
          $fg = $bg = 999999;
          $attr .= 'none ';
        } elsif ( $a eq '1' ) {
          $attr .= 'bold ';
        } elsif ( $a eq '4' ) {
          $attr .= 'underline ';
        } elsif ( $a < 38 ) {
          $fg = $a - 30;
          $bg = 999999;
        } elsif ( $a > 99 ) {
          $attr .= 'standout '; # "bright" in taskwarrior
          $bg = $a - 100;
          $fg = 999999;
        } else {
          $bg = $a - 40;
          $fg = 999999;
        }
        last CASE;
      }
      # ANSI 16 color bold...
      if ( $tok =~ s/\[1;(\d+);(\d+)m// ) {
        my ($a,$b) = ($1,$2);
        $attr .= 'bold ';
        $fg = $a - 30;
        $bg = $b - 40;
        last CASE;
      }
      # ANSI 16 color underline...
      if ( $tok =~ s/\[4;(\d+);(\d+)m// ) {
        my ($a,$b) = ($1,$2);
        $attr .= 'underline ';
        $fg = $a - 30;
        $bg = $b - 40;
        last CASE;
      }
      # ANSI 16 color inverse...
      if ( $tok =~ s/\[7;(\d+);(\d+)m// ) {
        my ($a,$b) = ($1,$2);
        $attr .= 'inverse ';
        $fg = $a - 30;
        $bg = $b - 40;
        last CASE;
      }
      # 256 color xterm foreground...
      if ( $tok =~ s/\[38;5;(\d+)m// ) {
        $fg = $1;
        last CASE;
      }
      # 256 color xterm background...
      if ( $tok =~ s/\[48;5;(\d+)m// ) {
        $bg = $1;
        last CASE;
      }
    }
    # FIXME summary mode...
    # if ( $tok =~ /0%\s+100%/ ) { debug("summary graph tok=\"$tok\" column=$t"); }
    if ( $tok ne '' ) {
      $parsed_tokens[$t] = $tok;
      $parsed_colors_fg[$t] = $fg;
      $parsed_colors_bg[$t] = $bg;
      if ( $attr eq '' ) { $attr = 'none'; }
      $parsed_attrs[$t] = $attr;
      #if ( $t == 0 ) { debug("PARSE OUT tok=\"$tok\" pos=$l.$t cp=$fg,$bg attr=$attr"); }
      $t++;
    }
  }
}

#------------------------------------------------------------------

sub extract_color {
  my ($s,$t) = @_;
  $parsed_colors_fg[1] = -1;
  $parsed_colors_bg[1] = -1;
  $parsed_attrs[1] = '';
  &audit("EXEC $task rc._forcecolor=on color $s 2>&1");
  open(IN2,"$task rc._forcecolor=on color $s 2>&1 |");
  while(<IN2>){
    if ( $_ =~ /Your sample:/ ) {
      $_ = <IN2>; $_ = <IN2>;
      &parse_line(0,$_);
      if ( $parsed_colors_fg[1] eq '999999' ) { $parsed_colors_fg[1] = -1; }
      if ( $parsed_colors_bg[1] eq '999999' ) { $parsed_colors_bg[1] = -1; }
    }
  }
  close(IN2);
}

#------------------------------------------------------------------

return 1;

