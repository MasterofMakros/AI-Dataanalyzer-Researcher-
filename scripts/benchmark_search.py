"""
Search Quality Benchmark (Heuristic)
Tests if the top search results for a keyword actually contain that keyword or synonyms.
A simple "Sanity Check" for the retrieval system.
"""

import sqlite3
import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer, util
from tabulate import tabulate

MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"
from config.paths import LEDGER_DB_PATH

LEDGER_DB = str(LEDGER_DB_PATH)

# Test Queries and expected keywords in text/filename
TEST_CASES = [
    {"query": "Chemie", "expected": ["chemie", "chemistry", "stoff", "reaktion", "periodensystem"]},
    {"query": "Rechnung", "expected": ["rechnung", "invoice", "bezahlung", "betrag", "steuer"]},
    {"query": "Biologie", "expected": ["biologie", "biology", "zelle", "genetik", "organismus"]},
    {"query": "Programmierung", "expected": ["programmierung", "code", "python", "java", "software"]},
    # Specific Check for known files (based on previous logs)
    {"query": "Mikrobiologie", "expected": ["mikrobiologie", "microbiology", "bakterien", "viren"]}
]

def run_benchmark():
    print(f"🚀 Loading Model: {MODEL_NAME}...")
    model = SentenceTransformer(MODEL_NAME)
    
    print("📋 Loading Index...")
    conn = sqlite3.connect(LEDGER_DB)
    df = pd.read_sql_query("SELECT id, original_filename, extracted_text, embedding_blob FROM files WHERE embedding_status='DONE'", conn)
    conn.close()
    
    if df.empty:
        print("❌ No indexed documents found.")
        return

    # Prepare Corpus
    embeddings = []
    for idx, row in df.iterrows():
        vec = np.frombuffer(row['embedding_blob'], dtype=np.float32)
        embeddings.append(vec)
    corpus_embeddings = np.array(embeddings)
    
    print(f"🔍 Benchmarking {len(TEST_CASES)} queries against {len(df)} docs...\n")
    
    results_table = []
    
    total_score = 0
    
    for case in TEST_CASES:
        query = case['query']
        expected_keywords = case['expected']
        
        # Search
        query_vec = model.encode(query)
        hits = util.semantic_search(query_vec, corpus_embeddings, top_k=5)[0]
        
        # Evaluate Top 5
        precision_at_5 = 0
        relevant_docs = []
        
        for hit in hits:
            doc_idx = hit['corpus_id']
            record = df.iloc[doc_idx]
            content = (str(record['original_filename']) + " " + str(record['extracted_text'])).lower()
            
            is_relevant = any(k in content for k in expected_keywords)
            if is_relevant:
                precision_at_5 += 1
                relevant_docs.append("✅ " + record['original_filename'][:30])
            else:
                relevant_docs.append("❌ " + record['original_filename'][:30])
                
        p5_score = precision_at_5 / 5.0
        total_score += p5_score
        
        results_table.append([
            query, 
            ", ".join(expected_keywords), 
            f"{p5_score:.2f}",
            "\n".join(relevant_docs)
        ])
        
    print(tabulate(results_table, headers=["Query", "Expected Keywords", "P@5 Score", "Top 5 Results"], tablefmt="grid"))
    
    avg_score = total_score / len(TEST_CASES)
    print(f"\n🏆 Overall Mean Precision@5: {avg_score:.2f}")
    if avg_score < 0.4:
        print("⚠️  System needs improvement (Target: >0.6)")
    else:
        print("✅ System seems plausible.")

if __name__ == "__main__":
    run_benchmark()
