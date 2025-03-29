"""Test module for Ruby language detection."""

import sys
import os

# Add the src directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from ai_code_converter.core.language_detection import LanguageDetector


def test_ruby_detection():
    """Test the Ruby language detection functionality."""
    detector = LanguageDetector()
    
    # Sample Ruby code
    ruby_code = """
# A simple Ruby class
class Person
  attr_accessor :name, :age
  
  def initialize(name, age)
    @name = name
    @age = age
  end
  
  def greet
    puts "Hello, my name is #{@name} and I am #{@age} years old."
  end
end

# Create a new Person
person = Person.new("John", 30)
person.greet

# Hash examples
old_syntax = { :name => "Ruby", :created_by => "Yukihiro Matsumoto" }
new_syntax = { name: "Ruby", created_by: "Yukihiro Matsumoto" }

# Block with parameters
[1, 2, 3].each do |num|
  puts num * 2
end
"""
    
    # Test the detection
    assert detector.detect_ruby(ruby_code) == True
    assert detector.detect_language(ruby_code) == "Ruby"
    
    # Check validation
    valid, _ = detector.validate_language(ruby_code, "Ruby")
    assert valid == True


if __name__ == "__main__":
    test_ruby_detection()
    print("All Ruby detection tests passed!")
