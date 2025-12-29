"""
Graph Builder (The Weaver)
Phase 4: Builds the Knowledge Graph from the Indexed Data.
Integrates:
- Rustworkx (Graph Structure)
- TF-IDF (Keyword Extraction)
- Vector Similarity (Associative Links)
"""

import sqlite3
import rustworkx as rx
import numpy as np
import pickle
import time
from sklearn.feature_extraction.text import TfidfVectorizer
from sentence_transformers import util

from config.paths import LEDGER_DB_PATH, DATA_DIR

LEDGER_DB = LEDGER_DB_PATH
GRAPH_FILE = DATA_DIR / "knowledge_graph.pkl"

def build_graph():
    print("🕸️ Initializing Knowledge Graph...")
    graph = rx.PyDiGraph()
    node_indices = {} # Label -> Index
    
    def get_or_create_node(label, type="document"):
        if label in node_indices:
            return node_indices[label]
        idx = graph.add_node({"label": label, "type": type})
        node_indices[label] = idx
        return idx
    
    # 1. Load Data
    print("📥 Loading Data from Ledger...")
    conn = sqlite3.connect(LEDGER_DB)
    cursor = conn.cursor()
    
    # Fetch all indexed docs
    query = """
        SELECT id, original_filename, author, extracted_text, embedding_blob 
        FROM files 
        WHERE status LIKE 'indexed%' AND length(extracted_text) > 100
    """
    cursor.execute(query)
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        print("❌ No data found.")
        return
        
    print(f"📊 Processing {len(rows)} Documents...")
    
    docs = []
    texts = []
    ids = []
    vectors = []
    
    start = time.time()
    
    # 2. Build Document & Entity Nodes
    for row in rows:
        doc_id, filename, author, text, emb_blob = row
        
        # Document Node
        doc_node = get_or_create_node(filename, "document")
        ids.append(doc_node)
        docs.append({"id": doc_id, "node": doc_node, "filename": filename})
        texts.append(text)
        
        # Author Node
        if author and len(author.strip()) > 2:
            clean_author = author.strip()
            auth_node = get_or_create_node(clean_author, "author")
            graph.add_edge(doc_node, auth_node, {"rel": "HAS_AUTHOR"})
            
        # Vector Collection
        if emb_blob:
            vec = np.frombuffer(emb_blob, dtype=np.float32)
            vectors.append(vec)
        else:
            vectors.append(None)

    print(f"✅ Basic Nodes Created in {time.time()-start:.2f}s")
    
    # 3. TF-IDF Keywords (Corpus Wide)
    print("🔑 Extracting Top Keywords (TF-IDF)...")
    tfidf = TfidfVectorizer(max_features=1000, stop_words='english')
    try:
        tfidf_matrix = tfidf.fit_transform(texts)
        feature_names = tfidf.get_feature_names_out()
        
        for i, doc_record in enumerate(docs):
            doc_node = doc_record['node']
            # Get top 3 keywords for this doc
            row = tfidf_matrix[i]
            # argsort indices descending
            top_indices = row.toarray()[0].argsort()[-3:][::-1]
            
            for f_idx in top_indices:
                score = row[0, f_idx]
                if score > 0.1: # Threshold
                    word = feature_names[f_idx]
                    kw_node = get_or_create_node(word, "keyword")
                    graph.add_edge(doc_node, kw_node, {"rel": "MENTIONS", "weight": score})
                    
    except Exception as e:
        print(f"⚠️ TF-IDF Error: {e}")
        
    # 4. Vector Similarity Edges
    print("🔗 Computing Vector Links...")
    valid_vectors = [v for v in vectors if v is not None]
    valid_indices = [i for i, v in enumerate(vectors) if v is not None]
    
    if len(valid_vectors) > 1:
        tensor = np.array(valid_vectors)
        # Cosine Similarity Matrix
        sim_matrix = util.cos_sim(tensor, tensor)
        
        # Add Edges for > 0.85
        count = 0
        rows, cols = sim_matrix.shape
        for i in range(rows):
            for j in range(i+1, cols): # Upper triangle
                score = sim_matrix[i][j].item()
                if score > 0.85:
                    src_node = ids[valid_indices[i]]
                    tgt_node = ids[valid_indices[j]]
                    graph.add_edge(src_node, tgt_node, {"rel": "SIMILAR_TO", "weight": score})
                    count += 1
        print(f"✅ Created {count} Similarity Edges.")
        
    # 5. Stats & Save
    num_nodes = graph.num_nodes()
    num_edges = graph.num_edges()
    print(f"\n🎉 Graph Built!")
    print(f"  Nodes: {num_nodes}")
    print(f"  Edges: {num_edges}")
    
    with open(GRAPH_FILE, "wb") as f:
        pickle.dump(graph, f)
    print(f"💾 Saved to {GRAPH_FILE}")

if __name__ == "__main__":
    build_graph()
