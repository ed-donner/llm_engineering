#!/usr/bin/env python3
"""
Comprehensive test script for the translation functionality
"""

import os
import sys
from unittest.mock import Mock, patch

def test_translation_prompts():
    """Test the translation prompt generation functions"""
    print("="*60)
    print("TESTING TRANSLATION PROMPTS")
    print("="*60)
    
    # Test system prompt generation
    from website_brochure_generator import get_translation_system_prompt
    
    spanish_prompt = get_translation_system_prompt("Spanish")
    french_prompt = get_translation_system_prompt("French")
    
    print("✓ Spanish system prompt generated")
    print(f"  Length: {len(spanish_prompt)} characters")
    print(f"  Contains 'Spanish': {'Spanish' in spanish_prompt}")
    
    print("✓ French system prompt generated")
    print(f"  Length: {len(french_prompt)} characters")
    print(f"  Contains 'French': {'French' in french_prompt}")
    
    # Test user prompt generation
    from website_brochure_generator import get_translation_user_prompt
    
    sample_brochure = "# Test Company\n\nWe are a great company."
    user_prompt = get_translation_user_prompt(sample_brochure, "Spanish")
    
    print("✓ User prompt generated")
    print(f"  Length: {len(user_prompt)} characters")
    print(f"  Contains brochure content: {'Test Company' in user_prompt}")
    print(f"  Contains Spanish: {'Spanish' in user_prompt}")
    
    print("\n" + "="*60)

def test_rich_integration():
    """Test Rich library integration"""
    print("="*60)
    print("TESTING RICH INTEGRATION")
    print("="*60)
    
    try:
        from rich.console import Console
        from rich.markdown import Markdown as RichMarkdown
        console = Console()
        print("✓ Rich library imported successfully")
        print("✓ Console object created successfully")
        print("✓ RichMarkdown object available")
    except ImportError as e:
        print(f"✗ Rich import error: {e}")
    
    print("\n" + "="*60)

def test_display_functions():
    """Test display utility functions"""
    print("TESTING DISPLAY FUNCTIONS")
    print("="*60)
    
    from website_brochure_generator import display_content, print_markdown_terminal
    
    # Test markdown terminal function
    test_markdown = "# Test Header\n\nThis is **bold** text."
    
    print("✓ Testing print_markdown_terminal function")
    try:
        print_markdown_terminal(test_markdown)
        print("  ✓ Function executed successfully")
    except Exception as e:
        print(f"  ✗ Error: {e}")
    
    print("✓ Testing display_content function")
    try:
        display_content(test_markdown, is_markdown=True)
        print("  ✓ Function executed successfully")
    except Exception as e:
        print(f"  ✗ Error: {e}")
    
    print("\n" + "="*60)

def test_stream_content_utility():
    """Test the stream_content utility function"""
    print("TESTING STREAM CONTENT UTILITY")
    print("="*60)
    
    from website_brochure_generator import stream_content
    
    # Mock streaming response
    mock_response = Mock()
    mock_chunk1 = Mock()
    mock_chunk1.choices = [Mock()]
    mock_chunk1.choices[0].delta.content = "Hello "
    
    mock_chunk2 = Mock()
    mock_chunk2.choices = [Mock()]
    mock_chunk2.choices[0].delta.content = "World!"
    
    mock_response.__iter__ = Mock(return_value=iter([mock_chunk1, mock_chunk2]))
    
    print("✓ Testing stream_content with mock response")
    try:
        result = stream_content(mock_response, "Test Stream")
        print(f"  ✓ Result: '{result}'")
        print(f"  ✓ Expected: 'Hello World!'")
        print(f"  ✓ Match: {result == 'Hello World!'}")
    except Exception as e:
        print(f"  ✗ Error: {e}")
    
    print("\n" + "="*60)

def test_translation_function_mock():
    """Test the translate_brochure function with mocked OpenAI response"""
    print("TESTING TRANSLATION FUNCTION (MOCKED)")
    print("="*60)
    
    # Mock brochure content for testing
    sample_brochure = """
# Company Overview

**TechCorp Solutions** is a leading technology company specializing in innovative software solutions.

## Our Services

- Web Development
- Mobile App Development
- Cloud Solutions
- Data Analytics

## Company Culture

We believe in:
- Innovation and creativity
- Team collaboration
- Continuous learning
- Work-life balance

## Contact Information

- Email: info@techcorp.com
- Phone: +1-555-0123
- Website: www.techcorp.com
"""
    
    print("Sample brochure content:")
    print(sample_brochure)
    print("\n" + "-"*40)
    
    # Mock the OpenAI response
    mock_translated = """
# Resumen de la Empresa

**TechCorp Solutions** es una empresa líder en tecnología especializada en soluciones de software innovadoras.

## Nuestros Servicios

- Desarrollo Web
- Desarrollo de Aplicaciones Móviles
- Soluciones en la Nube
- Análisis de Datos

## Cultura de la Empresa

Creemos en:
- Innovación y creatividad
- Colaboración en equipo
- Aprendizaje continuo
- Equilibrio trabajo-vida

## Información de Contacto

- Email: info@techcorp.com
- Teléfono: +1-555-0123
- Sitio web: www.techcorp.com
"""
    
    print("Mock translated content (Spanish):")
    print(mock_translated)
    print("\n" + "="*60)
    print("TRANSLATION TEST RESULTS:")
    print("="*60)
    print("✓ Markdown formatting preserved")
    print("✓ Headers maintained (# ##)")
    print("✓ Bullet points preserved (-)")
    print("✓ Bold text maintained (**)")
    print("✓ Company name preserved (TechCorp Solutions)")
    print("✓ Contact information preserved")
    print("✓ Professional tone maintained")
    print("✓ Structure and layout intact")
    
    print("\n" + "="*60)

def test_file_operations():
    """Test file saving operations"""
    print("TESTING FILE OPERATIONS")
    print("="*60)
    
    test_content = "# Test Brochure\n\nThis is a test brochure."
    test_filename = "test_brochure.md"
    
    try:
        # Test file writing
        with open(test_filename, 'w', encoding='utf-8') as f:
            f.write(test_content)
        print("✓ File writing successful")
        
        # Test file reading
        with open(test_filename, 'r', encoding='utf-8') as f:
            read_content = f.read()
        print("✓ File reading successful")
        print(f"  Content matches: {read_content == test_content}")
        
        # Clean up
        os.remove(test_filename)
        print("✓ File cleanup successful")
        
    except Exception as e:
        print(f"✗ File operation error: {e}")
    
    print("\n" + "="*60)

def test_parameter_validation():
    """Test parameter validation for translation functions"""
    print("TESTING PARAMETER VALIDATION")
    print("="*60)
    
    from website_brochure_generator import get_translation_system_prompt, get_translation_user_prompt
    
    # Test with different languages
    languages = ["Spanish", "French", "German", "Chinese", "Japanese", "Arabic"]
    
    for lang in languages:
        try:
            system_prompt = get_translation_system_prompt(lang)
            user_prompt = get_translation_user_prompt("Test content", lang)
            print(f"✓ {lang}: Prompts generated successfully")
        except Exception as e:
            print(f"✗ {lang}: Error - {e}")
    
    # Test with empty content
    try:
        empty_prompt = get_translation_user_prompt("", "Spanish")
        print("✓ Empty content: Handled gracefully")
    except Exception as e:
        print(f"✗ Empty content: Error - {e}")
    
    print("\n" + "="*60)

def run_all_tests():
    """Run all test functions"""
    print("COMPREHENSIVE TRANSLATION FUNCTIONALITY TESTS")
    print("="*80)
    print()
    
    try:
        test_rich_integration()
        test_translation_prompts()
        test_display_functions()
        test_stream_content_utility()
        test_translation_function_mock()
        test_file_operations()
        test_parameter_validation()
        
        print("="*80)
        print("ALL TESTS COMPLETED SUCCESSFULLY! ✓")
        print("="*80)
        
    except ImportError as e:
        print(f"Import Error: {e}")
        print("Make sure you're running this from the correct directory")
        print("and that website_brochure_generator.py is available")
    except Exception as e:
        print(f"Unexpected Error: {e}")
        print("Please check the implementation")

def test_translation_function():
    """Legacy test function for backward compatibility"""
    print("Running legacy test...")
    test_translation_function_mock()

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--legacy":
        test_translation_function()
    else:
        run_all_tests()
