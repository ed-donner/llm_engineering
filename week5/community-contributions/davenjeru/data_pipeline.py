"""
Data pipeline module for loading, parsing, and validating recipe data.
Consolidates data_loader, parser, and validator functionality.
"""

import os
import re
import json
import ast
from pathlib import Path
from collections import defaultdict

import pandas as pd
import kagglehub

from config import KAGGLE_DATASET, CSV_FILENAME, OUTPUT_DIR, DEFAULT_NUM_RECIPES


def _parse_list(value, delimiter=','):
    """Parse a value into a list of strings."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if item and str(item).strip()]
    
    value_str = str(value)
    if value_str.startswith('['):
        try:
            parsed = ast.literal_eval(value_str)
            if isinstance(parsed, list):
                result = []
                for item in parsed:
                    if isinstance(item, dict):
                        parts = [str(item.get(k, '')) for k in ['quantity', 'unit', 'name'] if item.get(k)]
                        result.append(' '.join(parts).strip())
                    else:
                        result.append(str(item).strip())
                return [r for r in result if r]
        except (ValueError, SyntaxError):
            pass
    return [item.strip() for item in value_str.split(delimiter) if item.strip()]


def _get_value(row, column_names):
    """Get value from row using first matching column name."""
    for col in column_names:
        if col in row.index and pd.notna(row[col]):
            return row[col]
    return None


class DataPipeline:
    """Pipeline for loading, parsing, and validating recipe data."""
    
    INGREDIENT_CATEGORIES = {
        'proteins': ['chicken', 'beef', 'pork', 'fish', 'tofu', 'beans', 'lentils', 'eggs', 'turkey', 'lamb', 'shrimp', 'salmon'],
        'vegetables': ['onion', 'garlic', 'tomato', 'carrot', 'broccoli', 'spinach', 'pepper', 'celery', 'potato', 'lettuce', 'cucumber', 'zucchini', 'mushroom'],
        'grains': ['rice', 'pasta', 'bread', 'quinoa', 'oats', 'flour', 'noodle', 'tortilla', 'couscous'],
        'dairy': ['milk', 'cheese', 'butter', 'cream', 'yogurt', 'sour cream', 'parmesan'],
        'spices': ['salt', 'pepper', 'cumin', 'paprika', 'oregano', 'basil', 'thyme', 'cinnamon', 'ginger', 'curry', 'cayenne'],
        'fruits': ['apple', 'lemon', 'orange', 'banana', 'berry', 'lime', 'cranberry']
    }
    
    REQUIRED_FIELDS = ['title', 'ingredients', 'instructions']
    
    def __init__(self, output_dir=None):
        self.output_dir = output_dir or OUTPUT_DIR
        Path(self.output_dir).mkdir(exist_ok=True)
        self.validation_stats = {'total': 0, 'valid': 0, 'errors': []}
    
    def load(self, num_recipes=None, random_sample=True):
        """Load recipes from Kaggle dataset."""
        num_recipes = num_recipes or DEFAULT_NUM_RECIPES
        
        print(f"Downloading dataset: {KAGGLE_DATASET}")
        dataset_path = kagglehub.dataset_download(KAGGLE_DATASET)
        
        csv_path = os.path.join(dataset_path, CSV_FILENAME)
        if not os.path.exists(csv_path):
            csv_files = [f for f in os.listdir(dataset_path) if f.endswith('.csv')]
            if csv_files:
                csv_path = os.path.join(dataset_path, csv_files[0])
            else:
                raise FileNotFoundError(f"No CSV files found in {dataset_path}")
        
        df = pd.read_csv(csv_path)
        print(f"Dataset contains {len(df)} recipes")
        
        if random_sample and len(df) > num_recipes:
            df = df.sample(n=num_recipes, random_state=42)
        else:
            df = df.head(num_recipes)
        
        recipes = []
        for idx, row in df.iterrows():
            recipe = {
                "id": f"recipe_{idx}",
                "title": str(_get_value(row, ['recipe_name', 'Name', 'name', 'title']) or "Unknown Recipe"),
                "source_url": _get_value(row, ['url', 'URL', 'source_url']) or "",
                "ingredients": _parse_list(_get_value(row, ['ingredients', 'Ingredients'])),
                "instructions": self._parse_instructions(_get_value(row, ['directions', 'Directions', 'instructions', 'Instructions'])),
                "prep_time": _get_value(row, ['prep_time', 'Prep Time', 'prep_time_minutes']),
                "cook_time": _get_value(row, ['cook_time', 'Cook Time', 'cook_time_minutes']),
                "total_time": _get_value(row, ['total_time', 'Total Time', 'total_time_minutes']),
                "servings": _get_value(row, ['servings', 'Servings']),
                "cuisine": self._extract_cuisine(row),
                "cuisine_path": _get_value(row, ['cuisine_path', 'category']),
                "rating": _get_value(row, ['rating', 'Rating']),
                "nutrition": _get_value(row, ['nutrition', 'Nutrition']),
                "image_url": _get_value(row, ['img_src', 'image_url', 'image']),
                "description": _get_value(row, ['description', 'Description']) or "",
            }
            recipes.append(recipe)
        
        print(f"Loaded {len(recipes)} recipes")
        return recipes
    
    def _parse_instructions(self, instructions_raw):
        """Parse instructions into a single string."""
        if pd.isna(instructions_raw) or instructions_raw is None:
            return ""
        if isinstance(instructions_raw, list):
            return '\n'.join([str(step).strip() for step in instructions_raw if step])
        
        instructions_str = str(instructions_raw)
        if instructions_str.startswith('['):
            try:
                parsed = ast.literal_eval(instructions_str)
                if isinstance(parsed, list):
                    return '\n'.join([str(step).strip() for step in parsed if step])
            except (ValueError, SyntaxError):
                pass
        return instructions_str
    
    def _extract_cuisine(self, row):
        """Extract cuisine type from row data."""
        cuisine_path = _get_value(row, ['cuisine_path', 'category', 'cuisine'])
        if cuisine_path and pd.notna(cuisine_path):
            cuisine_str = str(cuisine_path)
            if '/' in cuisine_str:
                parts = [p.strip() for p in cuisine_str.split('/') if p.strip()]
                return parts[-1] if len(parts) > 1 else (parts[0] if parts else "Unknown")
            return cuisine_str
        return "Unknown"
    
    def parse(self, recipes):
        """Parse and enrich recipe data with categories and dietary info."""
        processed = []
        
        for recipe in recipes:
            ingredients = recipe.get('ingredients', [])
            instructions = recipe.get('instructions', '')
            
            parsed_ingredients, ingredient_categories = self._categorize_ingredients(ingredients)
            instruction_data = self._parse_instruction_steps(instructions)
            dietary_info = self._extract_dietary_info(recipe)
            cuisine_info = self._parse_cuisine_path(recipe.get('cuisine_path', ''))
            
            ingredients_text = ' '.join(ingredients) if isinstance(ingredients, list) else str(ingredients)
            
            enhanced = {
                **recipe,
                'parsed_ingredients': parsed_ingredients,
                'ingredient_categories': ingredient_categories,
                'instruction_data': instruction_data,
                'dietary_info': dietary_info,
                'cuisine_info': cuisine_info,
                'searchable_text': f"{recipe.get('title', '')} {recipe.get('description', '')} {ingredients_text} {instructions}"
            }
            processed.append(enhanced)
        
        print(f"Parsed {len(processed)} recipes")
        return processed
    
    def _categorize_ingredients(self, ingredients):
        """Categorize ingredients by type."""
        ingredients_list = ingredients if isinstance(ingredients, list) else _parse_list(ingredients)
        parsed = []
        categories = defaultdict(list)
        
        for ingredient in ingredients_list:
            clean = re.sub(r'\d+[\s\w]*', '', str(ingredient)).strip()
            clean = re.sub(r'[^\w\s]', '', clean).lower()
            
            category = 'other'
            for cat, items in self.INGREDIENT_CATEGORIES.items():
                if any(item in clean for item in items):
                    category = cat
                    break
            
            parsed.append({'original': ingredient, 'cleaned': clean, 'category': category})
            categories[category].append(ingredient)
        
        return parsed, dict(categories)
    
    def _parse_instruction_steps(self, instructions):
        """Parse instructions into steps and extract cooking methods."""
        if isinstance(instructions, list):
            text = '\n'.join([str(step).strip() for step in instructions if step])
        else:
            text = str(instructions) if instructions else ""
        
        steps = re.split(r'\n+|\d+\.\s*', text)
        steps = [s.strip() for s in steps if s.strip() and len(s.strip()) > 10]
        
        techniques = ['bake', 'fry', 'boil', 'sauté', 'saute', 'grill', 'roast', 'steam', 'simmer', 'broil', 'stir-fry', 'poach', 'braise']
        methods = list({t for step in steps for t in techniques if t in step.lower()})
        
        return {'steps': steps, 'cooking_methods': methods, 'step_count': len(steps)}
    
    def _parse_cuisine_path(self, cuisine_path):
        """Parse cuisine path into categories."""
        if not cuisine_path or str(cuisine_path) == 'nan':
            return {'main_category': 'Unknown', 'subcategories': [], 'full_path': ''}
        
        path_str = str(cuisine_path).strip()
        parts = [p.strip() for p in path_str.split('/') if p.strip()]
        
        return {
            'main_category': parts[0] if parts else 'Unknown',
            'subcategories': parts[1:] if len(parts) > 1 else [],
            'full_path': path_str
        }
    
    def _extract_dietary_info(self, recipe):
        """Extract dietary flags from recipe data."""
        ingredients = recipe.get('ingredients', [])
        ingredients_text = ' '.join(ingredients) if isinstance(ingredients, list) else str(ingredients)
        text = f"{recipe.get('title', '')} {ingredients_text}".lower()
        
        meat = ['chicken', 'beef', 'pork', 'fish', 'meat', 'bacon', 'ham', 'turkey', 'lamb', 'shrimp', 'salmon', 'sausage']
        dairy = ['milk', 'cheese', 'butter', 'cream', 'yogurt', 'egg']
        gluten = ['flour', 'bread', 'pasta', 'wheat', 'noodle']
        
        has_meat = any(kw in text for kw in meat)
        has_dairy = any(kw in text for kw in dairy)
        has_gluten = any(kw in text for kw in gluten)
        
        return {
            'vegetarian': not has_meat or 'vegetarian' in text,
            'vegan': not has_meat and not has_dairy and 'vegan' in text,
            'gluten_free': not has_gluten or 'gluten-free' in text or 'gluten free' in text,
            'dairy_free': not has_dairy or 'dairy-free' in text or 'dairy free' in text,
            'low_carb': any(w in text for w in ['low-carb', 'low carb', 'keto']),
            'healthy': any(w in text for w in ['healthy', 'light', 'clean', 'salad', 'vegetable'])
        }
    
    def validate(self, recipes):
        """Validate and normalize recipes."""
        self.validation_stats = {'total': len(recipes), 'valid': 0, 'errors': []}
        validated = []
        
        for i, recipe in enumerate(recipes):
            is_valid, errors = self._validate_recipe(recipe)
            
            if is_valid:
                normalized = self._normalize_recipe(recipe)
                validated.append(normalized)
                self.validation_stats['valid'] += 1
            else:
                self.validation_stats['errors'].append({
                    'index': i, 'title': recipe.get('title', 'Unknown'), 'errors': errors
                })
        
        print(f"Validated {self.validation_stats['valid']}/{self.validation_stats['total']} recipes")
        return validated
    
    def _validate_recipe(self, recipe):
        """Validate individual recipe."""
        errors = []
        
        for field in self.REQUIRED_FIELDS:
            value = recipe.get(field)
            if not value or (isinstance(value, (list, str)) and len(value) == 0):
                errors.append(f"Missing {field}")
        
        ingredients = recipe.get('ingredients', [])
        if isinstance(ingredients, str):
            ingredients = _parse_list(ingredients)
        if len(ingredients) < 2:
            errors.append("Too few ingredients")
        
        instructions = recipe.get('instructions', '')
        if isinstance(instructions, list):
            instructions = ' '.join(instructions)
        if len(str(instructions)) < 20:
            errors.append("Instructions too short")
        
        if len(str(recipe.get('title', ''))) < 3:
            errors.append("Title too short")
        
        return len(errors) == 0, errors
    
    def _normalize_recipe(self, recipe):
        """Normalize recipe data formats."""
        normalized = recipe.copy()
        
        title = recipe.get('title', '')
        normalized['title'] = str(title).strip().title() if title else 'Unknown Recipe'
        
        for time_field in ['prep_time', 'cook_time', 'total_time']:
            normalized[time_field] = self._normalize_time(recipe.get(time_field))
        
        servings = recipe.get('servings')
        if servings:
            match = re.search(r'(\d+)', str(servings))
            normalized['servings'] = int(match.group(1)) if match else None
        
        ingredients = recipe.get('ingredients', [])
        if isinstance(ingredients, str):
            normalized['ingredients'] = _parse_list(ingredients)
        elif isinstance(ingredients, list):
            normalized['ingredients'] = [str(ing).strip() for ing in ingredients if ing and str(ing).strip()]
        else:
            normalized['ingredients'] = []
        
        instructions = recipe.get('instructions', '')
        if isinstance(instructions, list):
            normalized['instructions'] = '\n'.join([str(step).strip() for step in instructions if step])
        else:
            normalized['instructions'] = str(instructions).strip() if instructions else ''
        
        return normalized
    
    def _normalize_time(self, time_val):
        """Convert time strings to minutes."""
        if isinstance(time_val, (int, float)) and not pd.isna(time_val):
            return int(time_val)
        if not time_val or str(time_val).lower() == 'nan':
            return None
        
        time_str = str(time_val).lower().strip()
        minutes = 0
        
        for pattern in [r'(\d+)\s*hrs?', r'(\d+)\s*hours?', r'(\d+)\s*h\b']:
            match = re.search(pattern, time_str)
            if match:
                minutes += int(match.group(1)) * 60
                break
        
        for pattern in [r'(\d+)\s*mins?', r'(\d+)\s*minutes?', r'(\d+)\s*m\b']:
            match = re.search(pattern, time_str)
            if match:
                minutes += int(match.group(1))
                break
        
        if minutes == 0:
            match = re.search(r'^(\d+)$', time_str.strip())
            if match:
                minutes = int(match.group(1))
        
        return minutes if minutes > 0 else None
    
    def get_validation_report(self):
        """Generate validation report."""
        total = self.validation_stats['total']
        valid = self.validation_stats['valid']
        if total == 0:
            return "No recipes to validate."
        
        report = f"Validation: {valid}/{total} recipes valid ({valid/total*100:.1f}%)"
        if self.validation_stats['errors']:
            report += f"\n{len(self.validation_stats['errors'])} recipes failed validation"
        return report
    
    def save(self, recipes, filename="recipes_validated.json"):
        """Save recipes to JSON file."""
        filepath = os.path.join(self.output_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(recipes, f, indent=2, ensure_ascii=False, default=str)
        print(f"Saved {len(recipes)} recipes to {filepath}")
        return filepath
    
    def run(self, num_recipes=None, random_sample=True):
        """Run full pipeline: load -> parse -> validate -> save."""
        recipes = self.load(num_recipes, random_sample)
        parsed = self.parse(recipes)
        validated = self.validate(parsed)
        self.save(validated)
        print(self.get_validation_report())
        return validated
