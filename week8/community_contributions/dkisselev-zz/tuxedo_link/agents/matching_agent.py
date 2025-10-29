"""Matching agent for hybrid search (vector + metadata filtering)."""

import os
from typing import List
from dotenv import load_dotenv

from models.cats import Cat, CatProfile, CatMatch
from setup_vectordb import VectorDBManager
from utils.geocoding import calculate_distance
from .agent import Agent, timed


class MatchingAgent(Agent):
    """Agent for matching cats to user preferences using hybrid search."""
    
    name = "Matching Agent"
    color = Agent.BLUE
    
    def __init__(self, vector_db: VectorDBManager):
        """
        Initialize the matching agent.
        
        Args:
            vector_db: Vector database manager
        """
        load_dotenv()
        
        self.vector_db = vector_db
        
        # Load configuration
        self.vector_top_n = int(os.getenv('VECTOR_TOP_N', '50'))
        self.final_limit = int(os.getenv('FINAL_RESULTS_LIMIT', '20'))
        self.semantic_weight = float(os.getenv('SEMANTIC_WEIGHT', '0.6'))
        self.attribute_weight = float(os.getenv('ATTRIBUTE_WEIGHT', '0.4'))
        
        self.log("Matching Agent initialized")
        self.log(f"Config - Vector Top N: {self.vector_top_n}, Final Limit: {self.final_limit}")
        self.log(f"Weights - Semantic: {self.semantic_weight}, Attribute: {self.attribute_weight}")
    
    def _apply_metadata_filters(self, profile: CatProfile) -> dict:
        """
        Build ChromaDB where clause from profile hard constraints.
        
        Args:
            profile: User's cat profile
            
        Returns:
            Dictionary of metadata filters
        """
        filters = []
        
        # Age filter
        if profile.age_range:
            age_conditions = [{"age": age} for age in profile.age_range]
            if len(age_conditions) > 1:
                filters.append({"$or": age_conditions})
            else:
                filters.extend(age_conditions)
        
        # Size filter
        if profile.size:
            size_conditions = [{"size": size} for size in profile.size]
            if len(size_conditions) > 1:
                filters.append({"$or": size_conditions})
            else:
                filters.extend(size_conditions)
        
        # Gender filter
        if profile.gender_preference:
            filters.append({"gender": profile.gender_preference})
        
        # Behavioral filters
        if profile.good_with_children is not None:
            # Filter for cats that are explicitly good with children or unknown
            if profile.good_with_children:
                filters.append({
                    "$or": [
                        {"good_with_children": "True"},
                        {"good_with_children": "unknown"}
                    ]
                })
        
        if profile.good_with_dogs is not None:
            if profile.good_with_dogs:
                filters.append({
                    "$or": [
                        {"good_with_dogs": "True"},
                        {"good_with_dogs": "unknown"}
                    ]
                })
        
        if profile.good_with_cats is not None:
            if profile.good_with_cats:
                filters.append({
                    "$or": [
                        {"good_with_cats": "True"},
                        {"good_with_cats": "unknown"}
                    ]
                })
        
        # Special needs filter
        if not profile.special_needs_ok:
            filters.append({"special_needs": "False"})
        
        # Combine filters with AND logic
        if len(filters) == 0:
            return None
        elif len(filters) == 1:
            return filters[0]
        else:
            return {"$and": filters}
    
    def _calculate_attribute_match_score(self, cat: Cat, profile: CatProfile) -> tuple[float, List[str], List[str]]:
        """
        Calculate how well cat's attributes match profile preferences.
        
        Args:
            cat: Cat to evaluate
            profile: User profile
            
        Returns:
            Tuple of (score, matching_attributes, missing_attributes)
        """
        matching_attrs = []
        missing_attrs = []
        total_checks = 0
        matches = 0
        
        # Age preference
        if profile.age_range:
            total_checks += 1
            if cat.age in profile.age_range:
                matches += 1
                matching_attrs.append(f"Age: {cat.age}")
            else:
                missing_attrs.append(f"Preferred age: {', '.join(profile.age_range)}")
        
        # Size preference
        if profile.size:
            total_checks += 1
            if cat.size in profile.size:
                matches += 1
                matching_attrs.append(f"Size: {cat.size}")
            else:
                missing_attrs.append(f"Preferred size: {', '.join(profile.size)}")
        
        # Gender preference
        if profile.gender_preference:
            total_checks += 1
            if cat.gender == profile.gender_preference:
                matches += 1
                matching_attrs.append(f"Gender: {cat.gender}")
            else:
                missing_attrs.append(f"Preferred gender: {profile.gender_preference}")
        
        # Good with children
        if profile.good_with_children:
            total_checks += 1
            if cat.good_with_children:
                matches += 1
                matching_attrs.append("Good with children")
            elif cat.good_with_children is False:
                missing_attrs.append("Not good with children")
        
        # Good with dogs
        if profile.good_with_dogs:
            total_checks += 1
            if cat.good_with_dogs:
                matches += 1
                matching_attrs.append("Good with dogs")
            elif cat.good_with_dogs is False:
                missing_attrs.append("Not good with dogs")
        
        # Good with cats
        if profile.good_with_cats:
            total_checks += 1
            if cat.good_with_cats:
                matches += 1
                matching_attrs.append("Good with other cats")
            elif cat.good_with_cats is False:
                missing_attrs.append("Not good with other cats")
        
        # Special needs
        if not profile.special_needs_ok and cat.special_needs:
            total_checks += 1
            missing_attrs.append("Has special needs")
        
        # Breed preference
        if profile.preferred_breeds:
            total_checks += 1
            if cat.breed.lower() in [b.lower() for b in profile.preferred_breeds]:
                matches += 1
                matching_attrs.append(f"Breed: {cat.breed}")
            else:
                missing_attrs.append(f"Preferred breeds: {', '.join(profile.preferred_breeds)}")
        
        # Calculate score
        if total_checks == 0:
            return 0.5, matching_attrs, missing_attrs  # Neutral if no preferences
        
        score = matches / total_checks
        return score, matching_attrs, missing_attrs
    
    def _filter_by_distance(self, cats_data: dict, profile: CatProfile) -> List[tuple[Cat, float, dict]]:
        """
        Filter cats by distance and prepare for ranking.
        
        Args:
            cats_data: Results from vector search
            profile: User profile
            
        Returns:
            List of (cat, vector_similarity, metadata) tuples
        """
        results = []
        
        ids = cats_data['ids'][0]
        distances = cats_data['distances'][0]
        metadatas = cats_data['metadatas'][0]
        
        for i, cat_id in enumerate(ids):
            metadata = metadatas[i]
            
            # Convert distance to similarity (ChromaDB returns L2 distance)
            # Lower distance = higher similarity
            vector_similarity = 1.0 / (1.0 + distances[i])
            
            # Check distance constraint
            if profile.user_latitude and profile.user_longitude:
                cat_lat = metadata.get('latitude')
                cat_lon = metadata.get('longitude')
                
                if cat_lat and cat_lon and cat_lat != '' and cat_lon != '':
                    try:
                        cat_lat = float(cat_lat)
                        cat_lon = float(cat_lon)
                        distance = calculate_distance(
                            profile.user_latitude, 
                            profile.user_longitude,
                            cat_lat,
                            cat_lon
                        )
                        
                        max_dist = profile.max_distance or 100
                        if distance > max_dist:
                            self.log(f"DEBUG: Filtered out {metadata['name']} - {distance:.1f} miles away (max: {max_dist})")
                            continue  # Skip this cat, too far away
                    except (ValueError, TypeError):
                        pass  # Keep cat if coordinates invalid
            
            # Reconstruct Cat from metadata
            cat = Cat(
                id=metadata['id'],
                name=metadata['name'],
                age=metadata['age'],
                size=metadata['size'],
                gender=metadata['gender'],
                breed=metadata['breed'],
                city=metadata.get('city', ''),
                state=metadata.get('state', ''),
                zip_code=metadata.get('zip_code', ''),
                latitude=float(metadata['latitude']) if metadata.get('latitude') and metadata['latitude'] != '' else None,
                longitude=float(metadata['longitude']) if metadata.get('longitude') and metadata['longitude'] != '' else None,
                organization_name=metadata['organization'],
                source=metadata['source'],
                url=metadata['url'],
                primary_photo=metadata.get('primary_photo', ''),
                description='',  # Not stored in metadata
                good_with_children=metadata.get('good_with_children') == 'True' if metadata.get('good_with_children') != 'unknown' else None,
                good_with_dogs=metadata.get('good_with_dogs') == 'True' if metadata.get('good_with_dogs') != 'unknown' else None,
                good_with_cats=metadata.get('good_with_cats') == 'True' if metadata.get('good_with_cats') != 'unknown' else None,
                special_needs=metadata.get('special_needs') == 'True',
            )
            
            results.append((cat, vector_similarity, metadata))
        
        return results
    
    def _create_explanation(self, cat: Cat, match_score: float, vector_sim: float, attr_score: float, matching_attrs: List[str]) -> str:
        """
        Create human-readable explanation of match.
        
        Args:
            cat: Matched cat
            match_score: Overall match score
            vector_sim: Vector similarity score
            attr_score: Attribute match score
            matching_attrs: List of matching attributes
            
        Returns:
            Explanation string
        """
        explanation_parts = []
        
        # Overall match quality
        if match_score >= 0.8:
            explanation_parts.append(f"{cat.name} is an excellent match!")
        elif match_score >= 0.6:
            explanation_parts.append(f"{cat.name} is a good match.")
        else:
            explanation_parts.append(f"{cat.name} might be a match.")
        
        # Personality match
        if vector_sim >= 0.7:
            explanation_parts.append("Personality description strongly matches your preferences.")
        elif vector_sim >= 0.5:
            explanation_parts.append("Personality description aligns with your preferences.")
        
        # Matching attributes
        if matching_attrs:
            top_matches = matching_attrs[:3]  # Show top 3
            explanation_parts.append("Matches: " + ", ".join(top_matches))
        
        return " ".join(explanation_parts)
    
    @timed
    def match(self, profile: CatProfile) -> List[CatMatch]:
        """
        Find cats that match the user's profile using hybrid search.
        
        Strategy:
        1. Vector search for semantic similarity (top N)
        2. Filter by hard constraints (metadata)
        3. Rank by weighted combination of semantic + attribute scores
        4. Return top matches with explanations
        
        Args:
            profile: User's cat profile
            
        Returns:
            List of CatMatch objects, sorted by match score
        """
        self.log(f"Starting hybrid search with profile: {profile.personality_description[:50]}...")
        
        # Step 1: Vector search
        query = profile.personality_description or "friendly, loving cat"
        where_clause = self._apply_metadata_filters(profile)
        
        self.log(f"Vector search for top {self.vector_top_n} semantic matches")
        if where_clause:
            self.log(f"Applying metadata filters: {where_clause}")
        
        results = self.vector_db.search(
            query=query,
            n_results=self.vector_top_n,
            where=where_clause
        )
        
        if not results['ids'][0]:
            self.log("No results found matching criteria")
            return []
        
        self.log(f"Vector search returned {len(results['ids'][0])} candidates")
        
        # Step 2: Filter by distance (if applicable)
        candidates = self._filter_by_distance(results, profile)
        
        # Step 3: Calculate attribute scores and rank
        self.log("Calculating attribute match scores and ranking")
        matches = []
        
        for cat, vector_similarity, metadata in candidates:
            # Calculate attribute match score
            attr_score, matching_attrs, missing_attrs = self._calculate_attribute_match_score(cat, profile)
            
            # Calculate weighted final score
            final_score = (
                self.semantic_weight * vector_similarity +
                self.attribute_weight * attr_score
            )
            
            # Create explanation
            explanation = self._create_explanation(cat, final_score, vector_similarity, attr_score, matching_attrs)
            
            # Create match object
            match = CatMatch(
                cat=cat,
                match_score=final_score,
                vector_similarity=vector_similarity,
                attribute_match_score=attr_score,
                explanation=explanation,
                matching_attributes=matching_attrs,
                missing_attributes=missing_attrs
            )
            
            matches.append(match)
        
        # Sort by match score
        matches.sort(key=lambda m: m.match_score, reverse=True)
        
        # Return top matches
        top_matches = matches[:self.final_limit]
        
        self.log(f"Returning top {len(top_matches)} matches")
        if top_matches:
            self.log(f"Best match: {top_matches[0].cat.name} (score: {top_matches[0].match_score:.2f})")
        
        return top_matches

