"""Planning agent for orchestrating the cat adoption search pipeline."""

import threading
from typing import List
from concurrent.futures import ThreadPoolExecutor, as_completed

from models.cats import Cat, CatProfile, CatMatch, SearchResult
from database.manager import DatabaseManager
from setup_vectordb import VectorDBManager
from setup_metadata_vectordb import MetadataVectorDB
from .agent import Agent, timed
from .petfinder_agent import PetfinderAgent
from .rescuegroups_agent import RescueGroupsAgent
from .deduplication_agent import DeduplicationAgent
from .matching_agent import MatchingAgent


class PlanningAgent(Agent):
    """Agent for orchestrating the complete cat adoption search pipeline."""
    
    name = "Planning Agent"
    color = Agent.WHITE
    
    def __init__(
        self, 
        db_manager: DatabaseManager, 
        vector_db: VectorDBManager,
        metadata_vectordb: MetadataVectorDB = None
    ):
        """
        Initialize the planning agent.
        
        Args:
            db_manager: Database manager instance
            vector_db: Vector database manager instance
            metadata_vectordb: Optional metadata vector DB for color/breed fuzzy matching
        """
        self.log("Planning Agent initializing...")
        
        # Initialize all agents
        self.petfinder = PetfinderAgent()
        self.rescuegroups = RescueGroupsAgent()
        self.deduplication = DeduplicationAgent(db_manager)
        self.matching = MatchingAgent(vector_db)
        
        self.db_manager = db_manager
        self.vector_db = vector_db
        self.metadata_vectordb = metadata_vectordb
        
        self.log("Planning Agent ready")
    
    def _search_petfinder(self, profile: CatProfile) -> List[Cat]:
        """
        Search Petfinder with the given profile.
        
        Args:
            profile: User's cat profile
            
        Returns:
            List of cats from Petfinder
        """
        try:
            # Normalize colors to valid Petfinder API values (3-tier: dict + vector + fallback)
            api_colors = None
            if profile.color_preferences:
                from utils.color_mapping import normalize_user_colors
                valid_colors = self.petfinder.get_valid_colors()
                api_colors = normalize_user_colors(
                    profile.color_preferences, 
                    valid_colors,
                    vectordb=self.metadata_vectordb,
                    source="petfinder"
                )
                
                if api_colors:
                    self.log(f"✓ Colors: {profile.color_preferences} → {api_colors}")
                else:
                    self.log(f"⚠️ Could not map colors {profile.color_preferences}")
            
            # Normalize breeds to valid Petfinder API values (3-tier: dict + vector + fallback)
            api_breeds = None
            if profile.preferred_breeds:
                from utils.breed_mapping import normalize_user_breeds
                valid_breeds = self.petfinder.get_valid_breeds()
                api_breeds = normalize_user_breeds(
                    profile.preferred_breeds,
                    valid_breeds,
                    vectordb=self.metadata_vectordb,
                    source="petfinder"
                )
                
                if api_breeds:
                    self.log(f"✓ Breeds: {profile.preferred_breeds} → {api_breeds}")
                else:
                    self.log(f"⚠️ Could not map breeds {profile.preferred_breeds}")
            
            return self.petfinder.search_cats(
                location=profile.user_location,
                distance=profile.max_distance or 100,
                age=profile.age_range,
                size=profile.size,
                gender=profile.gender_preference,
                color=api_colors,
                breed=api_breeds,
                good_with_children=profile.good_with_children,
                good_with_dogs=profile.good_with_dogs,
                good_with_cats=profile.good_with_cats,
                limit=100
            )
        except Exception as e:
            self.log_error(f"Petfinder search failed: {e}")
            return []
    
    def _search_rescuegroups(self, profile: CatProfile) -> List[Cat]:
        """
        Search RescueGroups with the given profile.
        
        Args:
            profile: User's cat profile
            
        Returns:
            List of cats from RescueGroups
        """
        try:
            # Normalize colors to valid RescueGroups API values (3-tier: dict + vector + fallback)
            api_colors = None
            if profile.color_preferences:
                from utils.color_mapping import normalize_user_colors
                valid_colors = self.rescuegroups.get_valid_colors()
                api_colors = normalize_user_colors(
                    profile.color_preferences,
                    valid_colors,
                    vectordb=self.metadata_vectordb,
                    source="rescuegroups"
                )
                
                if api_colors:
                    self.log(f"✓ Colors: {profile.color_preferences} → {api_colors}")
                else:
                    self.log(f"⚠️ Could not map colors {profile.color_preferences}")
            
            # Normalize breeds to valid RescueGroups API values (3-tier: dict + vector + fallback)
            api_breeds = None
            if profile.preferred_breeds:
                from utils.breed_mapping import normalize_user_breeds
                valid_breeds = self.rescuegroups.get_valid_breeds()
                api_breeds = normalize_user_breeds(
                    profile.preferred_breeds,
                    valid_breeds,
                    vectordb=self.metadata_vectordb,
                    source="rescuegroups"
                )
                
                if api_breeds:
                    self.log(f"✓ Breeds: {profile.preferred_breeds} → {api_breeds}")
                else:
                    self.log(f"⚠️ Could not map breeds {profile.preferred_breeds}")
            
            return self.rescuegroups.search_cats(
                location=profile.user_location,
                distance=profile.max_distance or 100,
                age=profile.age_range,
                size=profile.size,
                gender=profile.gender_preference,
                color=api_colors,
                breed=api_breeds,
                good_with_children=profile.good_with_children,
                good_with_dogs=profile.good_with_dogs,
                good_with_cats=profile.good_with_cats,
                limit=100
            )
        except Exception as e:
            self.log_error(f"RescueGroups search failed: {e}")
            return []
    
    @timed
    def fetch_cats(self, profile: CatProfile) -> List[Cat]:
        """
        Fetch cats from all sources in parallel.
        
        Args:
            profile: User's cat profile
            
        Returns:
            Combined list of cats from all sources
        """
        self.log("Fetching cats from all sources in parallel...")
        self.log(f"DEBUG: Profile location={profile.user_location}, distance={profile.max_distance}, colors={profile.color_preferences}, age={profile.age_range}")
        
        all_cats = []
        sources_queried = []
        
        # Execute searches in parallel
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = {
                executor.submit(self._search_petfinder, profile): 'petfinder',
                executor.submit(self._search_rescuegroups, profile): 'rescuegroups'
            }
            
            for future in as_completed(futures):
                source = futures[future]
                try:
                    cats = future.result()
                    all_cats.extend(cats)
                    sources_queried.append(source)
                    self.log(f"DEBUG: ✓ Received {len(cats)} cats from {source}")
                except Exception as e:
                    self.log_error(f"Failed to fetch from {source}: {e}")
        
        self.log(f"DEBUG: Total cats fetched: {len(all_cats)} from {len(sources_queried)} sources")
        return all_cats, sources_queried
    
    @timed
    def deduplicate_and_cache(self, cats: List[Cat]) -> List[Cat]:
        """
        Deduplicate cats and cache them in the database.
        
        Args:
            cats: List of cats to process
            
        Returns:
            List of unique cats
        """
        self.log(f"Deduplicating {len(cats)} cats...")
        
        unique_cats = self.deduplication.deduplicate_batch(cats)
        
        self.log(f"Deduplication complete: {len(unique_cats)} unique cats")
        return unique_cats
    
    @timed
    def update_vector_db(self, cats: List[Cat]) -> None:
        """
        Update vector database with new cats.
        
        Args:
            cats: List of cats to add/update
        """
        self.log(f"Updating vector database with {len(cats)} cats...")
        
        try:
            self.vector_db.add_cats_batch(cats)
            self.log("Vector database updated successfully")
        except Exception as e:
            self.log_error(f"Failed to update vector database: {e}")
    
    @timed
    def search(self, profile: CatProfile, use_cache: bool = False) -> SearchResult:
        """
        Execute the complete search pipeline.
        
        Pipeline:
        1. Fetch cats from Petfinder and RescueGroups in parallel (or use cache)
        2. Deduplicate across sources and cache in database
        3. Update vector database with new/updated cats
        4. Use matching agent to find best matches
        5. Return search results
        
        Args:
            profile: User's cat profile
            use_cache: If True, use cached cats instead of fetching from APIs
            
        Returns:
            SearchResult with matches and metadata
        """
        import time
        start_time = time.time()
        
        self.log("=" * 50)
        self.log("STARTING CAT ADOPTION SEARCH PIPELINE")
        if use_cache:
            self.log("🔄 CACHE MODE: Using existing cached data")
        self.log("=" * 50)
        
        # Step 1: Fetch from sources or use cache
        if use_cache:
            self.log("Loading cats from cache...")
            all_cats = self.db_manager.get_all_cached_cats(exclude_duplicates=True)
            sources_queried = ['cache']
            total_found = len(all_cats)
            unique_cats = all_cats
            duplicates_removed = 0
            
            if not all_cats:
                self.log("No cached cats found. Run without use_cache=True first.")
                return SearchResult(
                    matches=[],
                    total_found=0,
                    search_profile=profile,
                    search_time=time.time() - start_time,
                    sources_queried=['cache'],
                    duplicates_removed=0
                )
            
            self.log(f"Loaded {len(all_cats)} cats from cache")
        else:
            all_cats, sources_queried = self.fetch_cats(profile)
            total_found = len(all_cats)
            
            if not all_cats:
                self.log("No cats found matching criteria")
                return SearchResult(
                    matches=[],
                    total_found=0,
                    search_profile=profile,
                    search_time=time.time() - start_time,
                    sources_queried=sources_queried,
                    duplicates_removed=0
                )
            
            # Step 2: Deduplicate and cache
            unique_cats = self.deduplicate_and_cache(all_cats)
            duplicates_removed = total_found - len(unique_cats)
            
            # Step 3: Update vector database
            self.update_vector_db(unique_cats)
        
        # Step 4: Find matches using hybrid search
        self.log("Finding best matches using hybrid search...")
        matches = self.matching.match(profile)
        
        # Calculate search time
        search_time = time.time() - start_time
        
        # Create result
        result = SearchResult(
            matches=matches,
            total_found=total_found,
            search_profile=profile,
            search_time=search_time,
            sources_queried=sources_queried,
            duplicates_removed=duplicates_removed
        )
        
        self.log("=" * 50)
        self.log(f"SEARCH COMPLETE - Found {len(matches)} matches in {search_time:.2f}s")
        self.log("=" * 50)
        
        return result
    
    def cleanup_old_data(self, days: int = 30) -> dict:
        """
        Clean up old cached data.
        
        Args:
            days: Number of days to keep
            
        Returns:
            Dictionary with cleanup stats
        """
        self.log(f"Cleaning up cats older than {days} days...")
        
        # Clean SQLite cache
        removed = self.db_manager.cleanup_old_cats(days)
        
        # Note: ChromaDB cleanup would require tracking IDs separately
        # For now, we rely on the database as source of truth
        
        self.log(f"Cleanup complete: removed {removed} old cats")
        
        return {
            'cats_removed': removed,
            'days_threshold': days
        }

