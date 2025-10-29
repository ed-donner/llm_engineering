"""Deduplication agent for identifying and managing duplicate cat listings."""

import os
from typing import List, Tuple, Optional
from dotenv import load_dotenv
import numpy as np

from models.cats import Cat
from database.manager import DatabaseManager
from utils.deduplication import (
    create_fingerprint,
    calculate_text_similarity,
    calculate_composite_score
)
from utils.image_utils import generate_image_embedding, calculate_image_similarity
from .agent import Agent, timed


class DeduplicationAgent(Agent):
    """Agent for deduplicating cat listings across multiple sources."""
    
    name = "Deduplication Agent"
    color = Agent.YELLOW
    
    def __init__(self, db_manager: DatabaseManager):
        """
        Initialize the deduplication agent.
        
        Args:
            db_manager: Database manager instance
        """
        load_dotenv()
        
        self.db_manager = db_manager
        
        # Load thresholds from environment
        self.name_threshold = float(os.getenv('DEDUP_NAME_SIMILARITY_THRESHOLD', '0.8'))
        self.desc_threshold = float(os.getenv('DEDUP_DESCRIPTION_SIMILARITY_THRESHOLD', '0.7'))
        self.image_threshold = float(os.getenv('DEDUP_IMAGE_SIMILARITY_THRESHOLD', '0.9'))
        self.composite_threshold = float(os.getenv('DEDUP_COMPOSITE_THRESHOLD', '0.85'))
        
        self.log("Deduplication Agent initialized")
        self.log(f"Thresholds - Name: {self.name_threshold}, Desc: {self.desc_threshold}, "
                f"Image: {self.image_threshold}, Composite: {self.composite_threshold}")
    
    def _get_image_embedding(self, cat: Cat) -> Optional[np.ndarray]:
        """
        Get or generate image embedding for a cat.
        
        Args:
            cat: Cat object
            
        Returns:
            Image embedding or None if unavailable
        """
        if not cat.primary_photo:
            return None
        
        try:
            embedding = generate_image_embedding(cat.primary_photo)
            return embedding
        except Exception as e:
            self.log_warning(f"Failed to generate image embedding for {cat.name}: {e}")
            return None
    
    def _compare_cats(self, cat1: Cat, cat2: Cat, 
                     emb1: Optional[np.ndarray], 
                     emb2: Optional[np.ndarray]) -> Tuple[float, dict]:
        """
        Compare two cats and return composite similarity score with details.
        
        Args:
            cat1: First cat
            cat2: Second cat
            emb1: Image embedding for cat1
            emb2: Image embedding for cat2
            
        Returns:
            Tuple of (composite_score, details_dict)
        """
        # Text similarity
        name_sim, desc_sim = calculate_text_similarity(cat1, cat2)
        
        # Image similarity
        image_sim = 0.0
        if emb1 is not None and emb2 is not None:
            image_sim = calculate_image_similarity(emb1, emb2)
        
        # Composite score
        composite = calculate_composite_score(
            name_similarity=name_sim,
            description_similarity=desc_sim,
            image_similarity=image_sim,
            name_weight=0.4,
            description_weight=0.3,
            image_weight=0.3
        )
        
        details = {
            'name_similarity': name_sim,
            'description_similarity': desc_sim,
            'image_similarity': image_sim,
            'composite_score': composite
        }
        
        return composite, details
    
    @timed
    def process_cat(self, cat: Cat) -> Tuple[Cat, bool]:
        """
        Process a single cat for deduplication.
        
        Checks if the cat is a duplicate of an existing cat in the database.
        If it's a duplicate, marks it as such and returns the canonical cat.
        If it's unique, caches it in the database.
        
        Args:
            cat: Cat to process
            
        Returns:
            Tuple of (canonical_cat, is_duplicate)
        """
        # Generate fingerprint
        cat.fingerprint = create_fingerprint(cat)
        
        # Check database for cats with same fingerprint
        candidates = self.db_manager.get_cats_by_fingerprint(cat.fingerprint)
        
        if not candidates:
            # No candidates, this is unique
            # Generate and cache image embedding
            embedding = self._get_image_embedding(cat)
            self.db_manager.cache_cat(cat, embedding)
            return cat, False
        
        self.log(f"Found {len(candidates)} potential duplicates for {cat.name}")
        
        # Get embedding for new cat
        new_embedding = self._get_image_embedding(cat)
        
        # Compare with each candidate
        best_match = None
        best_score = 0.0
        best_details = None
        
        for candidate_cat, candidate_embedding in candidates:
            score, details = self._compare_cats(cat, candidate_cat, new_embedding, candidate_embedding)
            
            self.log(f"Comparing with {candidate_cat.name} (ID: {candidate_cat.id}): "
                    f"name={details['name_similarity']:.2f}, "
                    f"desc={details['description_similarity']:.2f}, "
                    f"image={details['image_similarity']:.2f}, "
                    f"composite={score:.2f}")
            
            if score > best_score:
                best_score = score
                best_match = candidate_cat
                best_details = details
        
        # Check if best match exceeds threshold
        if best_match and best_score >= self.composite_threshold:
            self.log(f"DUPLICATE DETECTED: {cat.name} is duplicate of {best_match.name} "
                    f"(score: {best_score:.2f})")
            
            # Mark as duplicate in database
            self.db_manager.mark_as_duplicate(cat.id, best_match.id)
            
            return best_match, True
        
        # Not a duplicate, cache it
        self.log(f"UNIQUE: {cat.name} is not a duplicate (best score: {best_score:.2f})")
        self.db_manager.cache_cat(cat, new_embedding)
        
        return cat, False
    
    @timed
    def deduplicate_batch(self, cats: List[Cat]) -> List[Cat]:
        """
        Process a batch of cats for deduplication.
        
        Args:
            cats: List of cats to process
            
        Returns:
            List of unique cats (duplicates removed)
        """
        self.log(f"Deduplicating batch of {len(cats)} cats")
        
        unique_cats = []
        duplicate_count = 0
        
        for cat in cats:
            try:
                canonical_cat, is_duplicate = self.process_cat(cat)
                
                if not is_duplicate:
                    unique_cats.append(canonical_cat)
                else:
                    duplicate_count += 1
                    # Optionally include canonical if not already in list
                    if canonical_cat not in unique_cats:
                        unique_cats.append(canonical_cat)
                
            except Exception as e:
                self.log_error(f"Error processing cat {cat.name}: {e}")
                # Include it anyway to avoid losing data
                unique_cats.append(cat)
        
        self.log(f"Deduplication complete: {len(unique_cats)} unique, {duplicate_count} duplicates")
        
        return unique_cats
    
    def get_duplicate_report(self) -> dict:
        """
        Generate a report of duplicate statistics.
        
        Returns:
            Dictionary with duplicate statistics
        """
        stats = self.db_manager.get_cache_stats()
        
        return {
            'total_unique': stats['total_unique'],
            'total_duplicates': stats['total_duplicates'],
            'deduplication_rate': stats['total_duplicates'] / (stats['total_unique'] + stats['total_duplicates']) 
                                 if (stats['total_unique'] + stats['total_duplicates']) > 0 else 0,
            'by_source': stats['by_source']
        }

