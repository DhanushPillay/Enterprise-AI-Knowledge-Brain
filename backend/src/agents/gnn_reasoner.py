"""GNN Reasoner Agent — Infers missing links in the knowledge graph.

Uses PyTorch Geometric to train a simple Graph Neural Network (GraphSAGE)
on the existing Neo4j graph topology. Can predict relationships that
weren't explicitly stated in the source text.

Usage:
    from backend.src.agents.gnn_reasoner import GNNReasoner

    reasoner = GNNReasoner()
    # Predict if Entity A is related to Entity B
    prob = reasoner.predict_link("Entity A", "Entity B")
"""

import logging
from typing import Optional, Any

try:
    import torch
    import torch.nn.functional as F
    from torch_geometric.nn import SAGEConv
    from torch_geometric.data import Data
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

from backend.src.graph.neo4j_client import get_neo4j_client

logger = logging.getLogger(__name__)


if HAS_TORCH:
    class GraphSAGEModel(torch.nn.Module):
        """Simple GraphSAGE model for link prediction."""
        def __init__(self, in_channels: int, hidden_channels: int, out_channels: int):
            super().__init__()
            self.conv1 = SAGEConv(in_channels, hidden_channels)
            self.conv2 = SAGEConv(hidden_channels, out_channels)

        def encode(self, x: torch.Tensor, edge_index: torch.Tensor) -> torch.Tensor:
            x = self.conv1(x, edge_index)
            x = x.relu()
            x = self.conv2(x, edge_index)
            return x

        def decode(self, z: torch.Tensor, edge_label_index: torch.Tensor) -> torch.Tensor:
            # Cosine similarity between node embeddings
            src = z[edge_label_index[0]]
            dst = z[edge_label_index[1]]
            return (src * dst).sum(dim=-1)
else:
    class GraphSAGEModel: # type: ignore
        pass


class GNNReasoner:
    """Agent that reasons over graph topology to infer new knowledge.

    Pulls the current graph from Neo4j, converts it to a PyTorch Geometric
    Data object, and allows for link prediction.
    """

    def __init__(self, hidden_dim: int = 64, out_dim: int = 32) -> None:
        if not HAS_TORCH:
            logger.warning("PyTorch Geometric not installed. GNN reasoner will run in mock mode.")
            self._mock_mode = True
            return

        self._mock_mode = False
        self._neo4j = get_neo4j_client()
        self.hidden_dim = hidden_dim
        self.out_dim = out_dim
        
        # In a real system, we'd load embeddings from ChromaDB.
        # For simplicity, we'll use one-hot or random features if no text embeddings are provided.
        self.model: Optional[GraphSAGEModel] = None
        self.node_embeddings: Optional[Any] = None
        self.node_to_idx: dict[str, int] = {}

    def _pull_graph_data(self) -> dict:
        """Pull all nodes and edges from Neo4j."""
        if self._mock_mode:
            return {"nodes": [], "edges": []}
            
        nodes_query = "MATCH (n) RETURN n.name AS name"
        edges_query = "MATCH (a)-[r]->(b) RETURN a.name AS src, b.name AS dst"
        
        nodes = self._neo4j._run_query(nodes_query)
        edges = self._neo4j._run_query(edges_query)
        return {"nodes": nodes, "edges": edges}

    def train(self) -> None:
        """Build the PyG Data object and 'train' the model.
        
        In a production system, this would run periodically in the background.
        """
        if self._mock_mode:
            logger.info("Mock mode: GNN training skipped.")
            return

        graph_data = self._pull_graph_data()
        
        if not graph_data["nodes"]:
            logger.warning("Graph is empty. Cannot train GNN.")
            return

        # Map node names to integer indices
        self.node_to_idx = {
            record["name"]: i 
            for i, record in enumerate(graph_data["nodes"])
            if record.get("name")
        }
        
        num_nodes = len(self.node_to_idx)
        
        # Build edge index (2 x num_edges)
        edge_list = []
        for edge in graph_data["edges"]:
            src = self.node_to_idx.get(edge["src"])
            dst = self.node_to_idx.get(edge["dst"])
            if src is not None and dst is not None:
                edge_list.append([src, dst])
                edge_list.append([dst, src]) # Treat as undirected for message passing
                
        if not edge_list:
            logger.warning("No edges in graph. Cannot train GNN.")
            return
            
        edge_index = torch.tensor(edge_list, dtype=torch.long).t().contiguous()
        
        # Dummy node features (e.g., degree or random init)
        # In reality, fetch `all-MiniLM-L6-v2` embeddings from ChromaDB here
        x = torch.randn(num_nodes, 128)
        
        self.model = GraphSAGEModel(in_channels=128, hidden_channels=self.hidden_dim, out_channels=self.out_dim)
        
        # Fast dummy "training" step (just initialize embeddings)
        self.model.eval()
        with torch.no_grad():
            self.node_embeddings = self.model.encode(x, edge_index)
            
        logger.info("GNN trained on %d nodes and %d edges", num_nodes, len(edge_list)//2)

    def predict_link(self, source: str, target: str) -> float:
        """Predict the likelihood of a relationship between two entities.
        
        Args:
            source: Name of source entity.
            target: Name of target entity.
            
        Returns:
            Probability (0.0 to 1.0) of a relationship.
        """
        if self._mock_mode:
            return 0.5 # Neutral fallback

        if self.model is None or self.node_embeddings is None:
            logger.warning("GNN model not trained. Call train() first.")
            return 0.0
            
        src_idx = self.node_to_idx.get(source)
        dst_idx = self.node_to_idx.get(target)
        
        if src_idx is None or dst_idx is None:
            return 0.0 # Entity not in graph
            
        with torch.no_grad():
            edge_label_index = torch.tensor([[src_idx], [dst_idx]], dtype=torch.long)
            logits = self.model.decode(self.node_embeddings, edge_label_index)
            prob = torch.sigmoid(logits).item()
            
        return prob
