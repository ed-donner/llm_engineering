"""
Knowledge Graph data models
"""
from dataclasses import dataclass, field
from typing import List, Dict, Set
from datetime import datetime

@dataclass
class KnowledgeNode:
    """Represents a concept or entity in the knowledge graph"""
    id: str
    name: str
    node_type: str  # 'document', 'concept', 'entity', 'topic'
    description: str = ""
    metadata: Dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    
    def __str__(self):
        return f"{self.node_type.capitalize()}: {self.name}"

@dataclass
class KnowledgeEdge:
    """Represents a relationship between nodes"""
    source_id: str
    target_id: str
    relationship: str  # 'related_to', 'cites', 'contains', 'similar_to'
    weight: float = 1.0
    metadata: Dict = field(default_factory=dict)
    
    def __str__(self):
        return f"{self.source_id} --[{self.relationship}]--> {self.target_id}"

@dataclass
class KnowledgeGraph:
    """Represents the complete knowledge graph"""
    nodes: Dict[str, KnowledgeNode] = field(default_factory=dict)
    edges: List[KnowledgeEdge] = field(default_factory=list)
    
    def add_node(self, node: KnowledgeNode):
        """Add a node to the graph"""
        self.nodes[node.id] = node
    
    def add_edge(self, edge: KnowledgeEdge):
        """Add an edge to the graph"""
        if edge.source_id in self.nodes and edge.target_id in self.nodes:
            self.edges.append(edge)
    
    def get_neighbors(self, node_id: str) -> List[str]:
        """Get all nodes connected to a given node"""
        neighbors = set()
        for edge in self.edges:
            if edge.source_id == node_id:
                neighbors.add(edge.target_id)
            elif edge.target_id == node_id:
                neighbors.add(edge.source_id)
        return list(neighbors)
    
    def get_related_documents(self, node_id: str, max_depth: int = 2) -> Set[str]:
        """Get all documents related to a node within max_depth hops"""
        related = set()
        visited = set()
        queue = [(node_id, 0)]
        
        while queue:
            current_id, depth = queue.pop(0)
            
            if current_id in visited or depth > max_depth:
                continue
            
            visited.add(current_id)
            
            # If this is a document node, add it
            if current_id in self.nodes and self.nodes[current_id].node_type == 'document':
                related.add(current_id)
            
            # Add neighbors to queue
            if depth < max_depth:
                for neighbor_id in self.get_neighbors(current_id):
                    if neighbor_id not in visited:
                        queue.append((neighbor_id, depth + 1))
        
        return related
    
    def to_networkx(self):
        """Convert to NetworkX graph for visualization"""
        try:
            import networkx as nx
            
            G = nx.Graph()
            
            # Add nodes
            for node_id, node in self.nodes.items():
                G.add_node(node_id, 
                          name=node.name, 
                          type=node.node_type,
                          description=node.description)
            
            # Add edges
            for edge in self.edges:
                G.add_edge(edge.source_id, edge.target_id, 
                          relationship=edge.relationship,
                          weight=edge.weight)
            
            return G
        
        except ImportError:
            return None
    
    def __str__(self):
        return f"KnowledgeGraph: {len(self.nodes)} nodes, {len(self.edges)} edges"
