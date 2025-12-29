"""
Graph Library Benchmark: NetworkX vs Rustworkx
Goal: Find a scalable solution for 10M edges on Windows.
"""

import time
import networkx as nx
import rustworkx as rx
import os
import psutil

# Configuration
NUM_NODES = 100_000
NUM_EDGES = 500_000

def get_memory_usage():
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024  # MB

def benchmark_networkx():
    print(f"\n--- NetworkX Benchmark ({NUM_NODES} nodes, {NUM_EDGES} edges) ---")
    start_mem = get_memory_usage()
    
    # 1. Creation
    t0 = time.time()
    G = nx.gnm_random_graph(NUM_NODES, NUM_EDGES, seed=42)
    t1 = time.time()
    print(f"Creation: {t1-t0:.4f} sec")
    
    # 2. PageRank
    t0 = time.time()
    try:
        pr = nx.pagerank(G, alpha=0.85, max_iter=10)
    except:
        pr = {}
    t1 = time.time()
    print(f"PageRank: {t1-t0:.4f} sec")
    
    # 3. Shortest Path (Single Source)
    t0 = time.time()
    try:
        # Calculate from node 0 to all others
        paths = nx.single_source_shortest_path_length(G, 0)
    except:
        paths = {}
    t1 = time.time()
    print(f"Shortest Path (One-to-All): {t1-t0:.4f} sec")
    
    end_mem = get_memory_usage()
    print(f"Memory Delta: {end_mem - start_mem:.2f} MB")
    return G

def benchmark_rustworkx():
    print(f"\n--- Rustworkx Benchmark ({NUM_NODES} nodes, {NUM_EDGES} edges) ---")
    start_mem = get_memory_usage()
    
    # 1. Creation (Rustworkx doesn't have gnm_random_graph built-in exactly like NX, simulating or using equivalent)
    # Rustworkx has directed/undirected. We'll use undirected for fair comparison.
    t0 = time.time()
    G = rx.undirected_gnm_random_graph(NUM_NODES, NUM_EDGES, seed=42)
    t1 = time.time()
    print(f"Creation: {t1-t0:.4f} sec")
    
    # 2. PageRank
    t0 = time.time()
    # rustworkx.pagerank returns a dictionary
    try:
        pr = rx.pagerank(G, alpha=0.85, max_iter=10)
    except:
        pr = {}
    t1 = time.time()
    print(f"PageRank: {t1-t0:.4f} sec")
    
    # 3. Shortest Path (Single Source)
    # rustworkx.dijkstra_shortest_path_lengths
    t0 = time.time()
    try:
        paths = rx.dijkstra_shortest_path_lengths(G, 0, lambda x: 1.0)
    except:
        paths = {}
    t1 = time.time()
    print(f"Shortest Path (One-to-All): {t1-t0:.4f} sec")
    
    end_mem = get_memory_usage()
    print(f"Memory Delta: {end_mem - start_mem:.2f} MB")
    return G

if __name__ == "__main__":
    print("Starting Graph Benchmark...")
    
    benchmark_networkx()
    benchmark_rustworkx()
