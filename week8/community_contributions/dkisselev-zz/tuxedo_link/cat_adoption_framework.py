"""Main framework for Tuxedo Link cat adoption application."""

import logging
import sys
from typing import Optional
from dotenv import load_dotenv

from models.cats import CatProfile, SearchResult
from database.manager import DatabaseManager
from setup_vectordb import VectorDBManager
from setup_metadata_vectordb import MetadataVectorDB
from agents.planning_agent import PlanningAgent
from utils.config import get_db_path, get_vectordb_path

# Color codes for logging
BG_BLUE = '\033[44m'
WHITE = '\033[37m'
RESET = '\033[0m'


def init_logging() -> None:
    """Initialize logging with colored output for the framework."""
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter(
        "[%(asctime)s] [Tuxedo Link] [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    root.addHandler(handler)


class TuxedoLinkFramework:
    """Main framework for Tuxedo Link cat adoption application."""
    
    def __init__(self):
        """Initialize the Tuxedo Link framework."""
        init_logging()
        load_dotenv()
        
        self.log("Initializing Tuxedo Link Framework...")
        
        # Initialize database managers using config
        db_path = get_db_path()
        vectordb_path = get_vectordb_path()
        
        self.db_manager = DatabaseManager(db_path)
        self.vector_db = VectorDBManager(vectordb_path)
        self.metadata_vectordb = MetadataVectorDB("metadata_vectorstore")
        
        # Index colors and breeds from APIs for fuzzy matching
        self._index_metadata()
        
        # Lazy agent initialization
        self.planner: Optional[PlanningAgent] = None
        
        self.log("Tuxedo Link Framework initialized")
    
    def _index_metadata(self) -> None:
        """Index colors and breeds from APIs into metadata vector DB for fuzzy matching."""
        try:
            from agents.petfinder_agent import PetfinderAgent
            from agents.rescuegroups_agent import RescueGroupsAgent
            
            self.log("Indexing colors and breeds for fuzzy matching...")
            
            # Index Petfinder colors and breeds
            try:
                petfinder = PetfinderAgent()
                colors = petfinder.get_valid_colors()
                breeds = petfinder.get_valid_breeds()
                
                if colors:
                    self.metadata_vectordb.index_colors(colors, source="petfinder")
                if breeds:
                    self.metadata_vectordb.index_breeds(breeds, source="petfinder")
            except Exception as e:
                logging.warning(f"Could not index Petfinder metadata: {e}")
            
            # Index RescueGroups colors and breeds
            try:
                rescuegroups = RescueGroupsAgent()
                colors = rescuegroups.get_valid_colors()
                breeds = rescuegroups.get_valid_breeds()
                
                if colors:
                    self.metadata_vectordb.index_colors(colors, source="rescuegroups")
                if breeds:
                    self.metadata_vectordb.index_breeds(breeds, source="rescuegroups")
            except Exception as e:
                logging.warning(f"Could not index RescueGroups metadata: {e}")
            
            stats = self.metadata_vectordb.get_stats()
            self.log(f"✓ Metadata indexed: {stats['colors_count']} colors, {stats['breeds_count']} breeds")
        
        except Exception as e:
            logging.warning(f"Metadata indexing failed: {e}")
    
    def init_agents(self) -> None:
        """Initialize agents lazily on first search request."""
        if not self.planner:
            self.log("Initializing agent pipeline...")
            self.planner = PlanningAgent(
                self.db_manager, 
                self.vector_db,
                self.metadata_vectordb
            )
            self.log("Agent pipeline ready")
    
    def log(self, message: str) -> None:
        """
        Log a message with framework identifier.
        
        Args:
            message: Message to log
        """
        text = BG_BLUE + WHITE + "[Framework] " + message + RESET
        logging.info(text)
    
    def search(self, profile: CatProfile, use_cache: bool = False) -> SearchResult:
        """
        Execute cat adoption search.
        
        This runs the complete pipeline:
        1. Fetch cats from APIs OR load from cache (if use_cache=True)
        2. Deduplicate across sources (if fetching new)
        3. Cache in database with image embeddings (if fetching new)
        4. Update vector database (if fetching new)
        5. Perform hybrid matching (semantic + metadata)
        6. Return ranked results
        
        Args:
            profile: User's cat profile with preferences
            use_cache: If True, use cached data instead of fetching from APIs.
                      This saves API calls during development/testing.
            
        Returns:
            SearchResult with matches and metadata
        """
        self.init_agents()
        return self.planner.search(profile, use_cache=use_cache)
    
    def cleanup_old_data(self, days: int = 30) -> dict:
        """
        Clean up data older than specified days.
        
        Args:
            days: Number of days to keep (default: 30)
            
        Returns:
            Dictionary with cleanup statistics
        """
        self.init_agents()
        return self.planner.cleanup_old_data(days)
    
    def get_stats(self) -> dict:
        """
        Get statistics about the application state.
        
        Returns:
            Dictionary with database and vector DB stats
        """
        cache_stats = self.db_manager.get_cache_stats()
        vector_stats = self.vector_db.get_stats()
        
        return {
            'database': cache_stats,
            'vector_db': vector_stats
        }


if __name__ == "__main__":
    # Test the framework with a real search
    print("\n" + "="*60)
    print("Testing Tuxedo Link Framework")
    print("="*60 + "\n")
    
    framework = TuxedoLinkFramework()
    
    # Create a test profile
    print("Creating test profile...")
    profile = CatProfile(
        user_location="10001",  # New York City
        max_distance=50,
        personality_description="friendly, playful cat good with children",
        age_range=["young", "adult"],
        good_with_children=True
    )
    
    print(f"\nProfile:")
    print(f"  Location: {profile.user_location}")
    print(f"  Distance: {profile.max_distance} miles")
    print(f"  Age: {', '.join(profile.age_range)}")
    print(f"  Personality: {profile.personality_description}")
    print(f"  Good with children: {profile.good_with_children}")
    
    # Run search
    print("\n" + "-"*60)
    print("Running search pipeline...")
    print("-"*60 + "\n")
    
    result = framework.search(profile)
    
    # Display results
    print("\n" + "="*60)
    print("SEARCH RESULTS")
    print("="*60 + "\n")
    
    print(f"Total cats found: {result.total_found}")
    print(f"Sources queried: {', '.join(result.sources_queried)}")
    print(f"Duplicates removed: {result.duplicates_removed}")
    print(f"Matches returned: {len(result.matches)}")
    print(f"Search time: {result.search_time:.2f} seconds")
    
    if result.matches:
        print("\n" + "-"*60)
        print("TOP MATCHES")
        print("-"*60 + "\n")
        
        for i, match in enumerate(result.matches[:5], 1):
            cat = match.cat
            print(f"{i}. {cat.name}")
            print(f"   Breed: {cat.breed}")
            print(f"   Age: {cat.age} | Size: {cat.size} | Gender: {cat.gender}")
            print(f"   Location: {cat.city}, {cat.state}")
            print(f"   Match Score: {match.match_score:.2%}")
            print(f"   Explanation: {match.explanation}")
            print(f"   Source: {cat.source}")
            print(f"   URL: {cat.url}")
            if cat.primary_photo:
                print(f"   Photo: {cat.primary_photo}")
            print()
    else:
        print("\nNo matches found. Try adjusting your search criteria.")
    
    # Show stats
    print("\n" + "="*60)
    print("SYSTEM STATISTICS")
    print("="*60 + "\n")
    
    stats = framework.get_stats()
    print("Database:")
    for key, value in stats['database'].items():
        print(f"  {key}: {value}")
    
    print("\nVector Database:")
    for key, value in stats['vector_db'].items():
        print(f"  {key}: {value}")
    
    print("\n" + "="*60)
    print("Test Complete!")
    print("="*60 + "\n")

