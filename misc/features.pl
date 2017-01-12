#!/usr/bin/perl
#
# Extract gene from text of a genbank page
# TODO: maybe extend to scraping webpage

use warnings; use strict;
while(<>) {
    next unless /^FEATURES/ .. /^ORIGIN/;
    if(/^\s+gene\s+/) {
	my ($start, $end) = /(\d+)\.\.(\d+)/;
	my $dir = /comp/i ? 'rev' : 'fwd';
	$_ = <>; chomp;
	print "$start\t$end\t$dir\t$1\n" 
	    if m#^\s+/gene=\"(.+)\"\s*$# && $start && $end;
    }
}
