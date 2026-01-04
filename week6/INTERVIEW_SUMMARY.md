# Week 6: Product Pricing Model & Data Curation

## Core Concepts Covered

### 1. **Product Pricing Prediction**
- **Business Problem**: Estimating product prices from descriptions
- **Dataset Curation**: Amazon Reviews 2023 dataset processing
- **Data Cleaning**: Handling missing prices, cleaning descriptions
- **Feature Engineering**: Extracting meaningful features from text

### 2. **Large-Scale Data Processing**
- **Hugging Face Datasets**: Working with large datasets efficiently
- **Data Filtering**: Subsetting data for specific categories (Appliances)
- **Memory Management**: Handling large datasets without memory issues
- **Data Validation**: Ensuring data quality and consistency

### 3. **Text Processing & Analysis**
- **Product Descriptions**: Processing and cleaning product text
- **Feature Extraction**: Extracting relevant information from descriptions
- **Text Preprocessing**: Tokenization, cleaning, normalization
- **Data Exploration**: Understanding data distribution and patterns

### 4. **Model Preparation**
- **Data Splitting**: Training, validation, and test sets
- **Feature Engineering**: Creating input features for pricing models
- **Target Variable**: Price prediction and regression setup
- **Data Pipeline**: End-to-end data processing workflow

### 5. **Business Applications**
- **E-commerce**: Product pricing optimization
- **Market Analysis**: Understanding price factors
- **Competitive Intelligence**: Price comparison and analysis
- **Revenue Optimization**: Data-driven pricing strategies

## Key Code Patterns

### Dataset Loading and Exploration
```python
from datasets import load_dataset
import matplotlib.pyplot as plt

# Load Amazon Reviews dataset
dataset = load_dataset("McAuley-Lab/Amazon-Reviews-2023", 
                      f"raw_meta_Appliances", 
                      split="full", 
                      trust_remote_code=True)

print(f"Number of Appliances: {len(dataset):,}")

# Explore data structure
datapoint = dataset[2]
print(f"Title: {datapoint['title']}")
print(f"Description: {datapoint['description']}")
print(f"Price: {datapoint['price']}")
```

### Data Quality Analysis
```python
# Count items with prices
prices = 0
for item in dataset:
    if item['price'] is not None and item['price'] > 0:
        prices += 1

print(f"Items with valid prices: {prices:,}")
print(f"Percentage with prices: {prices/len(dataset)*100:.2f}%")
```

### Data Filtering and Cleaning
```python
def clean_product_data(item):
    # Clean description
    description = item.get('description', '')
    if description:
        description = description.strip()
    
    # Clean price
    price = item.get('price')
    if price is None or price <= 0:
        price = None
    
    return {
        'title': item.get('title', ''),
        'description': description,
        'price': price,
        'features': item.get('features', ''),
        'details': item.get('details', '')
    }

# Apply cleaning
cleaned_data = [clean_product_data(item) for item in dataset]
```

### Feature Engineering
```python
def extract_features(item):
    features = {
        'title_length': len(item['title']) if item['title'] else 0,
        'description_length': len(item['description']) if item['description'] else 0,
        'has_features': bool(item['features']),
        'has_details': bool(item['details']),
        'word_count': len(item['description'].split()) if item['description'] else 0
    }
    return features
```

### Data Visualization
```python
import matplotlib.pyplot as plt

# Price distribution
prices = [item['price'] for item in cleaned_data if item['price'] is not None]
plt.hist(prices, bins=50, alpha=0.7)
plt.xlabel('Price ($)')
plt.ylabel('Frequency')
plt.title('Price Distribution of Appliances')
plt.show()
```

## Interview-Ready Talking Points

1. **"I built a product pricing prediction system using real-world e-commerce data"**
   - Explain the business value of accurate price prediction
   - Discuss the challenges of working with large, messy datasets

2. **"I implemented comprehensive data curation and cleaning pipelines"**
   - Show understanding of data quality issues and solutions
   - Discuss the importance of data validation and preprocessing

3. **"I worked with Hugging Face datasets for large-scale data processing"**
   - Explain the benefits of using established dataset platforms
   - Discuss memory management and efficient data processing

4. **"I created features from unstructured text data for machine learning"**
   - Show understanding of text processing and feature engineering
   - Discuss the challenges of converting text to numerical features

## Technical Skills Demonstrated

- **Data Processing**: Large-scale dataset handling, cleaning, validation
- **Text Processing**: Description cleaning, feature extraction
- **Data Analysis**: Exploration, visualization, statistical analysis
- **Feature Engineering**: Creating ML-ready features from text
- **Data Pipeline**: End-to-end data processing workflows
- **Business Applications**: E-commerce, pricing optimization
- **Memory Management**: Efficient handling of large datasets

## Common Interview Questions & Answers

**Q: "How did you handle the data quality issues in the Amazon dataset?"**
A: "I implemented comprehensive data validation, handled missing prices and descriptions, cleaned text data, and created quality metrics to track data completeness. I also used filtering to focus on high-quality data points for model training."

**Q: "What features did you extract from product descriptions for pricing prediction?"**
A: "I extracted text length, word count, presence of specific keywords, brand mentions, and technical specifications. I also created categorical features for product categories and used text embeddings for semantic similarity."

**Q: "How did you handle the class imbalance in price distribution?"**
A: "I used stratified sampling for train/test splits, implemented price binning for classification approaches, and used regression with appropriate loss functions. I also considered log transformation for skewed price distributions."

**Q: "What challenges did you face with the large dataset size?"**
A: "I used streaming data loading, implemented batch processing, and used memory-efficient data structures. I also created data subsets for initial experimentation and used progressive loading for the full dataset when needed."