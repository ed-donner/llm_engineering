"""Test module for Rust language detection."""

import sys
import os

# Add the src directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from ai_code_converter.core.language_detection import LanguageDetector


def test_rust_detection():
    """Test the Rust language detection functionality."""
    detector = LanguageDetector()
    
    # Sample Rust code
    rust_code = """
use std::collections::HashMap;
use std::io::{self, Write};

// A struct in Rust
#[derive(Debug, Clone)]
pub struct Person {
    name: String,
    age: u32,
}

// Implementation block for Person
impl Person {
    // Constructor (associated function)
    pub fn new(name: String, age: u32) -> Self {
        Person { name, age }
    }
    
    // Method
    pub fn greet(&self) -> String {
        format!("Hello, my name is {} and I am {} years old.", self.name, self.age)
    }
    
    // Mutable method
    pub fn celebrate_birthday(&mut self) {
        self.age += 1;
        println!("Happy birthday! Now I am {} years old.", self.age);
    }
}

// A simple function with pattern matching
fn process_option(opt: Option<i32>) -> i32 {
    match opt {
        Some(value) => value,
        None => -1,
    }
}

// Main function with vector usage
fn main() {
    // Create a vector
    let mut numbers: Vec<i32> = vec![1, 2, 3, 4, 5];
    numbers.push(6);
    
    // Create a Person instance
    let mut person = Person::new(String::from("Alice"), 30);
    println!("{}", person.greet());
    person.celebrate_birthday();
    
    // Use a HashMap
    let mut scores = HashMap::new();
    scores.insert(String::from("Blue"), 10);
    scores.insert(String::from("Red"), 50);
    
    // Pattern matching with if let
    if let Some(score) = scores.get("Blue") {
        println!("Blue team score: {}", score);
    }
}
"""
    
    # Test the detection
    assert detector.detect_rust(rust_code) == True
    assert detector.detect_language(rust_code) == "Rust"
    
    # Check validation
    valid, _ = detector.validate_language(rust_code, "Rust")
    assert valid == True


if __name__ == "__main__":
    test_rust_detection()
    print("All Rust detection tests passed!")
