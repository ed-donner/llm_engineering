from examples.example import Rectangle, add, greet
import pytest


def test_greet_regular_name():
    assert greet("Alice") == "Hello, Alice!"


def test_greet_empty_string():
    assert greet("") == "Hello, !"


def test_greet_non_string_input():
    # Objects are converted to string via f-string
    class Dummy:
        def __str__(self):
            return "DummyObject"

    assert greet(Dummy()) == "Hello, DummyObject!"


def test_add_integers():
    assert add(2, 3) == 5


def test_add_floats():
    assert add(2.5, 4.0) == 6.5


def test_add_negative_numbers():
    assert add(-2, 5) == 3


def test_add_zero():
    assert add(0, 10) == 10


def test_rectangle_initialization():
    rect = Rectangle(3.0, 4.0)
    assert rect.width == 3.0
    assert rect.height == 4.0


def test_rectangle_area_integer_dimensions():
    rect = Rectangle(5, 2)
    assert rect.area() == 10


def test_rectangle_area_float_dimensions():
    rect = Rectangle(2.5, 4.0)
    assert rect.area() == 10.0


def test_rectangle_area_zero_dimensions():
    rect = Rectangle(0, 5)
    assert rect.area() == 0