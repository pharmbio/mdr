#!/usr/bin/perl
use strict; use warnings;
use DBI; use v5.10;

# TODO: mlst name must be unique (via db or script)

my $xml = 'dbases.xml';
my $dbf = '../bacteria.sqlite';
my $dbh = DBI->connect("dbi:SQLite:dbname=$dbf",'','');

my $sql = 'select bid, genus || " " || species from bacteria';
my %bact = map { $$_[1] => $$_[0] } @{ $dbh->selectall_arrayref($sql) };

$dbh->do('delete from mlst2bid');
my $sth = $dbh->prepare('insert into mlst2bid values (?,?,?)');

my($spe, $mlst, @tfa);
open(my $fh, '<', $xml) or die;
while(<$fh>) {
    if (/^\<species\>(.*)/) {
	$spe = $1; $spe =~ s/^\s*|\s*$//g; $spe =~ s/\s*\#\d+$//;
	$mlst = ''; @tfa = ();
    } elsif (m#data/alleles/([^/]+)/([^./]+)\.tfa#) {
	die if $mlst && $mlst ne $1;
	$mlst = $1; push @tfa, $2;
    } elsif (/^\<\/species\>/) {
	# too much bother to stop early if $spe not in bact db
	my $tfa = join(',', @tfa);
        $sth->execute($bact{$spe}, $mlst, $tfa) if $bact{$spe};
	print "$bact{$spe}\t$mlst\t$tfa\n" if $bact{$spe};
    }
}
