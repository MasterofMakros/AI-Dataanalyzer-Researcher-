"""
Knowledge Graph Service (Step 2)
High-Performance Graph Engine using Rustworkx (Memory Optimized)
Target: 10M Edges on Consumer Hardware
"""

import rustworkx as rx
import json
from pathlib import Path
from typing import List, Dict, Tuple

class KnowledgeGraphService:
    def __init__(self):
        # Rustworkx graph (Directed)
        self.graph = rx.PyDiGraph()
        self.node_indices = {} # Map label -> index
        print(f"KnowledgeGraphService initialized (Backend: rustworkx)")

    def add_node(self, label: str, metadata: Dict = None) -> int:
        """Fügt einen Knoten hinzu, falls nicht existiert."""
        if label in self.node_indices:
            return self.node_indices[label]
        
        idx = self.graph.add_node(label)
        self.node_indices[label] = idx
        return idx

    def add_edge(self, source_label: str, target_label: str, weight: float = 1.0):
        """Erstellt eine Kante zwischen zwei Labels."""
        src_idx = self.add_node(source_label)
        tgt_idx = self.add_node(target_label)
        
        # Rustworkx erlaubt Multigraphen, wir prüfen hier einfachheitshalber nicht auf Duplikate
        # für High-Speed Ingest. In Prod: graph.has_edge(src, tgt) checken.
        self.graph.add_edge(src_idx, tgt_idx, weight)

    def shortest_path(self, source_label: str, target_label: str) -> List[str]:
        """Findet den kürzesten Pfad zwischen zwei Knoten."""
        if source_label not in self.node_indices or target_label not in self.node_indices:
            return []
            
        src = self.node_indices[source_label]
        tgt = self.node_indices[target_label]
        
        try:
            # Dijkstra
            path_indices = rx.dijkstra_shortest_paths(self.graph, src, target=tgt, weight_fn=lambda x: float(x))
            # path_indices ist ein Dict {target: [path]}
            if tgt in path_indices:
                path = path_indices[tgt]
                return [self.graph[i] for i in path]
            return []
        except Exception as e:
            print(f"Path error: {e}")
            return []

    def get_stats(self):
        return {
            "nodes": self.graph.num_nodes(),
            "edges": self.graph.num_edges(),
            "memory_efficient": True
        }

if __name__ == "__main__":
    # Integration Test
    kg = KnowledgeGraphService()
    
    print("Ingesting Data...")
    kg.add_edge("Review_A.pdf", "Project_X", 1.0)
    kg.add_edge("Project_X", "Budget_2025.xlsx", 1.0)
    kg.add_edge("Budget_2025.xlsx", "Finance_Dept", 1.0)
    
    print(f"Graph Stats: {kg.get_stats()}")
    
    path = kg.shortest_path("Review_A.pdf", "Finance_Dept")
    print(f"Shortest Path: {' -> '.join(path)}")
