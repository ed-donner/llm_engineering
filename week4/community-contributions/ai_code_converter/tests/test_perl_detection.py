"""Test module for Perl language detection."""

import sys
import os

# Add the src directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from ai_code_converter.core.language_detection import LanguageDetector


def test_perl_detection():
    """Test the Perl language detection functionality."""
    detector = LanguageDetector()
    
    # Sample Perl code
    perl_code = """
#!/usr/bin/perl
use strict;
use warnings;
use Data::Dumper;
use File::Basename;
use Getopt::Long;

# Scalar variable
my $name = "John Doe";
my $age = 30;
my $pi = 3.14159;

# Array variables
my @fruits = ("apple", "banana", "orange");
my @numbers = (1..10);

# Hash variables
my %user = (
    "name" => "John",
    "age" => 30,
    "email" => "john@example.com"
);

# Print statements
print "Hello, $name!\\n";
print "Your age is $age\\n";

# Accessing array elements
print "First fruit: $fruits[0]\\n";
print "Last fruit: $fruits[-1]\\n";

# Accessing hash elements
print "User name: $user{name}\\n";
print "User email: $user{email}\\n";

# Subroutine definition
sub greet {
    my ($person) = @_;
    print "Hello, $person!\\n";
    return "Greeting sent";
}

# Call the subroutine
my $result = greet($name);
print "Result: $result\\n";

# Control structures
if ($age >= 18) {
    print "You are an adult.\\n";
} else {
    print "You are a minor.\\n";
}

# Unless example
unless ($age < 18) {
    print "Not a minor.\\n";
}

# For loop
for my $i (0..$#fruits) {
    print "Fruit $i: $fruits[$i]\\n";
}

# Foreach loop
foreach my $fruit (@fruits) {
    print "I like $fruit\\n";
}

# While loop
my $counter = 0;
while ($counter < 5) {
    print "Counter: $counter\\n";
    $counter++;
}

# Regular expressions
my $text = "The quick brown fox";
if ($text =~ m/quick/) {
    print "Match found!\\n";
}

# Substitution
my $modified = $text;
$modified =~ s/quick/slow/;
print "Modified text: $modified\\n";

# Special variables
print "Script name: $0\\n";
print "Command line arguments: @ARGV\\n";
print "Current line: $. \\n";

# File operations
open(my $fh, '>', 'output.txt') or die "Cannot open file: $!";
print $fh "Hello, Perl!\\n";
close $fh;

# Reading from standard input
print "Enter your name: ";
my $input = <STDIN>;
chomp($input);  # Remove newline
print "Hello, $input!\\n";

# References
my $array_ref = \\@fruits;
print "First element via ref: ${$array_ref}[0]\\n";

my $hash_ref = \\%user;
print "Name via ref: ${$hash_ref}{name}\\n";

# Using references for functions
sub process_data {
    my ($data_ref) = @_;
    foreach my $key (keys %{$data_ref}) {
        print "Key: $key, Value: ${$data_ref}{$key}\\n";
    }
}

process_data(\\%user);

# Object-oriented style
package Person;

sub new {
    my ($class, $name, $age) = @_;
    return bless { name => $name, age => $age }, $class;
}

sub get_name {
    my ($self) = @_;
    return $self->{name};
}

sub get_age {
    my ($self) = @_;
    return $self->{age};
}

package main;
my $person = Person->new("Bob", 25);
print "Person name: " . $person->get_name() . "\\n";
print "Person age: " . $person->get_age() . "\\n";

exit 0;
"""
    
    # Test the detection
    assert detector.detect_perl(perl_code) == True
    assert detector.detect_language(perl_code) == "Perl"
    
    # Check validation
    valid, _ = detector.validate_language(perl_code, "Perl")
    assert valid == True


if __name__ == "__main__":
    test_perl_detection()
    print("All Perl detection tests passed!")
