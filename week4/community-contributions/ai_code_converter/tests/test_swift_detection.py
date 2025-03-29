"""Test module for Swift language detection."""

import sys
import os

# Add the src directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from ai_code_converter.core.language_detection import LanguageDetector


def test_swift_detection():
    """Test the Swift language detection functionality."""
    detector = LanguageDetector()
    
    # Sample Swift code
    swift_code = """
import Foundation
import UIKit

// A simple Swift class
class Person {
    var name: String
    var age: Int
    
    init(name: String, age: Int) {
        self.name = name
        self.age = age
    }
    
    func greet() -> String {
        return "Hello, my name is \(name) and I am \(age) years old."
    }
    
    func celebrateBirthday() {
        age += 1
        print("Happy birthday! Now I am \(age) years old.")
    }
}

// Swift structs
struct Point {
    let x: Double
    let y: Double
    
    func distanceTo(point: Point) -> Double {
        return sqrt(pow(point.x - x, 2) + pow(point.y - y, 2))
    }
}

// Swift optional binding
func processName(name: String?) {
    if let unwrappedName = name {
        print("Hello, \(unwrappedName)!")
    } else {
        print("Hello, anonymous!")
    }
}

// Guard statement
func process(value: Int?) {
    guard let value = value else {
        print("Value is nil")
        return
    }
    
    print("Value is \(value)")
}

// UIKit elements
class MyViewController: UIViewController {
    @IBOutlet weak var nameLabel: UILabel!
    
    @IBAction func buttonPressed(_ sender: UIButton) {
        nameLabel.text = "Button was pressed!"
    }
    
    override func viewDidLoad() {
        super.viewDidLoad()
        // Do additional setup
    }
}
"""
    
    # Test the detection
    assert detector.detect_swift(swift_code) == True
    assert detector.detect_language(swift_code) == "Swift"
    
    # Check validation
    valid, _ = detector.validate_language(swift_code, "Swift")
    assert valid == True


if __name__ == "__main__":
    test_swift_detection()
    print("All Swift detection tests passed!")
