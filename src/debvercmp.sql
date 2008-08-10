CREATE OR REPLACE FUNCTION debvercmp(v1 text, v2 text) RETURNS text AS $$
   sub parseversion
   {
       my $ver = shift;
       my %verhash;
       if ($ver =~ /:/)
       {
      $ver =~ /^(\d+):(.+)/ or die "bad version number '$ver'";
      $verhash{epoch} = $1;
      $ver = $2;
       }
       else
       {
      $verhash{epoch} = 0;
       }
       if ($ver =~ /(.+)-(.+)$/)
       {
      $verhash{version} = $1;
      $verhash{revision} = $2;
       }
       else
       {
      $verhash{version} = $ver;
      $verhash{revision} = 0;
       }
       return %verhash;
   }

   sub verrevcmp
   {

        sub order{
        my ($x) = @_;
        ##define order(x) ((x) == '~' ? -1 \
        #           : cisdigit((x)) ? 0 \
        #           : !(x) ? 0 \
        #           : cisalpha((x)) ? (x) \
        #           : (x) + 256)
        # This comparison is out of dpkg's order to avoid
        # comparing things to undef and triggering warnings.
        if (not defined $x) {
             return 0;
        }
        elsif ($x eq '~') {
             return -1;
        }
        elsif ($x =~ /^\d$/) {
             return 0;
        }
        elsif ($x =~ /^[A-Z]$/i) {
             return ord($x);
        }
        else {
             return ord($x) + 256;
        }
        }

        sub next_elem(\@){
        my $a = shift;
        return @{$a} ? shift @{$a} : undef;
        }
        my ($val, $ref) = @_;
        $val = "" if not defined $val;
        $ref = "" if not defined $ref;
        my @val = split //,$val;
        my @ref = split //,$ref;
        my $vc = next_elem @val;
        my $rc = next_elem @ref;
        while (defined $vc or defined $rc) {
        my $first_diff = 0;
        while ((defined $vc and $vc !~ /^\d$/) or
          (defined $rc and $rc !~ /^\d$/)) {
             my $vo = order($vc); my $ro = order($rc);
             # Unlike dpkg's verrevcmp, we only return 1 or -1 here.
             return (($vo - $ro > 0) ? 1 : -1) if $vo != $ro;
             $vc = next_elem @val; $rc = next_elem @ref;
        }
        while (defined $vc and $vc eq '0') {
             $vc = next_elem @val;
        }
        while (defined $rc and $rc eq '0') {
             $rc = next_elem @ref;
        }
        while (defined $vc and $vc =~ /^\d$/ and
          defined $rc and $rc =~ /^\d$/) {
             $first_diff = ord($vc) - ord($rc) if !$first_diff;
             $vc = next_elem @val; $rc = next_elem @ref;
        }
        return 1 if defined $vc and $vc =~ /^\d$/;
        return -1 if defined $rc and $rc =~ /^\d$/;
        return $first_diff if $first_diff;
        }
        return 0;
   }
    my %version = parseversion $_[0];
    my %refversion = parseversion $_[1];
    return 1 if $version{epoch} > $refversion{epoch};
    return -1 if $version{epoch} < $refversion{epoch};
    my $r = verrevcmp($version{version}, $refversion{version});
    return $r if $r;
    return verrevcmp($version{revision}, $refversion{revision});
$$ LANGUAGE plperl;

