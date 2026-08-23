"""
RAG core module for vector storage and semantic search.
Consolidates vector_store and rag_engine functionality.
"""

import chromadb
from sentence_transformers import SentenceTransformer

from config import VECTOR_DB_DIR, EMBEDDING_MODEL


class RecipeRAG:
    """Unified RAG system for recipe embeddings and semantic search."""
    
    def __init__(self, recipes_data=None, persist_directory=None):
        persist_directory = persist_directory or VECTOR_DB_DIR
        
        self.client = chromadb.PersistentClient(path=persist_directory)
        self.embedding_model = SentenceTransformer(EMBEDDING_MODEL)
        self.collection = self.client.get_or_create_collection(
            name="recipes",
            metadata={"description": "Recipe collection for RAG system"}
        )
        
        self.recipes_data = {}
        if recipes_data:
            self.recipes_data = {recipe['id']: recipe for recipe in recipes_data}
        
        self._chunk_cache = {}
        print(f"RAG initialized with {self.collection.count()} existing chunks")
    
    def set_recipes(self, recipes_data):
        """Set the recipes data for retrieval."""
        self.recipes_data = {recipe['id']: recipe for recipe in recipes_data}
    
    def add_recipes(self, recipes):
        """Add recipes to vector store."""
        all_chunks, all_ids, all_embeddings, all_metadatas = [], [], [], []
        
        for recipe in recipes:
            chunks = self._create_chunks(recipe)
            self._chunk_cache[recipe['id']] = chunks
            
            for chunk in chunks:
                embedding = self.embedding_model.encode(chunk['text']).tolist()
                all_chunks.append(chunk['text'])
                all_ids.append(chunk['id'])
                all_embeddings.append(embedding)
                all_metadatas.append(self._sanitize_metadata({
                    'recipe_id': recipe['id'],
                    'title': recipe['title'],
                    'chunk_type': chunk['type'],
                    'cuisine': str(recipe.get('cuisine', 'Unknown')),
                    'prep_time': recipe.get('prep_time'),
                    'cook_time': recipe.get('cook_time'),
                    'servings': recipe.get('servings'),
                    'vegetarian': recipe.get('dietary_info', {}).get('vegetarian', False),
                    'vegan': recipe.get('dietary_info', {}).get('vegan', False),
                    'gluten_free': recipe.get('dietary_info', {}).get('gluten_free', False)
                }))
        
        self.collection.add(
            documents=all_chunks,
            embeddings=all_embeddings,
            metadatas=all_metadatas,
            ids=all_ids
        )
        
        if not self.recipes_data:
            self.set_recipes(recipes)
        
        print(f"Added {len(all_chunks)} chunks from {len(recipes)} recipes")
        return len(all_chunks)
    
    def _create_chunks(self, recipe):
        """Create searchable chunks from recipe data."""
        chunks = []
        
        main_text = f"""Recipe: {recipe['title']}
Description: {recipe.get('description', 'No description')}
Cuisine: {recipe.get('cuisine', 'Unknown')}
Prep Time: {recipe.get('prep_time', 'Unknown')} minutes
Cook Time: {recipe.get('cook_time', 'Unknown')} minutes
Servings: {recipe.get('servings', 'Unknown')}"""
        
        chunks.append({'id': f"{recipe['id']}_main", 'text': main_text.strip(), 'type': 'main', 'recipe_id': recipe['id']})
        
        ingredients_text = f"Ingredients for {recipe['title']}: " + ", ".join(recipe['ingredients'])
        chunks.append({'id': f"{recipe['id']}_ingredients", 'text': ingredients_text, 'type': 'ingredients', 'recipe_id': recipe['id']})
        
        instructions_text = f"Instructions for {recipe['title']}: {recipe['instructions']}"
        chunks.append({'id': f"{recipe['id']}_instructions", 'text': instructions_text, 'type': 'instructions', 'recipe_id': recipe['id']})
        
        return chunks
    
    def _sanitize_metadata(self, metadata):
        """Remove None values from metadata."""
        return {k: v for k, v in metadata.items() if v is not None}
    
    def search(self, query, n_results=5, filters=None):
        """Semantic search for recipes."""
        query_embedding = self.embedding_model.encode(query).tolist()
        
        where_clause = {}
        if filters:
            where_clause = {k: v for k, v in filters.items() if v is not None}
        
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where_clause if where_clause else None
        )
        return results
    
    def search_by_ingredients(self, ingredients_list, dietary_restrictions=None, max_results=5):
        """Search recipes by available ingredients."""
        query = f"Recipe with ingredients: {', '.join(ingredients_list)}"
        
        filters = {}
        if dietary_restrictions:
            for restriction in dietary_restrictions:
                if restriction in ['vegetarian', 'vegan', 'gluten_free']:
                    filters[restriction] = True
        
        results = self.search(query, n_results=max_results * 3, filters=filters)
        
        recipe_scores = {}
        for doc, metadata, distance in zip(results['documents'][0], results['metadatas'][0], results['distances'][0]):
            recipe_id = metadata['recipe_id']
            
            if recipe_id not in recipe_scores and recipe_id in self.recipes_data:
                recipe = self.recipes_data[recipe_id]
                match_score = self._calculate_ingredient_match(recipe['ingredients'], ingredients_list)
                
                recipe_scores[recipe_id] = {
                    'recipe': recipe,
                    'metadata': metadata,
                    'distance': distance,
                    'ingredient_match': match_score,
                    'combined_score': (1 - distance) * 0.7 + match_score * 0.3
                }
        
        sorted_recipes = sorted(recipe_scores.values(), key=lambda x: x['combined_score'], reverse=True)
        return sorted_recipes[:max_results]
    
    def search_by_cuisine(self, cuisine_type, max_results=5):
        """Search recipes by cuisine type."""
        query = f"{cuisine_type} cuisine recipes"
        results = self.search(query, n_results=max_results * 2, filters={'cuisine': cuisine_type})
        return self._process_results(results, max_results)
    
    def search_by_time(self, max_prep_time=None, max_cook_time=None, max_results=5):
        """Search recipes by time constraints."""
        results = self.search("quick and easy recipes", n_results=max_results * 3)
        
        filtered = []
        seen = set()
        
        for doc, metadata, distance in zip(results['documents'][0], results['metadatas'][0], results['distances'][0]):
            recipe_id = metadata['recipe_id']
            
            if recipe_id in seen or recipe_id not in self.recipes_data:
                continue
            
            recipe = self.recipes_data[recipe_id]
            prep_time = recipe.get('prep_time') or 0
            cook_time = recipe.get('cook_time') or 0
            
            if max_prep_time and prep_time > max_prep_time:
                continue
            if max_cook_time and cook_time > max_cook_time:
                continue
            
            filtered.append({'recipe': recipe, 'metadata': metadata, 'distance': distance, 'score': 1 - distance})
            seen.add(recipe_id)
            
            if len(filtered) >= max_results:
                break
        
        return filtered
    
    def search_natural_language(self, query, max_results=5):
        """Search recipes using natural language."""
        results = self.search(query, n_results=max_results * 2)
        return self._process_results(results, max_results)
    
    def get_recommendations(self, user_preferences, max_results=3):
        """Get personalized recipe recommendations."""
        query_parts = []
        filters = {}
        
        if user_preferences.get('favorite_ingredients'):
            query_parts.append(f"recipes with {', '.join(user_preferences['favorite_ingredients'])}")
        
        if user_preferences.get('cuisine_preference'):
            query_parts.append(f"{user_preferences['cuisine_preference']} cuisine")
        
        if user_preferences.get('dietary_restrictions'):
            for restriction in user_preferences['dietary_restrictions']:
                if restriction in ['vegetarian', 'vegan', 'gluten_free']:
                    filters[restriction] = True
        
        query = " ".join(query_parts) if query_parts else "delicious recipes"
        results = self.search(query, n_results=max_results * 2, filters=filters)
        return self._process_results(results, max_results)
    
    def _calculate_ingredient_match(self, recipe_ingredients, available_ingredients):
        """Calculate ingredient match score."""
        recipe_lower = [ing.lower() for ing in recipe_ingredients]
        available_lower = [ing.lower() for ing in available_ingredients]
        
        matches = sum(
            1 for available in available_lower
            for recipe_ing in recipe_lower
            if available in recipe_ing or recipe_ing in available
        )
        
        return matches / len(recipe_ingredients) if recipe_ingredients else 0
    
    def _process_results(self, results, max_results):
        """Process and deduplicate search results."""
        seen = set()
        processed = []
        
        for doc, metadata, distance in zip(results['documents'][0], results['metadatas'][0], results['distances'][0]):
            recipe_id = metadata['recipe_id']
            
            if recipe_id not in seen and recipe_id in self.recipes_data:
                processed.append({
                    'recipe': self.recipes_data[recipe_id],
                    'metadata': metadata,
                    'distance': distance,
                    'score': 1 - distance
                })
                seen.add(recipe_id)
                
                if len(processed) >= max_results:
                    break
        
        return processed
    
    def get_recipe_chunks(self, recipe_id):
        """Get chunks for a specific recipe."""
        if recipe_id in self._chunk_cache:
            return self._chunk_cache[recipe_id]
        
        results = self.collection.get(where={"recipe_id": recipe_id})
        
        chunks = []
        if results and results['documents']:
            for doc, metadata in zip(results['documents'], results['metadatas']):
                chunks.append({'type': metadata.get('chunk_type', 'unknown'), 'text': doc})
        
        return chunks
    
    def get_stats(self):
        """Get collection statistics."""
        return {
            'total_chunks': self.collection.count(),
            'total_recipes': len(self.recipes_data),
            'collection_name': self.collection.name
        }
