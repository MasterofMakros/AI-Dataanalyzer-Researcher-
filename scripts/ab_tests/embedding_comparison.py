"""
Neural Vault A/B Test: Embedding Model Comparison
==================================================

Vergleicht multilingual-e5-large (aktuell) mit Qwen3-Embedding (empfohlen).

Usage:
    python scripts/ab_tests/embedding_comparison.py --samples 1000
    python scripts/ab_tests/embedding_comparison.py --samples 100 --quick

Metriken:
    - Retrieval Precision@10
    - Embedding Speed (docs/sec)
    - RAM-Verbrauch
    - Clustering Quality (Silhouette Score)
"""

import os
import sys
import json
import time
import random
import argparse
import sqlite3
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import List, Dict, Tuple, Optional
import numpy as np

# Projekt-Root
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config.embeddings import (
    EmbeddingModel,
    EMBEDDING_CONFIGS,
    get_embedding_config,
    EMBEDDING_MODEL_ACTIVE,
    EMBEDDING_MODEL_EXPERIMENTAL,
)
from config.paths import LEDGER_DB_PATH, DATA_DIR


# =============================================================================
# KONFIGURATION
# =============================================================================

@dataclass
class ABTestConfig:
    """Konfiguration für den A/B-Test."""
    test_id: str
    sample_size: int
    models: List[str]
    metrics: List[str]
    created_at: str


@dataclass
class EmbeddingResult:
    """Ergebnis für ein Modell."""
    model_id: str
    model_name: str
    total_docs: int
    embedding_time_sec: float
    docs_per_second: float
    avg_embedding_dim: int
    memory_mb: float
    retrieval_precision_at_10: float
    silhouette_score: float
    errors: int


@dataclass
class ABTestResult:
    """Gesamtergebnis des A/B-Tests."""
    test_id: str
    config: ABTestConfig
    results: Dict[str, EmbeddingResult]
    winner: str
    winner_reason: str
    recommendation: str
    created_at: str


# =============================================================================
# EMBEDDING SERVICE
# =============================================================================

class EmbeddingService:
    """Service für Embedding-Generierung mit Model-Switching."""

    def __init__(self, model_enum: EmbeddingModel):
        self.model_enum = model_enum
        self.config = EMBEDDING_CONFIGS[model_enum]
        self.model = None
        self.tokenizer = None

    def load(self):
        """Lädt das Modell."""
        try:
            from sentence_transformers import SentenceTransformer
            print(f"  Loading {self.config.model_id}...")
            self.model = SentenceTransformer(
                self.config.model_id,
                device=self.config.device if self.config.device != "cuda" else None
            )
            print(f"  ✓ Loaded: {self.config.model_id}")
            return True
        except Exception as e:
            print(f"  ✗ Failed to load {self.config.model_id}: {e}")
            return False

    def embed(self, texts: List[str], batch_size: int = None) -> np.ndarray:
        """Generiert Embeddings für Texte."""
        if self.model is None:
            raise RuntimeError("Model not loaded")

        batch_size = batch_size or self.config.batch_size
        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=True,
            normalize_embeddings=self.config.normalize,
        )
        return embeddings

    def unload(self):
        """Entlädt das Modell aus dem Speicher."""
        if self.model is not None:
            del self.model
            self.model = None
            import gc
            gc.collect()
            try:
                import torch
                torch.cuda.empty_cache()
            except:
                pass


# =============================================================================
# TEST DATA SAMPLER
# =============================================================================

def get_sample_documents(sample_size: int) -> List[Dict]:
    """
    Holt Sample-Dokumente aus dem Shadow Ledger.

    Returns:
        Liste von Dokumenten mit {id, text, category}
    """
    documents = []

    # Versuche Shadow Ledger
    if LEDGER_DB_PATH.exists():
        try:
            conn = sqlite3.connect(LEDGER_DB_PATH)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT sha256, extracted_text, category, original_filename
                FROM files
                WHERE extracted_text IS NOT NULL
                AND LENGTH(extracted_text) > 100
                ORDER BY RANDOM()
                LIMIT ?
            """, (sample_size * 2,))  # 2x für Filtering

            rows = cursor.fetchall()
            conn.close()

            for sha256, text, category, filename in rows:
                if text and len(text.strip()) > 100:
                    documents.append({
                        "id": sha256,
                        "text": text[:5000],  # Truncate für Speed
                        "category": category or "unknown",
                        "filename": filename,
                    })

                if len(documents) >= sample_size:
                    break

            print(f"  ✓ Loaded {len(documents)} documents from Shadow Ledger")

        except Exception as e:
            print(f"  ⚠ Shadow Ledger error: {e}")

    # Fallback: Synthetische Testdaten
    if len(documents) < sample_size:
        missing = sample_size - len(documents)
        print(f"  Generating {missing} synthetic test documents...")

        categories = ["Finanzen", "Verträge", "Korrespondenz", "Technisch", "Privat"]
        templates = [
            "Dies ist ein Dokument über {topic}. Es enthält wichtige Informationen zu {detail}.",
            "Betreff: {topic}. Sehr geehrte Damen und Herren, bezüglich {detail} möchten wir...",
            "Rechnung Nr. {num} für {topic}. Betrag: {amount} EUR. Zahlbar bis {date}.",
            "Vertrag zwischen Partei A und Partei B betreffend {topic}. Laufzeit: {duration}.",
            "Technische Dokumentation: {topic}. Version {version}. Beschreibung: {detail}.",
        ]

        for i in range(missing):
            template = random.choice(templates)
            category = random.choice(categories)
            text = template.format(
                topic=f"Thema_{i}",
                detail=f"Detail_{random.randint(1, 100)}",
                num=random.randint(1000, 9999),
                amount=random.randint(100, 10000),
                date="2025-01-31",
                duration=f"{random.randint(1, 5)} Jahre",
                version=f"{random.randint(1, 5)}.{random.randint(0, 9)}",
            )

            documents.append({
                "id": f"synthetic_{i}",
                "text": text,
                "category": category,
                "filename": f"test_doc_{i}.txt",
            })

    return documents[:sample_size]


# =============================================================================
# METRIKEN
# =============================================================================

def calculate_retrieval_precision(
    embeddings: np.ndarray,
    categories: List[str],
    k: int = 10
) -> float:
    """
    Berechnet Retrieval Precision@K.

    Für jedes Dokument: Wie viele der Top-K ähnlichsten
    Dokumente haben die gleiche Kategorie?
    """
    from sklearn.metrics.pairwise import cosine_similarity

    n = len(embeddings)
    if n < k + 1:
        k = n - 1

    # Similarity Matrix
    sim_matrix = cosine_similarity(embeddings)

    precisions = []
    for i in range(n):
        # Top-K ähnlichste (exkl. sich selbst)
        similarities = sim_matrix[i]
        top_indices = np.argsort(similarities)[::-1][1:k+1]

        # Precision: Anteil gleicher Kategorie
        same_category = sum(1 for j in top_indices if categories[j] == categories[i])
        precision = same_category / k
        precisions.append(precision)

    return np.mean(precisions)


def calculate_silhouette_score(
    embeddings: np.ndarray,
    categories: List[str]
) -> float:
    """
    Berechnet Silhouette Score für Clustering-Qualität.

    Höher = bessere Trennung der Kategorien im Embedding-Space.
    """
    from sklearn.metrics import silhouette_score
    from sklearn.preprocessing import LabelEncoder

    # Kategorien zu numerischen Labels
    le = LabelEncoder()
    labels = le.fit_transform(categories)

    # Mindestens 2 verschiedene Labels
    if len(set(labels)) < 2:
        return 0.0

    try:
        score = silhouette_score(embeddings, labels, metric='cosine')
        return float(score)
    except Exception as e:
        print(f"  ⚠ Silhouette calculation failed: {e}")
        return 0.0


def get_memory_usage() -> float:
    """Gibt aktuellen RAM-Verbrauch in MB zurück."""
    try:
        import psutil
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / 1024 / 1024
    except:
        return 0.0


# =============================================================================
# A/B TEST RUNNER
# =============================================================================

def run_embedding_test(
    model_enum: EmbeddingModel,
    documents: List[Dict],
) -> EmbeddingResult:
    """
    Führt Test für ein Modell durch.
    """
    config = EMBEDDING_CONFIGS[model_enum]
    print(f"\n{'='*60}")
    print(f"Testing: {config.model_id}")
    print(f"{'='*60}")

    service = EmbeddingService(model_enum)

    # Memory vorher
    mem_before = get_memory_usage()

    # Modell laden
    if not service.load():
        return EmbeddingResult(
            model_id=config.model_id,
            model_name=model_enum.value,
            total_docs=0,
            embedding_time_sec=0,
            docs_per_second=0,
            avg_embedding_dim=0,
            memory_mb=0,
            retrieval_precision_at_10=0,
            silhouette_score=0,
            errors=1,
        )

    # Memory nach Laden
    mem_after_load = get_memory_usage()
    mem_used = mem_after_load - mem_before

    # Texte extrahieren
    texts = [doc["text"] for doc in documents]
    categories = [doc["category"] for doc in documents]

    # Embedding
    print(f"  Embedding {len(texts)} documents...")
    start_time = time.time()

    try:
        embeddings = service.embed(texts)
        embedding_time = time.time() - start_time
        errors = 0
    except Exception as e:
        print(f"  ✗ Embedding failed: {e}")
        service.unload()
        return EmbeddingResult(
            model_id=config.model_id,
            model_name=model_enum.value,
            total_docs=len(texts),
            embedding_time_sec=0,
            docs_per_second=0,
            avg_embedding_dim=config.dimensions,
            memory_mb=mem_used,
            retrieval_precision_at_10=0,
            silhouette_score=0,
            errors=1,
        )

    docs_per_second = len(texts) / embedding_time if embedding_time > 0 else 0

    print(f"  ✓ Embedded in {embedding_time:.2f}s ({docs_per_second:.1f} docs/sec)")

    # Metriken berechnen
    print("  Calculating metrics...")

    precision = calculate_retrieval_precision(embeddings, categories, k=10)
    print(f"  ✓ Retrieval Precision@10: {precision:.3f}")

    silhouette = calculate_silhouette_score(embeddings, categories)
    print(f"  ✓ Silhouette Score: {silhouette:.3f}")

    # Aufräumen
    service.unload()

    return EmbeddingResult(
        model_id=config.model_id,
        model_name=model_enum.value,
        total_docs=len(texts),
        embedding_time_sec=round(embedding_time, 2),
        docs_per_second=round(docs_per_second, 1),
        avg_embedding_dim=embeddings.shape[1],
        memory_mb=round(mem_used, 1),
        retrieval_precision_at_10=round(precision, 4),
        silhouette_score=round(silhouette, 4),
        errors=errors,
    )


def run_ab_test(sample_size: int = 1000) -> ABTestResult:
    """
    Führt vollständigen A/B-Test durch.
    """
    test_id = f"AB-EMB-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

    print(f"\n{'#'*60}")
    print(f"# A/B Test: Embedding Model Comparison")
    print(f"# Test ID: {test_id}")
    print(f"# Sample Size: {sample_size}")
    print(f"{'#'*60}")

    # Konfiguration
    config = ABTestConfig(
        test_id=test_id,
        sample_size=sample_size,
        models=[
            EMBEDDING_MODEL_ACTIVE.value,
            EMBEDDING_MODEL_EXPERIMENTAL.value,
        ],
        metrics=["retrieval_precision_at_10", "silhouette_score", "docs_per_second"],
        created_at=datetime.now().isoformat(),
    )

    # Testdaten laden
    print("\n📊 Loading test documents...")
    documents = get_sample_documents(sample_size)
    print(f"  ✓ Loaded {len(documents)} documents")

    # Kategorien-Verteilung
    category_counts = {}
    for doc in documents:
        cat = doc["category"]
        category_counts[cat] = category_counts.get(cat, 0) + 1
    print(f"  Categories: {category_counts}")

    # Tests durchführen
    results = {}

    # Modell A (Aktuell)
    result_a = run_embedding_test(EMBEDDING_MODEL_ACTIVE, documents)
    results[EMBEDDING_MODEL_ACTIVE.value] = result_a

    # Modell B (Experimental)
    result_b = run_embedding_test(EMBEDDING_MODEL_EXPERIMENTAL, documents)
    results[EMBEDDING_MODEL_EXPERIMENTAL.value] = result_b

    # Gewinner ermitteln
    print(f"\n{'='*60}")
    print("ERGEBNISVERGLEICH")
    print(f"{'='*60}")

    print(f"\n{'Metrik':<30} {'Modell A':<20} {'Modell B':<20} {'Gewinner':<10}")
    print("-" * 80)

    scores = {"A": 0, "B": 0}

    # Precision (höher = besser)
    print(f"{'Retrieval Precision@10':<30} {result_a.retrieval_precision_at_10:<20.4f} {result_b.retrieval_precision_at_10:<20.4f}", end="")
    if result_b.retrieval_precision_at_10 > result_a.retrieval_precision_at_10:
        print(" B ✓")
        scores["B"] += 2  # Wichtigste Metrik
    else:
        print(" A ✓")
        scores["A"] += 2

    # Silhouette (höher = besser)
    print(f"{'Silhouette Score':<30} {result_a.silhouette_score:<20.4f} {result_b.silhouette_score:<20.4f}", end="")
    if result_b.silhouette_score > result_a.silhouette_score:
        print(" B ✓")
        scores["B"] += 1
    else:
        print(" A ✓")
        scores["A"] += 1

    # Speed (höher = besser)
    print(f"{'Speed (docs/sec)':<30} {result_a.docs_per_second:<20.1f} {result_b.docs_per_second:<20.1f}", end="")
    if result_b.docs_per_second > result_a.docs_per_second:
        print(" B ✓")
        scores["B"] += 1
    else:
        print(" A ✓")
        scores["A"] += 1

    # Memory (niedriger = besser)
    print(f"{'Memory (MB)':<30} {result_a.memory_mb:<20.1f} {result_b.memory_mb:<20.1f}", end="")
    if result_b.memory_mb < result_a.memory_mb:
        print(" B ✓")
        scores["B"] += 1
    else:
        print(" A ✓")
        scores["A"] += 1

    print("-" * 80)
    print(f"{'SCORE':<30} {scores['A']:<20} {scores['B']:<20}")

    # Gewinner
    if scores["B"] > scores["A"]:
        winner = EMBEDDING_MODEL_EXPERIMENTAL.value
        winner_reason = "Höhere Retrieval Precision und/oder bessere Clustering-Qualität"
        recommendation = "Migration zu Qwen3-Embedding empfohlen"
    elif scores["A"] > scores["B"]:
        winner = EMBEDDING_MODEL_ACTIVE.value
        winner_reason = "Aktuelles Modell performt besser in den Benchmarks"
        recommendation = "Keine Migration erforderlich"
    else:
        winner = "TIE"
        winner_reason = "Beide Modelle performen ähnlich"
        recommendation = "Qwen3-Embedding für 8K Context-Länge migrieren"

    print(f"\n🏆 GEWINNER: {winner}")
    print(f"   Grund: {winner_reason}")
    print(f"   Empfehlung: {recommendation}")

    # Ergebnis zusammenstellen
    ab_result = ABTestResult(
        test_id=test_id,
        config=config,
        results={k: asdict(v) for k, v in results.items()},
        winner=winner,
        winner_reason=winner_reason,
        recommendation=recommendation,
        created_at=datetime.now().isoformat(),
    )

    # Ergebnis speichern
    output_dir = DATA_DIR / "ab_tests"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"{test_id}.json"

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(asdict(ab_result), f, indent=2, ensure_ascii=False)

    print(f"\n📄 Ergebnis gespeichert: {output_file}")

    return ab_result


# =============================================================================
# MAIN
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="A/B Test: Embedding Model Comparison"
    )
    parser.add_argument(
        "--samples", "-n",
        type=int,
        default=100,
        help="Anzahl der Test-Dokumente (default: 100)"
    )
    parser.add_argument(
        "--quick", "-q",
        action="store_true",
        help="Quick-Test mit 50 Dokumenten"
    )

    args = parser.parse_args()

    sample_size = 50 if args.quick else args.samples

    # Abhängigkeiten prüfen
    print("Checking dependencies...")
    try:
        from sentence_transformers import SentenceTransformer
        from sklearn.metrics.pairwise import cosine_similarity
        from sklearn.metrics import silhouette_score
        print("  ✓ All dependencies available")
    except ImportError as e:
        print(f"  ✗ Missing dependency: {e}")
        print("  Install with: pip install sentence-transformers scikit-learn")
        sys.exit(1)

    # Test durchführen
    result = run_ab_test(sample_size)

    # Exit-Code basierend auf Ergebnis
    if result.winner == EMBEDDING_MODEL_EXPERIMENTAL.value:
        print("\n✅ Migration empfohlen!")
        sys.exit(0)
    else:
        print("\n⚠️ Aktuelle Konfiguration beibehalten")
        sys.exit(0)


if __name__ == "__main__":
    main()
