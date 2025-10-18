from typing import Optional, Dict, Any, List
from transformers import AutoTokenizer
import re
from dataclasses import dataclass, field

# =============================================================================
# CONFIGURATION CONSTANTS
# =============================================================================

# The base language model used for tokenization
BASE_MODEL = "meta-llama/Meta-Llama-3.1-8B"

# Token limits: We want product descriptions between 150-160 tokens
# This ensures enough context without exceeding model limits
MIN_TOKENS = 150  # Minimum tokens for useful content
MAX_TOKENS = 160  # Maximum tokens before truncation

# Character limits: Pre-filter by character count before expensive tokenization
MIN_CHARS = 300  # Minimum characters to consider an item
CEILING_CHARS = MAX_TOKENS * 7  # Approximate max chars (7 chars per token avg)

# The maximum length a word can be while containing digits
# Longer words with digits are likely product codes/IDs
MAX_WORD_LENGTH_WITH_DIGITS = 7


# =============================================================================
# ITEM CLASS
# =============================================================================

@dataclass
class Item:
    """
    A cleaned, curated datapoint representing a Product with its Price.
    
    This class processes raw product data into a format suitable for training
    a language model to predict prices from product descriptions.
    
    Attributes:
        title (str): The product title/name
        price (float): The product price in dollars
        category (str): The product category (optional)
        token_count (int): Number of tokens in the final prompt
        details (Optional[str]): Raw product details string
        prompt (Optional[str]): The formatted training prompt
        include (bool): Whether this item passes quality filters
    """
    
    # Instance attributes with defaults
    title: str
    price: float
    category: str = ""
    token_count: int = 0
    details: Optional[str] = None
    prompt: Optional[str] = None
    include: bool = False
    
    # Class-level shared tokenizer (loaded once for all instances)
    _tokenizer: Optional[AutoTokenizer] = field(default=None, init=False, repr=False)
    
    # Prompt template components
    PREFIX = "Price is $"
    QUESTION = "How much does this cost to the nearest dollar?"
    
    # Text patterns to remove during cleaning
    REMOVALS = [
        '"Batteries Included?": "No"',
        '"Batteries Included?": "Yes"',
        '"Batteries Required?": "No"',
        '"Batteries Required?": "Yes"',
        "By Manufacturer",
        "Item",
        "Date First",
        "Package",
        ":",
        "Number of",
        "Best Sellers",
        "Number",
        "Product "
    ]
    
    def __post_init__(self):
        """
        Initialize the tokenizer on first use (lazy loading).
        This is called automatically after __init__.
        """
        if Item._tokenizer is None:
            try:
                Item._tokenizer = AutoTokenizer.from_pretrained(
                    BASE_MODEL, 
                    trust_remote_code=True
                )
            except Exception as e:
                raise RuntimeError(
                    f"Failed to load tokenizer for {BASE_MODEL}: {e}"
                )
    
    @classmethod
    def from_data(cls, data: Dict[str, Any], price: float) -> 'Item':
        """
        Factory method to create an Item from raw product data.
        
        Args:
            data: Dictionary containing product information with keys:
                  - title: Product name
                  - description: List of description strings
                  - features: List of feature strings
                  - details: Additional product details
            price: The product price in dollars
        
        Returns:
            Item: A processed Item instance
        """
        # Validate required fields
        if not data.get('title'):
            raise ValueError("Product data must include a 'title' field")
        if price <= 0:
            raise ValueError(f"Price must be positive, got: {price}")
        
        # Create the item instance
        item = cls(title=data['title'], price=price)
        
        # Parse and process the data
        item._parse_data(data)
        
        return item
    
    def _scrub_details(self) -> str:
        """
        Clean the details string by removing common boilerplate text.
        
        This removes low-value text patterns like battery information,
        generic labels, and other noise that doesn't help predict price.
        
        Returns:
            str: Cleaned details string
        """
        if not self.details:
            return ""
        
        # Start with the original details
        cleaned = self.details
        
        # Remove each pattern in our removal list
        for pattern in self.REMOVALS:
            cleaned = cleaned.replace(pattern, "")
        
        return cleaned
    
    def _scrub_text(self, text: str) -> str:
        """
        Clean text by removing unnecessary characters and irrelevant tokens.
        
        This function:
        1. Removes special characters and extra whitespace
        2. Normalizes punctuation
        3. Filters out likely product codes (long words with numbers)
        
        Args:
            text: Raw text to clean
        
        Returns:
            str: Cleaned and normalized text
        """
        # Replace special characters and multiple spaces with single space
        # Pattern matches: colons, brackets, quotes, Chinese characters, whitespace
        cleaned = re.sub(r'[:\[\]"{}ã€ã€'\s]+', ' ', text).strip()
        
        # Fix comma spacing and remove excessive commas
        cleaned = cleaned.replace(" ,", ",")  # Remove space before comma
        cleaned = cleaned.replace(",,,", ",")  # Reduce triple commas
        cleaned = cleaned.replace(",,", ",")   # Reduce double commas
        
        # Split into individual words for filtering
        words = cleaned.split(' ')
        
        # Keep only words that are either:
        # - Short (< 7 chars), OR
        # - Don't contain any digits
        # This filters out product codes like "B07XYZ1234"
        filtered_words = [
            word for word in words 
            if len(word) < MAX_WORD_LENGTH_WITH_DIGITS 
            or not any(char.isdigit() for char in word)
        ]
        
        # Rejoin the filtered words
        return " ".join(filtered_words)
    
    def _parse_data(self, data: Dict[str, Any]) -> None:
        """
        Parse raw product data and create a training prompt if quality criteria are met.
        
        This method:
        1. Combines description, features, and details into one text
        2. Checks if content meets minimum length requirements
        3. Tokenizes and truncates to fit within token limits
        4. Creates the final training prompt
        5. Sets self.include=True if the item passes all filters
        
        Args:
            data: Dictionary with product information
        """
        # Step 1: Gather all content from different fields
        content_parts: List[str] = []
        
        # Add description lines if present
        if 'description' in data and data['description']:
            description_text = '\n'.join(data['description'])
            if description_text:
                content_parts.append(description_text)
        
        # Add feature lines if present
        if 'features' in data and data['features']:
            features_text = '\n'.join(data['features'])
            if features_text:
                content_parts.append(features_text)
        
        # Add cleaned details if present
        self.details = data.get('details')
        if self.details:
            cleaned_details = self._scrub_details()
            if cleaned_details:
                content_parts.append(cleaned_details)
        
        # Combine all content with newlines
        combined_content = '\n'.join(content_parts)
        
        # Step 2: Check if we have enough content (quick character-based filter)
        if len(combined_content) < MIN_CHARS:
            # Not enough content, mark as excluded
            self.include = False
            return
        
        # Step 3: Truncate to reasonable length before tokenization
        # (Tokenization is expensive, so we pre-truncate)
        if len(combined_content) > CEILING_CHARS:
            combined_content = combined_content[:CEILING_CHARS]
        
        # Step 4: Clean both title and content
        cleaned_title = self._scrub_text(self.title)
        cleaned_content = self._scrub_text(combined_content)
        
        # Combine title and content with newline separator
        full_text = f"{cleaned_title}\n{cleaned_content}"
        
        # Step 5: Tokenize the text (convert to model's internal representation)
        try:
            tokens = self._tokenizer.encode(full_text, add_special_tokens=False)
        except Exception as e:
            print(f"Warning: Failed to tokenize item '{self.title}': {e}")
            self.include = False
            return
        
        # Step 6: Check if we have enough tokens
        if len(tokens) < MIN_TOKENS:
            # Not enough meaningful content after tokenization
            self.include = False
            return
        
        # Step 7: Truncate to maximum token length
        if len(tokens) > MAX_TOKENS:
            tokens = tokens[:MAX_TOKENS]
        
        # Step 8: Decode tokens back to text (this gives us the truncated text)
        final_text = self._tokenizer.decode(tokens)
        
        # Step 9: Create the training prompt
        self._make_prompt(final_text)
        
        # Step 10: Mark this item as included
        self.include = True
    
    def _make_prompt(self, product_text: str) -> None:
        """
        Create a formatted training prompt from the product text.
        
        Format:
            How much does this cost to the nearest dollar?
            
            [product text]
            
            Price is $X.00
        
        Args:
            product_text: The cleaned and tokenized product description
        """
        # Build the prompt in the specified format
        prompt_parts = [
            self.QUESTION,           # The question
            "",                      # Blank line
            product_text,           # The product description
            "",                      # Blank line
            f"{self.PREFIX}{round(self.price):.2f}"  # The answer
        ]
        
        # Join with newlines
        self.prompt = "\n".join(prompt_parts)
        
        # Calculate and store the total token count
        try:
            tokens = self._tokenizer.encode(self.prompt, add_special_tokens=False)
            self.token_count = len(tokens)
        except Exception as e:
            print(f"Warning: Failed to count tokens for prompt: {e}")
            self.token_count = 0
    
    def get_test_prompt(self) -> str:
        """
        Return a prompt suitable for testing (without the actual price).
        
        This is useful for model inference where we want to predict the price.
        
        Returns:
            str: The prompt with everything except the final price
        """
        if not self.prompt:
            return ""
        
        # Split on the price prefix and return everything before it, plus the prefix
        # This gives us the question and product info, ready for the model to complete
        prompt_without_price = self.prompt.split(self.PREFIX)[0]
        return prompt_without_price + self.PREFIX
    
    def __repr__(self) -> str:
        """
        Return a human-readable string representation of this Item.
        
        Returns:
            str: String in format "<Product Title = $X.XX>"
        """
        return f"<{self.title} = ${self.price:.2f}>"


# =============================================================================
# USAGE EXAMPLE
# =============================================================================

if __name__ == "__main__":
    # Example product data
    sample_data = {
        'title': 'Wireless Bluetooth Headphones',
        'description': [
            'Premium over-ear headphones with active noise cancellation',
            'Up to 30 hours of battery life on a single charge'
        ],
        'features': [
            'Bluetooth 5.0 connectivity',
            'Comfortable memory foam ear cushions',
            'Foldable design for easy storage'
        ],
        'details': 'Item Weight: 250g, Color: Black, Batteries Required?: No'
    }
    
    # Create an item
    item = Item.from_data(sample_data, price=89.99)
    
    # Check if it passed quality filters
    if item.include:
        print(f"Created item: {item}")
        print(f"Token count: {item.token_count}")
        print(f"\nTraining prompt:\n{item.prompt}")
        print(f"\nTest prompt:\n{item.get_test_prompt()}")
    else:
        print(f"Item '{item.title}' did not pass quality filters")