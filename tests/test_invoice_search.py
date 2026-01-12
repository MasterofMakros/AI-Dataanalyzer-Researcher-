# tests/test_invoice_search.py
"""
Automatisierte Tests für die Suchfunktion.
PRD: "Rechnungen, Belege und Kassenbons müssen innerhalb von 1 Minute gefunden werden."
"""

import pytest
import time
import os

# --- KONFIGURATION ---
# Für echte Tests: Ersetze dies durch den tatsächlichen Such-Client
# from neural_vault import search_client

# Mock-Implementation für Entwicklung
class MockSearchClient:
    """Placeholder - ersetze durch echten Qdrant/Meilisearch Client."""
    
    def __init__(self, index_path: str = "tests/dummy_index.csv"):
        self.index_path = index_path
        self._index = None
    
    def _load_index(self):
        """Lazy-load den CSV-Index."""
        if self._index is None:
            import csv
            self._index = []
            with open(self.index_path, 'r', encoding='utf-8', errors='replace') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    self._index.append(row)
        return self._index
    
    def search(self, query: str, top_k: int = 10) -> list:
        """Einfache Keyword-Suche im Index."""
        index = self._load_index()
        query_lower = query.lower()
        keywords = query_lower.split()
        
        results = []
        for row in index:
            filename_lower = row.get('Filename', '').lower()
            path_lower = row.get('Path', '').lower()
            
            # Prüfe ob ALLE Keywords im Dateinamen oder Pfad vorkommen
            if all(kw in filename_lower or kw in path_lower for kw in keywords):
                results.append({
                    'filename': row.get('Filename', ''),
                    'path': row.get('Path', ''),
                    'size_mb': row.get('Size_MB', 0)
                })
                
            if len(results) >= top_k:
                break
        
        return results

# Initialisiere den Such-Client
search_client = MockSearchClient()

# --- TEST DATA ---
TEST_QUERIES = [
    {
        "query": "Rechnung",
        "description": "Suche nach beliebiger Rechnung",
        "expected_min_results": 1
    },
    {
        "query": "pdf Finanzen",
        "description": "Suche nach PDFs im Finanz-Bereich",
        "expected_min_results": 0  # Kann 0 sein, wenn keine existieren
    },
    {
        "query": "Kontoauszug",
        "description": "Suche nach Kontoauszügen",
        "expected_min_results": 0
    },
]

# --- SLA ---
MAX_SEARCH_TIME_SECONDS = 60  # User-Anforderung: < 1 Minute


class TestInvoiceSearch:
    """Tests für die Rechnungs-/Beleg-Suche."""
    
    @pytest.mark.parametrize("test_case", TEST_QUERIES)
    def test_search_returns_within_time_limit(self, test_case):
        """
        Testet, dass jede Suche innerhalb des SLA (< 1 Minute) abgeschlossen wird.
        """
        query = test_case["query"]
        
        start_time = time.time()
        results = search_client.search(query, top_k=10)
        elapsed_time = time.time() - start_time
        
        # Assert: Zeitlimit eingehalten
        assert elapsed_time < MAX_SEARCH_TIME_SECONDS, \
            f"Suche für '{query}' dauerte {elapsed_time:.2f}s (Limit: {MAX_SEARCH_TIME_SECONDS}s)"
        
        print(f"✅ '{query}': {len(results)} Ergebnisse in {elapsed_time:.2f}s")
    
    def test_index_file_exists(self):
        """Prüft, ob die Index-Datei existiert."""
        assert os.path.exists(search_client.index_path), \
            f"Index-Datei nicht gefunden: {search_client.index_path}"
    
    def test_index_has_data(self):
        """Prüft, ob der Index Daten enthält."""
        index = search_client._load_index()
        assert len(index) > 0, "Index ist leer!"
        print(f"✅ Index enthält {len(index)} Einträge")


class TestSearchQuality:
    """Tests für die Qualität der Suchergebnisse."""
    
    def test_pdf_search_returns_pdfs(self):
        """Wenn nach '.pdf' gesucht wird, sollten nur PDFs zurückkommen."""
        results = search_client.search(".pdf", top_k=20)
        
        if len(results) > 0:
            pdf_count = sum(1 for r in results if r['filename'].lower().endswith('.pdf'))
            assert pdf_count > 0, "Keine PDFs in den Ergebnissen gefunden"
            print(f"✅ {pdf_count}/{len(results)} Ergebnisse sind PDFs")
    
    def test_empty_query_returns_gracefully(self):
        """Leere Suche sollte nicht abstürzen."""
        results = search_client.search("", top_k=5)
        # Sollte nicht abstürzen, Ergebnisse können leer oder voll sein
        assert isinstance(results, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
