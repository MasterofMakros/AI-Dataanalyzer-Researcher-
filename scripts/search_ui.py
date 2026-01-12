"""
Neural Vault Search UI (Hybrid-Ready)
Phase 3: Visual Interface for Knowledge Discovery
"""

import sys
from pathlib import Path
# Add project root to path to allow importing config
sys.path.append(str(Path(__file__).resolve().parent.parent))

import gradio as gr
import sqlite3
import numpy as np
from sentence_transformers import SentenceTransformer, util
import pandas as pd

# Config
import requests
import json
from config.paths import LEDGER_DB_PATH, DATA_DIR, OLLAMA_URL

LEDGER_DB = LEDGER_DB_PATH
MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2" # Must match Vector Service!

print("🚀 Loading Search Engine...")
model = SentenceTransformer(MODEL_NAME)
print("✅ Ready.")

def _search_core(query, top_k=5, threshold=0.35):
    """Core search logic returning structured data."""
    if not query:
        return []
    
    query_vec = model.encode(query)
    
    conn = sqlite3.connect(LEDGER_DB)
    df = pd.read_sql_query("SELECT id, original_filename, extracted_text, embedding_blob FROM files WHERE embedding_status='DONE'", conn)
    conn.close()
    
    if df.empty:
        return []
        
    embeddings = []
    for idx, row in df.iterrows():
        vec = np.frombuffer(row['embedding_blob'], dtype=np.float32)
        embeddings.append(vec)
        
    corpus_embeddings = np.array(embeddings)
    hits = util.semantic_search(query_vec, corpus_embeddings, top_k=top_k)[0]
    
    results = []
    for hit in hits:
        if hit['score'] < threshold:
            continue
            
        doc_idx = hit['corpus_id']
        record = df.iloc[doc_idx]
        results.append({
            "score": hit['score'],
            "filename": record['original_filename'],
            "text": record['extracted_text'] or ""
        })
    
    return results

def search_knowledge(query, top_k=10):
    """Formats search results for the UI list."""
    hits = _search_core(query, top_k=top_k)
    
    if not hits:
        return [["-", "Keine relevanten Dokumente gefunden (Threshold < 0.35)", "Bitte präzisieren Sie Ihre Suche."]]
    
    rows = []
    for hit in hits:
        text = hit['text']
        snippet = text[:300] + "..." if len(text) > 300 else text
        rows.append([f"{hit['score']:.2f}", hit['filename'], snippet])
    return rows


# Evidence Board Logic
def search_evidence(query):
    """Generates HTML Cards for Evidence Board."""
    hits = _search_core(query, top_k=20)
    
    if not hits:
        return "<div style='text-align:center; padding:20px; color:#666;'>No documents found matching criteria.</div>"
    
    html = "<div style='display: flex; flex-wrap: wrap; gap: 20px; padding: 20px; background-color: #f5f5f5; border-radius: 10px;'>"
    
    for hit in hits:
        score = hit['score']
        # Color coding based on score
        if score > 0.7:
            border_color = "#4CAF50" # Green
            bg_color = "#e8f5e9"
        elif score > 0.5:
            border_color = "#FF9800" # Orange
            bg_color = "#fff3e0"
        else:
            border_color = "#9E9E9E" # Grey
            bg_color = "#ffffff"
            
        snippet = hit['text'][:150] + "..." if len(hit['text']) > 150 else hit['text']
        filename = hit['filename']
        # Icon based on extension (simple check)
        icon = "📄"
        if filename.endswith(".pdf"): icon = "📕"
        elif filename.endswith(".jpg"): icon = "🖼️"
        
        card = f"""
        <div style="
            width: 250px;
            height: 300px;
            background: {bg_color};
            border: 2px solid {border_color};
            border-radius: 12px;
            padding: 15px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            display: flex;
            flex-direction: column;
            transition: transform 0.2s;
        " onmouseover="this.style.transform='scale(1.02)'" onmouseout="this.style.transform='scale(1.0)'">
            <div style="font-size: 2em; text-align: center; margin-bottom: 10px;">{icon}</div>
            <div style="font-weight: bold; margin-bottom: 10px; word-wrap: break-word; color: #333; height: 50px; overflow: hidden;">{filename}</div>
            <div style="font-size: 0.85em; color: #555; flex-grow: 1; overflow: hidden; margin-bottom: 10px;">{snippet}</div>
            <div style="margin-top: auto; padding-top: 10px; border-top: 1px solid rgba(0,0,0,0.1); display: flex; justify-content: space-between; align-items: center;">
                <span style="font-size: 0.8em; color: #666;">Match</span>
                <span style="font-weight: bold; color: {border_color};">{score:.0%}</span>
            </div>
        </div>
        """
        html += card
        
    html += "</div>"
    return html

def ask_ollama(message, history):
    """RAG Chat function for Gradio."""
    # 1. Retrieve Context
    docs = _search_core(message, top_k=3)
    
    if not docs:
        context = "Keine relevanten Dokumente im Archiv gefunden."
    else:
        context = "\n\n".join([f"--- Dokument: {d['filename']} ---\n{d['text'][:1500]}" for d in docs])
    
    # 2. Construct Prompt
    system_prompt = """Du bist der Neural Vault Data Narrator. 
Beantworte die Frage basierend auf den folgenden Dokumenten. 
Wenn die Antwort nicht in den Dokumenten steht, sage das ehrlich.
Erfinde keine Fakten. Antworte in der Sprache der Frage."""
    
    full_prompt = f"System: {system_prompt}\n\nKontext:\n{context}\n\nFrage: {message}\nAntwort:"
    
    # 3. Call Ollama
    try:
        payload = {
            "model": "qwen3:8b", # Or use default from config/flags if needed
            "prompt": full_prompt,
            "stream": True
        }
        
        response = requests.post(f"{OLLAMA_URL}/api/generate", json=payload, stream=True)
        
        partial_response = ""
        for line in response.iter_lines():
            if line:
                try:
                    json_response = json.loads(line)
                    token = json_response.get("response", "")
                    partial_response += token
                    yield partial_response
                except:
                    pass
    except Exception as e:
        yield f"Fehler bei der Anfrage an Ollama: {str(e)}"


# ... (Graph Code remains the same) ...
import rustworkx as rx
import pickle
from pathlib import Path

GRAPH_FILE = DATA_DIR / "knowledge_graph.pkl"

def load_graph_stats():
    # ... (Keep existing implementation)
    try:
        with open(GRAPH_FILE, "rb") as f:
            graph = pickle.load(f)
        
        num_nodes = graph.num_nodes()
        num_edges = graph.num_edges()
        
        pagerank = rx.pagerank(graph, alpha=0.85)
        sorted_nodes = sorted(pagerank.items(), key=lambda x: x[1], reverse=True)[:20]
        
        top_docs = []
        top_keywords = []
        
        for idx, score in sorted_nodes:
            node_data = graph[idx]
            if isinstance(node_data, dict):
                label = node_data.get("label", str(node_data))
                ntype = node_data.get("type", "unknown")
            else:
                label = str(node_data)
                ntype = "unknown"
                
            entry = [f"{score:.4f}", label]
            if ntype == "document":
                top_docs.append(entry)
            elif ntype == "keyword":
                top_keywords.append(entry)
                
        stats_text = f"Nodes: {num_nodes}\nEdges: {num_edges}\nDensity: {num_edges/(num_nodes*num_nodes):.6f}"
        return stats_text, top_docs[:10], top_keywords[:10]
    except Exception as e:
        return f"Error loading graph: {e}", [], []


# UI Definition
with gr.Blocks(title="Neural Vault: Knowledge Search") as demo:
    gr.Markdown("# 🧠 Neural Vault: Knowledge Search & Graph")
    
    with gr.Tabs():
        with gr.TabItem("💬 Q&A Chat"):
            gr.ChatInterface(
                fn=ask_ollama,
                title="Data Narrator",
                description="Stellen Sie Fragen an Ihr Dokumenten-Archiv.",
                examples=["Was ist die höchste Ausgabe?", "Fasse die letzten Projekt-Updates zusammen."],
            )

        with gr.TabItem("🔎 Search"):
            with gr.Row():
                query_input = gr.Textbox(label="Ask your archive...", placeholder="Wie funktioniert ein Oszilloskop?", scale=4)
                search_btn = gr.Button("Search", variant="primary", scale=1)
            
            with gr.Row():
                gr.Markdown("### Search Results (Quality Gate: >0.35)")
            
            results_output = gr.Dataframe(
                headers=["Score", "Filename", "Snippet"],
                datatype=["str", "str", "str"],
                label="Results",
                interactive=False,
                wrap=True
            )
            
            search_btn.click(fn=search_knowledge, inputs=query_input, outputs=results_output)
            query_input.submit(fn=search_knowledge, inputs=query_input, outputs=results_output)
            
        with gr.TabItem("🕵️ Evidence Board"):
            gr.Markdown("### 🕵️ Visual Knowledge Board")
            with gr.Row():
                ev_input = gr.Textbox(label="Filter Evidence...", placeholder="Project Alpha", scale=4)
                ev_btn = gr.Button("Visualize", variant="primary", scale=1)
            
            ev_output = gr.HTML(value="<div style='padding:20px; text-align:center'>Enter query to populate board.</div>")
            
            ev_btn.click(fn=search_evidence, inputs=ev_input, outputs=ev_output)
            ev_input.submit(fn=search_evidence, inputs=ev_input, outputs=ev_output)

        with gr.TabItem("🕸️ Graph Explorer"):
            gr.Markdown("### Knowledge Graph Statistics")
            refresh_btn = gr.Button("Refresh Graph Data")
            
            with gr.Row():
                stats_box = gr.Textbox(label="Network Stats", lines=4)
            
            with gr.Row():
                with gr.Column():
                    gr.Markdown("### Top 10 Central Documents (PageRank)")
                    top_docs_df = gr.Dataframe(headers=["PageRank", "Document"], datatype=["str", "str"])
                
                with gr.Column():
                    gr.Markdown("### Top 10 Key Concepts")
                    top_kw_df = gr.Dataframe(headers=["PageRank", "Keyword"], datatype=["str", "str"])
            
            refresh_btn.click(fn=load_graph_stats, outputs=[stats_box, top_docs_df, top_kw_df])
            demo.load(fn=load_graph_stats, outputs=[stats_box, top_docs_df, top_kw_df])
            
        with gr.TabItem("🗺️ Topic Map"):
            gr.Markdown("### Global Topic Clusters (BERTopic)")
            gr.Markdown("Run `topic_modeling_pilot.py` to generate this map.")
            topic_html = gr.HTML(value="<p>No Topic Map generated yet.</p>")
            
            def load_topic_map():
                try:
                    map_path = DATA_DIR / "topics_viz.html"
                    with open(map_path, "r", encoding="utf-8") as f:
                        return f.read()
                except:
                    return "<p>Topic Map not found. Please wait for the Pilot to complete.</p>"
            
            refresh_topics_btn = gr.Button("Refresh Map")
            refresh_topics_btn.click(fn=load_topic_map, outputs=topic_html)
            demo.load(fn=load_topic_map, outputs=topic_html)

if __name__ == "__main__":
    demo.launch(server_port=7861, share=False, theme=gr.themes.Soft())
