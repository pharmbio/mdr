#!/usr/bin/env perl
use strict; use warnings;

my $DSET = shift;
my $DATA = "../data";
my $IDIR = "$DATA/input/$DSET/assembly";
my $ODIR = "$DATA/results/prep";
my $cmd  = "makeblastdb -hash_index -parse_seqids -dbtype nucl -in";

opendir(my $dh, $IDIR) || die "can't open '$IDIR': $!";
# process fasta.gz ?
my @seq = grep { /\.fasta$/ && -f "$IDIR/$_" } readdir($dh);
# print join("\n",@seq),"\n";

for my $seq (@seq) {
    my ($nam) = $seq =~ /(${DSET}[_-]\d+)/;
    die("Unexpected name '$seq'") unless $nam;
    print "$nam\t";
    if (-e "$ODIR/$nam") {
	print "skipping\n";
    } else {
	mkdir "$ODIR/$nam" or die "Can't create '$ODIR/$nam'";
	system("$cmd $IDIR/$seq -title $nam -out $ODIR/$nam/$nam");
	print "\n";
    }
}
