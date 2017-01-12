#!/usr/bin/perl
#
# Extract genes from a fasta with one sequence using a locus file
# DNA assumed but could check and easily adjust for RNA
#
# Note: Seems wasteful to re-scan the fasta file for each gene but
#       it's quite fast and easier to deal with overlapping reading frames.
#       Better to read entire fasta file into memory or reopen for each gene?
#       I don't expect to use this on large fasta files so better to read once.

use warnings; use strict;

my $small = 1;
my $genome = '';
my $gi = '';

open(L,'<',shift) or die;
open(F,'<',shift) or die;

if($small) {
    $_ = <F>; die unless /^>/;
    $gi = $1 if /^gi|(\d+)/;
    local $/ = undef;
    $genome = <F>;
    $genome =~ s/\s//g;
    die('Check fasta') if $genome =~ y/ACGTN//c;
}

while(<L>) {
    next if (/^#/ || /^\s*$/);
    chomp;
    my ($start, $end, $dir, $gene) = split(" ", $_, 4);
    die("start='$start' for $gene") if $start =~ y/0123456789//c;
    die("end='$end' for $gene")     if $end =~ y/0123456789//c;
    die("dir='$dir' for $gene") unless $dir =~ /(?:fwd|rev)/;
    my $rev = $dir eq 'rev' ? 1 : 0;
    $gene =~ s/\s/_/g; 
    if($small) {
	print ">$gene|gi|$gi:";
	print 'c' if $rev;
	print "$start-$end\n";
	my $dna = substr($genome,$start-1,$end-$start+1);
	if($rev) { $dna = revcomp($dna); }
	$dna =~ s/(.{70})/$1\n/g;
	print "$dna\n";
    }
}
close L;


sub revcomp {
    my $rev = $_[0];
    $rev =~ y/ACGT/TGCA/;
    reverse $rev;
}
