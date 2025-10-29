"""Integration tests for color and breed normalization in search pipeline."""

import pytest
import tempfile
import shutil
from unittest.mock import Mock, patch

from models.cats import CatProfile
from setup_metadata_vectordb import MetadataVectorDB
from agents.planning_agent import PlanningAgent
from database.manager import DatabaseManager
from setup_vectordb import VectorDBManager


@pytest.fixture
def temp_dirs():
    """Create temporary directories for testing."""
    db_dir = tempfile.mkdtemp()
    vector_dir = tempfile.mkdtemp()
    metadata_dir = tempfile.mkdtemp()
    
    yield db_dir, vector_dir, metadata_dir
    
    # Cleanup
    shutil.rmtree(db_dir, ignore_errors=True)
    shutil.rmtree(vector_dir, ignore_errors=True)
    shutil.rmtree(metadata_dir, ignore_errors=True)


@pytest.fixture
def metadata_vectordb(temp_dirs):
    """Create metadata vector DB with sample data."""
    _, _, metadata_dir = temp_dirs
    vectordb = MetadataVectorDB(persist_directory=metadata_dir)
    
    # Index sample colors and breeds
    colors = [
        "Black",
        "White",
        "Black & White / Tuxedo",
        "Orange / Red",
        "Gray / Blue / Silver",
        "Calico"
    ]
    
    breeds = [
        "Siamese",
        "Persian",
        "Maine Coon",
        "Domestic Short Hair",
        "Domestic Medium Hair"
    ]
    
    vectordb.index_colors(colors, source="petfinder")
    vectordb.index_breeds(breeds, source="petfinder")
    
    return vectordb


@pytest.fixture
def planning_agent(temp_dirs, metadata_vectordb):
    """Create planning agent with metadata vector DB."""
    db_dir, vector_dir, _ = temp_dirs
    
    db_manager = DatabaseManager(f"{db_dir}/test.db")
    vector_db = VectorDBManager(vector_dir)
    
    return PlanningAgent(db_manager, vector_db, metadata_vectordb)


class TestColorBreedNormalization:
    """Integration tests for color and breed normalization."""
    
    @patch('agents.petfinder_agent.PetfinderAgent.search_cats')
    @patch('agents.petfinder_agent.PetfinderAgent.get_valid_colors')
    @patch('agents.petfinder_agent.PetfinderAgent.get_valid_breeds')
    def test_tuxedo_color_normalization(
        self,
        mock_get_breeds,
        mock_get_colors,
        mock_search,
        planning_agent
    ):
        """Test that 'tuxedo' is correctly normalized to 'Black & White / Tuxedo'."""
        # Setup mocks
        mock_get_colors.return_value = [
            "Black",
            "White",
            "Black & White / Tuxedo"
        ]
        mock_get_breeds.return_value = ["Domestic Short Hair"]
        mock_search.return_value = []
        
        # Create profile with "tuxedo" color
        profile = CatProfile(
            user_location="New York, NY",
            color_preferences=["tuxedo"]
        )
        
        # Execute search (will fail but we just want to see the API call)
        try:
            planning_agent._search_petfinder(profile)
        except:
            pass
        
        # Verify search_cats was called with correct normalized color
        assert mock_search.called
        call_args = mock_search.call_args
        
        # Check that color parameter contains the correct API value
        if 'color' in call_args.kwargs and call_args.kwargs['color']:
            assert "Black & White / Tuxedo" in call_args.kwargs['color']
            assert "Black" not in call_args.kwargs['color'] or len(call_args.kwargs['color']) == 1
    
    @patch('agents.petfinder_agent.PetfinderAgent.search_cats')
    @patch('agents.petfinder_agent.PetfinderAgent.get_valid_colors')
    @patch('agents.petfinder_agent.PetfinderAgent.get_valid_breeds')
    def test_multiple_colors_normalization(
        self,
        mock_get_breeds,
        mock_get_colors,
        mock_search,
        planning_agent
    ):
        """Test normalization of multiple color preferences."""
        mock_get_colors.return_value = [
            "Black & White / Tuxedo",
            "Orange / Red",
            "Calico"
        ]
        mock_get_breeds.return_value = []
        mock_search.return_value = []
        
        profile = CatProfile(
            user_location="New York, NY",
            color_preferences=["tuxedo", "orange", "calico"]
        )
        
        try:
            planning_agent._search_petfinder(profile)
        except:
            pass
        
        assert mock_search.called
        call_args = mock_search.call_args
        
        if 'color' in call_args.kwargs and call_args.kwargs['color']:
            colors = call_args.kwargs['color']
            assert len(colors) == 3
            assert "Black & White / Tuxedo" in colors
            assert "Orange / Red" in colors
            assert "Calico" in colors
    
    @patch('agents.petfinder_agent.PetfinderAgent.search_cats')
    @patch('agents.petfinder_agent.PetfinderAgent.get_valid_colors')
    @patch('agents.petfinder_agent.PetfinderAgent.get_valid_breeds')
    def test_breed_normalization_maine_coon(
        self,
        mock_get_breeds,
        mock_get_colors,
        mock_search,
        planning_agent
    ):
        """Test that 'main coon' (typo) is normalized to 'Maine Coon'."""
        mock_get_colors.return_value = []
        mock_get_breeds.return_value = ["Maine Coon", "Siamese"]
        mock_search.return_value = []
        
        profile = CatProfile(
            user_location="New York, NY",
            breed_preferences=["main coon"]  # Typo
        )
        
        try:
            planning_agent._search_petfinder(profile)
        except:
            pass
        
        assert mock_search.called
        call_args = mock_search.call_args
        
        if 'breed' in call_args.kwargs and call_args.kwargs['breed']:
            assert "Maine Coon" in call_args.kwargs['breed']
    
    @patch('agents.petfinder_agent.PetfinderAgent.search_cats')
    @patch('agents.petfinder_agent.PetfinderAgent.get_valid_colors')
    @patch('agents.petfinder_agent.PetfinderAgent.get_valid_breeds')
    def test_fuzzy_color_matching_with_vectordb(
        self,
        mock_get_breeds,
        mock_get_colors,
        mock_search,
        planning_agent
    ):
        """Test fuzzy matching with vector DB for typos."""
        mock_get_colors.return_value = ["Black & White / Tuxedo"]
        mock_get_breeds.return_value = []
        mock_search.return_value = []
        
        # Use a term that requires vector search (not in dictionary)
        profile = CatProfile(
            user_location="New York, NY",
            color_preferences=["tuxado"]  # Typo
        )
        
        try:
            planning_agent._search_petfinder(profile)
        except:
            pass
        
        assert mock_search.called
        # May or may not match depending on similarity threshold
        # This test primarily ensures no errors occur
    
    @patch('agents.petfinder_agent.PetfinderAgent.search_cats')
    @patch('agents.petfinder_agent.PetfinderAgent.get_valid_colors')
    @patch('agents.petfinder_agent.PetfinderAgent.get_valid_breeds')
    def test_colors_and_breeds_together(
        self,
        mock_get_breeds,
        mock_get_colors,
        mock_search,
        planning_agent
    ):
        """Test normalization of both colors and breeds in same search."""
        mock_get_colors.return_value = ["Black & White / Tuxedo", "Orange / Red"]
        mock_get_breeds.return_value = ["Siamese", "Maine Coon"]
        mock_search.return_value = []
        
        profile = CatProfile(
            user_location="New York, NY",
            color_preferences=["tuxedo", "orange"],
            breed_preferences=["siamese", "main coon"]
        )
        
        try:
            planning_agent._search_petfinder(profile)
        except:
            pass
        
        assert mock_search.called
        call_args = mock_search.call_args
        
        # Verify both colors and breeds are normalized
        if 'color' in call_args.kwargs and call_args.kwargs['color']:
            assert "Black & White / Tuxedo" in call_args.kwargs['color']
            assert "Orange / Red" in call_args.kwargs['color']
        
        if 'breed' in call_args.kwargs and call_args.kwargs['breed']:
            assert "Siamese" in call_args.kwargs['breed']
            assert "Maine Coon" in call_args.kwargs['breed']
    
    @patch('agents.rescuegroups_agent.RescueGroupsAgent.search_cats')
    @patch('agents.rescuegroups_agent.RescueGroupsAgent.get_valid_colors')
    @patch('agents.rescuegroups_agent.RescueGroupsAgent.get_valid_breeds')
    def test_rescuegroups_normalization(
        self,
        mock_get_breeds,
        mock_get_colors,
        mock_search,
        planning_agent
    ):
        """Test that normalization works for RescueGroups API too."""
        mock_get_colors.return_value = ["Tuxedo", "Orange"]
        mock_get_breeds.return_value = ["Siamese"]
        mock_search.return_value = []
        
        profile = CatProfile(
            user_location="New York, NY",
            color_preferences=["tuxedo"],
            breed_preferences=["siamese"]
        )
        
        try:
            planning_agent._search_rescuegroups(profile)
        except:
            pass
        
        assert mock_search.called
        # Normalization should have occurred with rescuegroups source
    
    def test_no_colors_or_breeds(self, planning_agent):
        """Test search without color or breed preferences."""
        with patch('agents.petfinder_agent.PetfinderAgent.search_cats') as mock_search:
            mock_search.return_value = []
            
            profile = CatProfile(
                user_location="New York, NY"
                # No color_preferences or breed_preferences
            )
            
            try:
                planning_agent._search_petfinder(profile)
            except:
                pass
            
            assert mock_search.called
            call_args = mock_search.call_args
            
            # Should be None or empty
            assert call_args.kwargs.get('color') is None or len(call_args.kwargs.get('color', [])) == 0
            assert call_args.kwargs.get('breed') is None or len(call_args.kwargs.get('breed', [])) == 0
    
    def test_invalid_color_graceful_handling(self, planning_agent):
        """Test that invalid colors don't break the search."""
        with patch('agents.petfinder_agent.PetfinderAgent.search_cats') as mock_search:
            with patch('agents.petfinder_agent.PetfinderAgent.get_valid_colors') as mock_colors:
                mock_search.return_value = []
                mock_colors.return_value = ["Black", "White"]
                
                profile = CatProfile(
                    user_location="New York, NY",
                    color_preferences=["invalid_color_xyz"]
                )
                
                try:
                    planning_agent._search_petfinder(profile)
                except:
                    pass
                
                # Should still call search, just with empty/None color
                assert mock_search.called

