"""Sample functions for testing the unit test generator."""


def calculate_average(numbers):
    """Calculate the average of a list of numbers."""
    if not numbers:
        return 0
    return sum(numbers) / len(numbers)


def is_palindrome(text):
    """Check if a string is a palindrome."""
    cleaned = "".join(c.lower() for c in text if c.isalnum())
    return cleaned == cleaned[::-1]


def factorial(n):
    """Calculate factorial of a number."""
    if n < 0:
        raise ValueError("Factorial is not defined for negative numbers")
    if n == 0 or n == 1:
        return 1
    return n * factorial(n - 1)


def find_max(numbers):
    """Find the maximum number in a list."""
    if not numbers:
        raise ValueError("Cannot find max of empty list")
    max_num = numbers[0]
    for num in numbers:
        if num > max_num:
            max_num = num
    return max_num


class ShoppingCart:
    """A simple shopping cart."""

    def __init__(self):
        self.items = []

    def add_item(self, name, price, quantity=1):
        """Add an item to the cart."""
        if price < 0:
            raise ValueError("Price cannot be negative")
        if quantity < 1:
            raise ValueError("Quantity must be at least 1")

        self.items.append({"name": name, "price": price, "quantity": quantity})

    def get_total(self):
        """Calculate the total price of all items."""
        total = 0
        for item in self.items:
            total += item["price"] * item["quantity"]
        return total

    def apply_discount(self, percentage):
        """Apply a discount percentage to the total."""
        if not 0 <= percentage <= 100:
            raise ValueError("Discount percentage must be between 0 and 100")

        total = self.get_total()
        discount = total * (percentage / 100)
        return total - discount
