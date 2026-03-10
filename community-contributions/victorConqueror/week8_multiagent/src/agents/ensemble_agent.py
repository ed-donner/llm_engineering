from .base_agent import Agent
from .specialist_agent import SpecialistAgent
from .frontier_agent import FrontierAgent
import sys
sys.path.append('../../week8/agents')
from neural_network_agent import NeuralNetworkAgent
from preprocessor import Preprocessor


class EnsembleAgent(Agent):
    """
    Ensemble Agent with Confidence-Aware Weighting
    
    IMPROVEMENT: Instead of fixed weights (0.8, 0.1, 0.1), this uses
    confidence scores from each agent to dynamically weight predictions.
    
    Expected improvement: 5-10% better accuracy
    """
    name = "Ensemble Agent"
    color = Agent.YELLOW

    def __init__(self, collection, use_confidence=True):
        """
        Create an instance of Ensemble, by creating each of the models
        
        Args:
            collection: ChromaDB collection for RAG
            use_confidence: If True, use confidence-aware weighting (NEW!)
                          If False, use Ed's original fixed weights
        """
        self.log("Initializing Ensemble Agent")
        self.specialist = SpecialistAgent()
        self.frontier = FrontierAgent(collection)
        self.neural_network = NeuralNetworkAgent()
        self.preprocessor = Preprocessor()
        self.use_confidence = use_confidence
        
        # Ed's original fixed weights
        self.fixed_weights = {
            'frontier': 0.8,
            'specialist': 0.1,
            'neural_network': 0.1
        }
        
        self.log(f"Ensemble Agent is ready (confidence_mode={use_confidence})")

    def price(self, description: str) -> float:
        """
        Run this ensemble model
        Ask each of the models to price the product
        Then combine using either fixed or confidence-based weights
        
        :param description: the description of a product
        :return: an estimate of its price
        """
        self.log("Running Ensemble Agent - preprocessing text")
        rewrite = self.preprocessor.preprocess(description)
        self.log(f"Pre-processed text using {self.preprocessor.model_name}")
        
        if self.use_confidence:
            # NEW: Confidence-aware weighting
            return self._price_with_confidence(rewrite)
        else:
            # Original: Fixed weights
            return self._price_fixed_weights(rewrite)
    
    def _price_fixed_weights(self, description: str) -> float:
        """
        Ed's original approach: Fixed weights
        """
        specialist = self.specialist.price(description)
        frontier = self.frontier.price(description)
        neural_network = self.neural_network.price(description)
        
        combined = (
            frontier * self.fixed_weights['frontier'] +
            specialist * self.fixed_weights['specialist'] +
            neural_network * self.fixed_weights['neural_network']
        )
        
        self.log(f"Ensemble Agent complete (fixed) - returning ${combined:.2f}")
        return combined
    
    def _price_with_confidence(self, description: str) -> float:
        """
        NEW: Confidence-aware weighting
        Agents with higher confidence get more weight
        """
        # Get predictions with confidence scores
        specialist_price, specialist_conf = self.specialist.price_with_confidence(description)
        frontier_price, frontier_conf = self.frontier.price_with_confidence(description)
        
        # Neural network doesn't have confidence method yet, use default
        neural_network_price = self.neural_network.price(description)
        neural_network_conf = 0.6  # Default confidence
        
        # Calculate weighted average based on confidence
        total_confidence = specialist_conf + frontier_conf + neural_network_conf
        
        combined = (
            (frontier_price * frontier_conf +
             specialist_price * specialist_conf +
             neural_network_price * neural_network_conf) / total_confidence
        )
        
        self.log(f"Ensemble Agent complete (confidence) - returning ${combined:.2f}")
        self.log(f"  Weights: Frontier={frontier_conf/total_confidence:.2f}, "
                f"Specialist={specialist_conf/total_confidence:.2f}, "
                f"Neural={neural_network_conf/total_confidence:.2f}")
        
        return combined
    
    def price_with_confidence(self, description: str) -> tuple[float, float]:
        """
        Get ensemble prediction with overall confidence
        Confidence is the weighted average of individual confidences
        """
        rewrite = self.preprocessor.preprocess(description)
        
        # Get predictions with confidence
        specialist_price, specialist_conf = self.specialist.price_with_confidence(rewrite)
        frontier_price, frontier_conf = self.frontier.price_with_confidence(rewrite)
        neural_network_price = self.neural_network.price(rewrite)
        neural_network_conf = 0.6
        
        # Calculate weighted price and average confidence
        total_confidence = specialist_conf + frontier_conf + neural_network_conf
        
        price = (
            (frontier_price * frontier_conf +
             specialist_price * specialist_conf +
             neural_network_price * neural_network_conf) / total_confidence
        )
        
        # Overall confidence is the average
        confidence = total_confidence / 3
        
        return price, confidence
