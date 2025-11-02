"""
Data cleaning utilities for dataset preparation
"""

from collections import defaultdict


def clean_dataset(data, min_length=10, max_samples_per_intent=None):
    """
    Clean and prepare dataset for fine-tuning
    
    Args:
        data: HuggingFace dataset or list of examples
        min_length: Minimum text length to keep (default: 10)
        max_samples_per_intent: Max samples per intent for balancing (default: None = no limit)
    
    Returns:
        list: Cleaned examples
    
    Example:
        >>> cleaned = clean_dataset(dataset['train'], min_length=10, max_samples_per_intent=200)
        >>> print(f"Cleaned {len(cleaned)} examples")
    """
    cleaned = []
    
    for example in data:
        text = example['text'].strip()
        
        # Skip if too short
        if len(text) < min_length:
            continue
        
        # Normalize text - remove extra whitespace
        text = ' '.join(text.split())
        
        cleaned.append({
            'text': text,
            'label': example['label']
        })
    
    # Balance classes if max_samples_per_intent is specified
    if max_samples_per_intent:
        balanced = defaultdict(list)
        
        for item in cleaned:
            balanced[item['label']].append(item)
        
        cleaned = []
        for label, items in balanced.items():
            cleaned.extend(items[:max_samples_per_intent])
    
    return cleaned


def analyze_distribution(data):
    """
    Analyze label distribution in dataset
    
    Args:
        data: List of examples with 'label' field
    
    Returns:
        dict: Label counts
    """
    from collections import Counter
    labels = [item['label'] for item in data]
    return Counter(labels)

