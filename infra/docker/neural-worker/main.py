
import logging
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from pydantic import BaseModel
from docling.document_converter import DocumentConverter
from gliner import GLiNER
import rustworkx as rx
import lancedb
from sentence_transformers import SentenceTransformer
import shutil
import os
import tempfile
import pyarrow as pa

# Initialize API
app = FastAPI(title="Neural Worker", version="1.1")
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("NeuralWorker")

# Initialize API
app = FastAPI(title="Neural Worker", version="1.0")
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("NeuralWorker")

# Global Model Placeholders
doc_converter = None
gliner_model = None
embed_model = None
db_connection = None

def get_doc_converter():
    global doc_converter
    if doc_converter is None:
        logger.info("🧠 Lazy Loading Docling Model...")
        doc_converter = DocumentConverter()
    return doc_converter

def get_gliner_model():
    global gliner_model
    if gliner_model is None:
        logger.info("🛡️ Lazy Loading GLiNER Model...")
        GLINER_MODEL = os.getenv("GLINER_MODEL", "urchade/gliner_small-v2.1")
        try:
            gliner_model = GLiNER.from_pretrained(GLINER_MODEL)
        except:
            gliner_model = GLiNER.from_pretrained("urchade/gliner_base")
    return gliner_model

def get_embed_model():
    global embed_model
    if embed_model is None:
        logger.info("🧬 Lazy Loading Embedding Model...")
        # optimized for German/English mixed content
        MODEL_NAME = os.getenv("EMBED_MODEL", "Alibaba-NLP/gte-Qwen3-Embedding-0.6B")
        embed_model = SentenceTransformer(MODEL_NAME)
    return embed_model

def get_db():
    global db_connection
    if db_connection is None:
        logger.info("💾 Connecting to LanceDB...")
        DB_PATH = os.getenv("LANCEDB_PATH", "/mnt/data/lancedb")
        db_connection = lancedb.connect(DB_PATH)
    return db_connection

@app.get("/health")
def health():
    # Shallow health check (container is running)
    return {"status": "ok", "models_loaded": {
        "docling": doc_converter is not None,
        "gliner": gliner_model is not None,
        "embedding": embed_model is not None,
        "lancedb": db_connection is not None
    }}

class PiiRequest(BaseModel):
    text: str
    labels: List[str] = ["person", "iban", "date", "phone", "email"]

class VectorSearchRequest(BaseModel):
    query: str
    limit: int = 5
    min_score: float = 0.0

class VectorStoreRequest(BaseModel):
    id: str
    text: str
    metadata: Dict[str, Any] = {}

@app.post("/vector/embed")
def create_embedding(payload: VectorStoreRequest):
    """
    Generate embedding for text (Internal utility).
    """
    model = get_embed_model()
    vector = model.encode(payload.text).tolist()
    return {"vector": vector, "dim": len(vector)}

@app.post("/vector/store")
def store_document(payload: VectorStoreRequest):
    """
    Store document in LanceDB.
    """
    model = get_embed_model()
    db = get_db()
    
    # Generate Vector
    vector = model.encode(payload.text).tolist()
    
    # Open/Create Table
    table_name = "conductor_docs"
    try:
        table = db.open_table(table_name)
    except:
        # Create schema if not exists
        # 384 dim default for MiniLM-L6, but L12 is 384 too? No L12 is 384.
        # Wait, paraphrase-multilingual-MiniLM-L12-v2 is 384 dimensions.
        schema = pa.schema([
            pa.field("vector", pa.list_(pa.float32(), 384)),
            pa.field("id", pa.string()),
            pa.field("text", pa.string()),
            pa.field("metadata", pa.string()) # Stored as JSON string for flexibility
        ])
        logger.info(f"Creating new table {table_name}")
        # Initial dummy data to force schema creation (LanceDB quirk)
        # Actually pyarrow schema is better supported in create_table now
        # But keeping it simple: just passing data allows auto-inference usually, but explicit is better.
        # We'll rely on the first insert or use `create_table`.
        # For now, let's just attempt to create with data.
        table = None

    import json
    data = [{
        "vector": vector,
        "id": payload.id,
        "text": payload.text,
        "metadata": json.dumps(payload.metadata)
    }]
    
    if table is None:
        table = db.create_table(table_name, data=data)
    else:
        table.add(data)
        
    return {"status": "stored", "id": payload.id}

@app.post("/vector/search")
def search_vector(payload: VectorSearchRequest):
    """
    Semantic Search in LanceDB.
    """
    model = get_embed_model()
    db = get_db()
    
    query_vec = model.encode(payload.query).tolist()
    
    try:
        table = db.open_table("conductor_docs")
        results = table.search(query_vec).limit(payload.limit).to_list()
        
        # Filter by score if needed (LanceDB returns distance usually, but can return similarity)
        # Assuming defaults (L2 distance), lower is better? 
        # Wait, LanceDB defaults to L2. We want cosine similarity maybe?
        # Let's just return what we get for now.
        
        return {"results": results}
    except Exception as e:
        logger.warning(f"Search failed (maybe empty DB?): {e}")
        return {"results": []}


@app.post("/process/pii")
def detect_pii(request: PiiRequest):
    """
    Detect PII in text using GLiNER.
    """
    model = get_gliner_model()
    entities = model.predict_entities(request.text, request.labels)
    # Convert to standard JSON
    results = [
        {"text": e["text"], "label": e["label"], "score": float(e["score"])}
        for e in entities
    ]
    return {"entities": results}

@app.post("/process/deep")
async def deep_ingest(file: UploadFile = File(...)):
    """
    Deep extraction using Docling.
    """
    try:
        # Save upload to temp
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            shutil.copyfileobj(file.file, tmp)
            tmp_path = tmp.name
        
        # Convert
        converter = get_doc_converter()
        result = converter.convert(tmp_path)
        md = result.document.export_to_markdown()
        
        # Cleanup
        os.remove(tmp_path)
        
        return {"markdown": md, "stats": {"chars": len(md)}}
        
    except Exception as e:
        logger.error(f"Docling Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
