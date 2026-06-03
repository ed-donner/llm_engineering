"""
Display Utilities Module

Functions for formatting and displaying recipe analysis results.
"""

from IPython.display import Markdown, display


def display_nutrition(nutrition_data):
    """Display nutrition information in a formatted way."""
    if not nutrition_data:
        print("No nutrition data available")
        return
    
    per_serving = nutrition_data.get('per_serving', {})
    servings = nutrition_data.get('servings', 1)
    findings = nutrition_data.get('key_findings', [])
    
    markdown = f"""# 📊 NUTRITION ANALYSIS

**Recipe makes {servings} servings**

## Per Serving:
- **Calories:** {per_serving.get('calories', 'N/A')} kcal
- **Protein:** {per_serving.get('protein_g', 'N/A')}g
- **Carbohydrates:** {per_serving.get('carbohydrates_g', 'N/A')}g
- **Fat:** {per_serving.get('fat_g', 'N/A')}g
  - Saturated Fat: {per_serving.get('saturated_fat_g', 'N/A')}g
- **Fiber:** {per_serving.get('fiber_g', 'N/A')}g
- **Sugar:** {per_serving.get('sugar_g', 'N/A')}g
- **Sodium:** {per_serving.get('sodium_mg', 'N/A')}mg

## 🔍 Key Findings:
"""
    for finding in findings:
        markdown += f"- {finding}\n"
    
    display(Markdown(markdown))


def display_substitutions(substitutions_data):
    """Display substitution suggestions."""
    if not substitutions_data:
        print("No substitution suggestions available")
        return
    
    subs = substitutions_data.get('substitutions', [])
    
    markdown = "# 💡 HEALTHY SUBSTITUTION SUGGESTIONS\n\n"
    
    for i, sub in enumerate(subs, 1):
        markdown += f"""## {i}. {sub.get('original', '')} → {sub.get('suggestion', '')}

**Health Benefit:** {sub.get('health_benefit', '')}  
**Impact:** {sub.get('impact', '')}  
**Nutrition Improvement:** {sub.get('nutrition_improvement', '')}

"""
    
    display(Markdown(markdown))


def display_modified_recipe(modified_recipe):
    """Display modified recipe for dietary restrictions."""
    if not modified_recipe:
        print("No modified recipe available")
        return
    
    markdown = f"""# 🌱 MODIFIED RECIPE

## {modified_recipe.get('modified_title', 'Modified Recipe')}

### Summary of Changes:
{modified_recipe.get('modifications_summary', '')}

### Modified Ingredients:
"""
    for ing in modified_recipe.get('modified_ingredients', []):
        sub_text = f" (replaces: {ing.get('substitution', '')})" if ing.get('substitution') else ""
        notes = ing.get('notes', '')
        markdown += f"- **{ing.get('quantity', '')} {ing.get('ingredient', '')}**{notes}{sub_text}\n"
    
    markdown += "\n### Modified Instructions:\n"
    for i, step in enumerate(modified_recipe.get('modified_instructions', []), 1):
        markdown += f"{i}. {step}\n"
    
    if modified_recipe.get('notes'):
        markdown += f"\n### Notes:\n{modified_recipe.get('notes', '')}\n"
    
    display(Markdown(markdown))

