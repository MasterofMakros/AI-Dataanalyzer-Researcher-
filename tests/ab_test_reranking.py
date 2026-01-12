
"""
A/B Test: Search Reranking (ABT-B01)
Compares Standard Search (BM25+Vector) vs Reranked Search.
"""

import time
import pandas as pd
import numpy as np
from pathlib import Path
from sentence_transformers import SentenceTransformer, util

# Add project root to path
# Add project root to path
import sys
from pathlib import Path
ROOT_DIR = Path(__file__).parent.parent.resolve()
sys.path.append(str(ROOT_DIR))
from services.reranker import RerankingService

# Setup Mock Data
DOCS = [
    # Ambiguous "Bank" documents
    {"id": 1, "text": "Die Parkbank im Stadtpark ist neu gestrichen.", "category": "Privat"},
    {"id": 2, "text": "Die Deutsche Bank erhöht die Zinsen für Sparkonten.", "category": "Finanzen"},
    {"id": 3, "text": "Ich sitze auf der Bank und lese ein Buch.", "category": "Privat"},
    {"id": 4, "text": "Banküberweisung von 500 Euro getätigt.", "category": "Finanzen"},
    
    # Ambiguous "Java" documents
    {"id": 5, "text": "Java ist eine Insel in Indonesien.", "category": "Reisen"},
    {"id": 6, "text": "Java Programming Language Tutorial for Beginners.", "category": "Technologie"},
    {"id": 7, "text": "Urlaub auf Java war sehr schön.", "category": "Reisen"},
    {"id": 8, "text": "System.out.println('Hello Java');", "category": "Technologie"},
    
    # Simple "Invoice"
    {"id": 9, "text": "Rechnung Nr 123 für Dienstleistung.", "category": "Finanzen"},
    {"id": 10, "text": "Rechnung über Hardware-Kauf.", "category": "Finanzen"},
]

QUERIES = [
    {"q": "Bank Zinsen", "relevant": [2, 4]},      # Finance context
    {"q": "Java Programmieren", "relevant": [6, 8]}, # Tech context
    {"q": "Urlaub", "relevant": [5, 7]},            # Travel context
]

print("🚀 Loading Embedding Model...")
embedder = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
doc_embeddings = embedder.encode([d["text"] for d in DOCS])

# Force Enable Reranker for Test
import config.feature_flags
config.feature_flags.FEATURE_FLAGS["ENABLE_RERANKING"] = (True, "TEST", "")
reranker = RerankingService()

def search_baseline(query, top_k=3):
    """Standard Semantic Search (Cosine Sim)."""
    q_vec = embedder.encode(query)
    hits = util.semantic_search(q_vec, doc_embeddings, top_k=5)[0] # Fetch top 5 candidates
    
    # Map back to docs
    results = []
    for hit in hits:
        doc = DOCS[hit['corpus_id']].copy()
        doc['score'] = hit['score']
        results.append(doc)
        
    return results[:top_k]

def search_candidate(query, top_k=3):
    """Search + Reranker."""
    # 1. Retrieve Candidates (Top 5)
    candidates = search_baseline(query, top_k=5)
    
    # 2. Rerank
    reranked = reranker.rerank(query, candidates, top_k=top_k)
    return reranked

def evaluate(search_fn, name):
    print(f"\n🏃 Evaluating {name}...")
    precisions = []
    
    for item in QUERIES:
        query = item["q"]
        relevant_ids = item["relevant"]
        
        results = search_fn(query, top_k=2) # Strict top-k for precision
        
        found_ids = [r["id"] for r in results]
        
        # Calculate Precision@2
        relevant_found = len(set(found_ids) & set(relevant_ids))
        precision = relevant_found / len(found_ids) if found_ids else 0
        precisions.append(precision)
        
        print(f"   Q: '{query}' -> Found: {found_ids} (Relevant: {relevant_ids}) -> P@2: {precision:.1f}")
        if name == "Candidate (Reranked)":
             for r in results:
                 print(f"      - {r['text'][:40]}... (Score: {r.get('rerank_score', 0):.4f})")

    avg_p = sum(precisions) / len(precisions)
    return avg_p

def main():
    print("--- Baseline (Cosine Similarity) ---")
    score_a = evaluate(search_baseline, "Baseline (Cosine)")
    
    print("\n--- Candidate (Cross-Encoder) ---")
    score_b = evaluate(search_candidate, "Candidate (Reranked)")
    
    print("\n" + "="*40)
    print(f"Baseline Precision:  {score_a:.2%}")
    print(f"Candidate Precision: {score_b:.2%}")
    print("="*40)
    
    improvement = score_b - score_a
    result_file = Path("F:/conductor/tests/report_abt_b01.md")
    
    report = f"""
## A/B-Test Report: ABT-B01 (Reranking)

### Test-Setup
- Daten: 10 Dokumente (Ambige Beispiele)
- Queries: 3 (Bank, Java, Urlaub)

### Ergebnisse
| Metrik | Baseline | Kandidat | Verbesserung |
|--------|----------|----------|--------------|
| Precision@2 | {score_a:.2%} | {score_b:.2%} | {improvement:+.2%} |

### Decision
"""
    if improvement > 0.10:
        report += "**BLUE** (Reranking Wins) - Significant Improvement."
    else:
        report += "**INCONCLUSIVE** - No significant gain."
        
    print(report)
    result_file.write_text(report, encoding="utf-8")

if __name__ == "__main__":
    main()
