"""
Topic Modeling Service (The Map)
Phase 4: Generates Topic Clusters from the Golden Dataset.
Uses BERTopic (Native) + UMAP + HDBScan.
"""

import sqlite3
import pandas as pd
from bertopic import BERTopic
from sklearn.feature_extraction.text import CountVectorizer
from colorama import Fore, Style
import pickle

from config.paths import LEDGER_DB_PATH, DATA_DIR

LEDGER_DB = LEDGER_DB_PATH
MODEL_PATH = DATA_DIR / "topic_model"
TOPIC_INFO = DATA_DIR / "topic_info.csv"

def run_topic_modeling():
    print(Fore.CYAN + "🗺️  Topic Modeling: Loading Data..." + Style.RESET_ALL)
    
    conn = sqlite3.connect(LEDGER_DB)
    # Only use successfully indexed files from Pilot or Passive
    query = """
        SELECT extracted_text, original_filename 
        FROM files 
        WHERE (status='indexed_pilot' OR status='indexed_passive') 
        AND length(extracted_text) > 200
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    docs = df['extracted_text'].tolist()
    filenames = df['original_filename'].tolist()
    
    print(f"📊 Dataset: {len(docs)} Documents")
    
    if len(docs) < 100:
        print(Fore.RED + "❌ Not enough data (Need > 100 docs)." + Style.RESET_ALL)
        return

    # 2. Configure BERTopic
    # - language="multilingual" (uses robust model)
    # - calculate_probabilities=False (faster)
    # - verbose=True
    print(Fore.YELLOW + "🧠 Training BERTopic Model (This may take a while)..." + Style.RESET_ALL)
    
    topic_model = BERTopic(
        language="multilingual", 
        verbose=True,
        min_topic_size=10, # Good for 5k docs
        vectorizer_model=CountVectorizer(stop_words="english") # Basic stop words
    )
    
    topics, probs = topic_model.fit_transform(docs)
    
    # 3. Analyze Results
    freq = topic_model.get_topic_info()
    print(Fore.GREEN + f"✅ Found {len(freq)-1} Topics!" + Style.RESET_ALL)
    print(freq.head(10))
    
    # 4. Save
    print(f"💾 Saving to {MODEL_PATH}...")
    topic_model.save(MODEL_PATH)
    freq.to_csv(TOPIC_INFO, index=False)
    
    # 5. Output for UI
    # Generate simple hierarchical visualization
    try:
        fig = topic_model.visualize_topics()
    fig.write_html(str(DATA_DIR / "topics_viz.html"))
        print("🗺️  Saved Visualization to 'data/topics_viz.html'")
    except Exception as e:
        print(f"⚠️ Viz Error: {e}")

if __name__ == "__main__":
    run_topic_modeling()
