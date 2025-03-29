"""Test module for C# language detection."""

import sys
import os

# Add the src directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from ai_code_converter.core.language_detection import LanguageDetector


def test_csharp_detection():
    """Test the C# language detection functionality."""
    detector = LanguageDetector()
    
    # Sample C# code
    csharp_code = """
using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;

namespace MyApp
{
    // A simple C# class
    public class Person
    {
        // Properties
        public string Name { get; set; }
        public int Age { get; private set; }
        
        // Constructor
        public Person(string name, int age)
        {
            Name = name;
            Age = age;
        }
        
        // Method
        public string Greet()
        {
            return $"Hello, my name is {Name} and I am {Age} years old.";
        }
        
        // Method with out parameter
        public bool TryParse(string input, out int result)
        {
            return int.TryParse(input, out result);
        }
    }
    
    // Interface
    public interface IRepository<T> where T : class
    {
        Task<T> GetByIdAsync(int id);
        Task<IEnumerable<T>> GetAllAsync();
        Task AddAsync(T entity);
    }
    
    // Async method
    public class DataProcessor
    {
        public async Task ProcessDataAsync()
        {
            await Task.Delay(1000);
            Console.WriteLine("Data processed!");
        }
    }
    
    class Program
    {
        static void Main(string[] args)
        {
            // Variable declaration with var
            var person = new Person("John", 30);
            Console.WriteLine(person.Greet());
            
            // LINQ query
            var numbers = new List<int> { 1, 2, 3, 4, 5 };
            var evenNumbers = numbers.Where(n => n % 2 == 0).ToList();
            
            // String interpolation
            string message = $"Found {evenNumbers.Count} even numbers.";
            Console.WriteLine(message);
        }
    }
}
"""
    
    # Test the detection
    assert detector.detect_csharp(csharp_code) == True
    assert detector.detect_language(csharp_code) == "C#"
    
    # Check validation
    valid, _ = detector.validate_language(csharp_code, "C#")
    assert valid == True


if __name__ == "__main__":
    test_csharp_detection()
    print("All C# detection tests passed!")
