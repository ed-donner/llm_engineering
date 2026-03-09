"""
Feature engineering utilities for price prediction
"""

import numpy as np
import pandas as pd
from typing import List
from sklearn.preprocessing import LabelEncoder, StandardScaler
import re


class FeatureEngineer:
    """
    Advanced feature engineering for product price prediction
    """
    
    def __init__(self):
        self.category_encoder = LabelEncoder()
        self.brand_encoder = LabelEncoder()
        self.scaler = StandardScaler()
        self.fitted = False
    
    def extract_numeric_features(self, items: List) -> pd.DataFrame:
        """Extract numeric features from items"""
        features = []
        
        for item in items:
            feature_dict = {
                'weight': item.weight or 0,
                'weight_unknown': 1 if not item.weight else 0,
                'word_count': item.word_count or 0,
                'char_count': item.char_count or 0,
                'has_dimensions': 1 if item.has_dimensions else 0,
                'is_premium': 1 if item.is_premium else 0,
                'text_quality_score': item.text_quality_score or 0,
                'price_per_weight': item.price_per_weight or 0,
            }
            features.append(feature_dict)
        
        return pd.DataFrame(features)
    
    def extract_categorical_features(self, items: List) -> pd.DataFrame:
        """Extract and encode categorical features"""
        categories = [item.category for item in items]
        brands = [item.brand or "Unknown" for item in items]
        price_buckets = [item.price_bucket or "medium" for item in items]
        
        df = pd.DataFrame({
            'category': categories,
            'brand': brands,
            'price_bucket': price_buckets
        })
        
        return df
    
    def fit_transform(self, items: List) -> pd.DataFrame:
        """Fit encoders and transform features"""
        # Extract features
        numeric_df = self.extract_numeric_features(items)
        categorical_df = self.extract_categorical_features(items)
        
        # Encode categorical features
        categorical_df['category_encoded'] = self.category_encoder.fit_transform(categorical_df['category'])
        categorical_df['brand_encoded'] = self.brand_encoder.fit_transform(categorical_df['brand'])
        
        # One-hot encode price bucket
        price_bucket_dummies = pd.get_dummies(categorical_df['price_bucket'], prefix='bucket')
        
        # Combine all features
        features_df = pd.concat([
            numeric_df,
            categorical_df[['category_encoded', 'brand_encoded']],
            price_bucket_dummies
        ], axis=1)
        
        # Scale numeric features
        numeric_cols = numeric_df.columns.tolist()
        features_df[numeric_cols] = self.scaler.fit_transform(features_df[numeric_cols])
        
        self.fitted = True
        return features_df
    
    def transform(self, items: List) -> pd.DataFrame:
        """Transform features using fitted encoders"""
        if not self.fitted:
            raise ValueError("FeatureEngineer must be fitted before transform")
        
        # Extract features
        numeric_df = self.extract_numeric_features(items)
        categorical_df = self.extract_categorical_features(items)
        
        # Encode categorical features
        categorical_df['category_encoded'] = self.category_encoder.transform(categorical_df['category'])
        categorical_df['brand_encoded'] = self.brand_encoder.transform(categorical_df['brand'])
        
        # One-hot encode price bucket
        price_bucket_dummies = pd.get_dummies(categorical_df['price_bucket'], prefix='bucket')
        
        # Combine all features
        features_df = pd.concat([
            numeric_df,
            categorical_df[['category_encoded', 'brand_encoded']],
            price_bucket_dummies
        ], axis=1)
        
        # Scale numeric features
        numeric_cols = numeric_df.columns.tolist()
        features_df[numeric_cols] = self.scaler.transform(features_df[numeric_cols])
        
        return features_df


def extract_keywords(text: str) -> List[str]:
    """Extract important keywords from text"""
    if not text:
        return []
    
    # Remove common words and extract meaningful terms
    words = re.findall(r'\b[A-Za-z]{3,}\b', text.lower())
    
    # Filter out very common words
    stopwords = {'the', 'and', 'for', 'with', 'this', 'that', 'from', 'are', 'was', 'were'}
    keywords = [w for w in words if w not in stopwords]
    
    return keywords[:20]  # Top 20 keywords


def compute_similarity_score(item1, item2) -> float:
    """Compute similarity between two items"""
    score = 0.0
    
    # Category match
    if item1.category == item2.category:
        score += 0.4
    
    # Brand match
    if item1.brand and item2.brand and item1.brand == item2.brand:
        score += 0.3
    
    # Price bucket match
    if item1.price_bucket == item2.price_bucket:
        score += 0.2
    
    # Weight similarity
    if item1.weight and item2.weight:
        weight_diff = abs(item1.weight - item2.weight) / max(item1.weight, item2.weight)
        score += 0.1 * (1 - min(weight_diff, 1.0))
    
    return score
