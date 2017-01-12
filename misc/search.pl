#!/usr/bin/perl
use strict; use warnings; use v5.10;

my $target = shift;

my $dir = '../../data';
my $db  = "-db $dir/results/prep";
my $qry = "-query query/selected-$target.fa";
my $out = "-out $target";
my $fmt = '-outfmt "6 qacc pident qlen length mismatch gaps evalue bitscore"';
my $all = "blastn -ungapped $qry";
my $one = "$all -outfmt 1";
my $sum = "$all $fmt -max_target_seqs 1";

for my $vic (1, 3..7) {
    my $seq = "ugit_95_$vic";
    system("$all $db/$seq/$seq $out/$seq.out");
    system("$one $db/$seq/$seq $out/$seq.one");
    system("$sum $db/$seq/$seq $out/$seq.tab");
}
