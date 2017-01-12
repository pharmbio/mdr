#!/usr/bin/perl
#
# Show differences between default blast searches against a common query seq
# Kludge: too lazy to deal with file I/O so just reading into arrays
# TODO: fix the tag lengths for better alignment (good enough for now)

use strict; use warnings; use v5.10;
my (@f1,@f2);
my @files = map { /([^.]+)/ } @ARGV;
my $gene= ''; my $l2 = '';

{ local $/ = 'Query= '; 
  open(F1, '<', $ARGV[0]) or die; @f1 = <F1>; close F1;
  open(F2, '<', $ARGV[1]) or die; @f2 = <F2>; close F2;
}

# print scalar(@f1), "\t", scalar(@f2), "\n";
# shift @f1;  shift @f2;
 
for my $i (1 .. @f1-1) {
    $gene = $1 if $f1[$i] =~ /^([^\|\ ]+)/; die unless $gene;
    my @r1 = split(/Query_/,$f1[$i]);
    my @r2 = split(/Query_/,$f2[$i]);
    for my $j (1 .. @r1-1) {
	# $run =~ /(\d+\s+)(\d+\s+)(.+)/;
	# my ($indent, $off, $loc, $dat) = (length($1), length($2), $2, $3);
	# printf "%-11s %-12s %-10s %-6s%s\n", $files[0], $gene, 'Query', $loc, $dat;
	$r1[$j] =~ s/Lambda.+//ms;
	$r2[$j] =~ s/Lambda.+//ms;
	$r1[$j] =~ s/^\s*[\r\n]+//ms;
	$r2[$j] =~ s/^[^\n\r]+[\r\n]+//;
	substr($r1[$j], 0, 6) = sprintf "%-12s", $gene;
	print "$r1[$j]" if $r1[$j];
	print "$r2[$j]" if $r2[$j];
	#print "#####\n";
    }
}
