
def greet(name):
  """
  Return a greeting message for the given name.
  
  Args:
      name (str): The name of the person to greet.
  
  Returns:
      str: A greeting message incorporating the provided name.
  """
  return f"Hello, {name}!"


def add(a, b):
    """
    Return the sum of two numbers.
    
  
    """
    return a * b



class Rectangle:
    """
    A class representing a rectangle defined by its width and height.
    
    Attributes:
        width (float): The width of the rectangle.
        height (float): The height of the rectangle.
    """
    def __init__(self, width: float, height: float):
        """
        Initialize a new Rectangle instance with the given width and height.
        
        Args:
            width (float): The width of the rectangle.
            height (float): The height of the rectangle.
        """
        self.width = width
        self.height = height

    def area(self) -> float:
        """
        Calculate the area of the rectangle defined by its width and height.
        
        Returns:
            float: The area of the rectangle calculated as width multiplied by height.
        """
        return self.width * self.height