#!/usr/bin/perl
# Perl Test File
use strict;
use warnings;

my %employee = (
    name => "Max Mustermann",
    age => 35,
    department => "Entwicklung"
);

sub print_employee {
    my (\) = @_;
    print "Name: \->{name}\n";
    print "Alter: \->{age}\n";
    print "Abteilung: \->{department}\n";
}

print_employee(\%employee);
