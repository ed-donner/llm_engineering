# Recipe Nutrition Calculator & Modifier

An AI-powered tool that analyzes recipes from the web or text input, calculates approximate nutrition information, suggests healthy substitutions, and modifies recipes for dietary restrictions.

## 🎯 Features

- **Web Recipe Scraping**: Extracts recipes from popular recipe websites (AllRecipes, Food Network, BBC Good Food, etc.)
- **Nutrition Calculation**: Uses LLM to estimate nutritional values (calories, protein, carbs, fats, vitamins, etc.)
- **Dietary Modifications**: Automatically adapts recipes for:
  - Vegan/Vegetarian
  - Keto/Low-carb
  - Gluten-free
  - Low-sodium
  - Dairy-free
  - And more custom restrictions
- **Healthy Substitutions**: Suggests ingredient swaps for better nutrition
- **Portion Scaling**: Adjusts nutrition values based on serving size

## 🚀 Quick Start

### Prerequisites

- Python 3.7+
- OpenAI API key

### Installation

1. **Install required packages:**
   ```bash
   pip install requests beautifulsoup4 openai python-dotenv ipython pandas
   ```

2. **Set up your API key:**
   
   Create a `.env` file in the same directory:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   ```

3. **Run the notebook:**
   Open `recipe_nutrition_calculator.ipynb` in Jupyter Lab or VS Code

## 💡 Usage Examples

### Analyze a Recipe from URL

```python
# Analyze a recipe from AllRecipes
url = "https://www.allrecipes.com/recipe/..."
result = analyze_recipe_from_url(url)
display_nutrition_analysis(result)
```

### Analyze Recipe from Text

```python
recipe_text = """
Chocolate Chip Cookies
- 2 cups all-purpose flour
- 1 cup butter
- 1 cup brown sugar
- 2 eggs
...
"""
result = analyze_recipe_from_text(recipe_text)
```

### Modify for Dietary Restrictions

```python
# Make it vegan
modified = modify_recipe(result, dietary_restrictions=["vegan"])
display_modified_recipe(modified)

# Make it keto-friendly
modified = modify_recipe(result, dietary_restrictions=["keto", "low-carb"])
```

### Get Healthy Substitutions

```python
substitutions = suggest_substitutions(result)
display_substitutions(substitutions)
```

## 📊 Example Output

```
📊 NUTRITION ANALYSIS (per serving)
═══════════════════════════════════
Calories: 245 kcal
Protein: 8.5g
Carbohydrates: 32g
Fat: 9.2g
Fiber: 2.1g
Sugar: 12g
Sodium: 420mg

🔍 KEY FINDINGS:
- High in saturated fat (butter)
- Moderate sodium content
- Good source of protein from eggs

💡 HEALTHY SUBSTITUTIONS:
1. Butter → Coconut oil or applesauce (reduce saturated fat)
2. White flour → Whole wheat flour (increase fiber)
3. Sugar → Stevia or honey (reduce refined sugar)

🌱 VEGAN MODIFICATION:
- Replace 2 eggs with 2 flax eggs (2 tbsp ground flaxseed + 6 tbsp water)
- Replace butter with vegan butter or coconut oil
```

## 🛠️ How It Works

1. **Recipe Extraction**: Scrapes or parses recipe text to extract ingredients and quantities
2. **Ingredient Parsing**: Uses LLM to understand ingredients and convert to standardized format
3. **Nutrition Estimation**: LLM estimates nutritional values based on ingredient knowledge
4. **Dietary Modification**: Identifies non-compliant ingredients and suggests replacements
5. **Substitution Suggestions**: Recommends healthier alternatives with explanations

## 📁 Project Structure

```
Recipe_Nutrition_Calculator/
├── README.md
├── recipe_nutrition_calculator.ipynb  # Main notebook (LLM calls only)
├── requirements.txt
├── recipe_scraper.py                  # Web scraping logic
├── recipe_formatter.py                # Data formatting utilities
├── display_utils.py                   # Display/formatting functions
├── config.py                          # Configuration and constants
└── .env (create this, git-ignored)
```

### Code Organization

- **Notebook**: Contains all LLM API calls and orchestration logic
- **Python Modules**: Utility functions, scrapers, formatters, and display functions
- **Clean Separation**: LLM logic is centralized in the notebook for easy modification

## ⚠️ Important Notes

### Nutrition Accuracy

- **Approximate Values**: Nutrition calculations are estimates based on LLM knowledge
- **Not Medical Advice**: This tool is for informational purposes only
- **Always Check Labels**: For precise nutrition, use official nutrition databases or product labels
- **Variations**: Actual nutrition may vary based on brand, preparation method, etc.

### API Costs

- Uses GPT-4o-mini (very affordable - ~$0.001 per recipe analysis)

## 📄 License

MIT License - Feel free to use and modify for personal or educational purposes.

## 🙏 Acknowledgments

- Built as part of LLM Engineering Course Week 1
- Uses OpenAI GPT-4o-mini for nutrition analysis
- Inspired by the need for accessible nutrition information

---

**Disclaimer**: This tool provides estimated nutrition information and dietary suggestions. Always consult with healthcare professionals for medical dietary advice. Individual nutritional needs vary.

