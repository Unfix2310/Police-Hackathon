"""
Investigation Graph Module.
"""
import networkx as nx
from typing import Dict, Any, List

class InvestigationGraph:
    """Builds and analyzes investigation graphs."""
    
    def __init__(self):
        self.graph = nx.Graph()

    async def build_entity_graph(self, entity_type: str, entity_id: str, depth: int, db: Any) -> nx.Graph:
        """Builds a graph around an entity up to a certain depth."""
        self.graph.add_node(entity_id, type=entity_type)
        return self.graph

    def find_path(self, source: str, target: str) -> List[str]:
        """Finds path between two nodes."""
        try:
            return nx.shortest_path(self.graph, source, target)
        except nx.NetworkXNoPath:
            return []

    def get_neighbors(self, node: str) -> List[str]:
        """Gets neighbors of a node."""
        return list(self.graph.neighbors(node))

    def to_visualization_format(self) -> Dict[str, List[Dict[str, Any]]]:
        """Converts graph to visualization format {nodes: [...], edges: [...]}. """
        nodes = [{"id": n, **self.graph.nodes[n]} for n in self.graph.nodes]
        edges = [{"source": u, "target": v, **self.graph.edges[u, v]} for u, v in self.graph.edges]
        return {"nodes": nodes, "edges": edges}
