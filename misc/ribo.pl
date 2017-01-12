#!/usr/bin/env perl
# 
use strict; use warnings;

my (@base, @codon, @aa, %trans);
@base = qw (T C A G);
@aa   = qw (F F L L S S S S Y Y X X C C X W 
            L L L L P P P P H H Q Q R R R R
            I I I M T T T T N N K K S S R R
            V V V V A A A A D D E E G G G G);

for my $i (@base) { for my $j (@base) { for my $k (@base) { push @codon, "$i$j$k"; } } }
@trans{@codon} = @aa;


my $seq;
while(<>) {
    next if /^#/; next if /^\s*$/;
    if (/^>/) {
	print ribo($seq),"\n" if $seq;
	print; $seq = '';
    } else {
	chomp;
	$seq .= $_;
    }
}
print ribo($seq),"\n" if $seq;


sub ribo {
    my $s = uc $_[0];
    my $e = length($s) % 3;
    $s = substr($s,0,-$e) if $e;
    $s =~ s/(...)/$trans{$1}/g;
    $s =~s/X.*//;
    $s =~ s/(.{70})/$1\n/g;
    return $s;
}

