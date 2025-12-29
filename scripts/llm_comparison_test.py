"""
LLM Comparison Test: Llama3:8b vs Qwen3:8b
Vergleicht Geschwindigkeit, Genauigkeit und Output-Qualität
"""

import time
import json
import requests
from pathlib import Path
from datetime import datetime

OLLAMA_URL = "http://localhost:11435"

# Testfälle mit erwarteten Ergebnissen
TEST_CASES = [
    {
        "name": "Rechnung klassifizieren",
        "filename": "Rechnung_Bauhaus_2024.pdf",
        "text": """
        BAUHAUS Fachcentrum
        Rechnung Nr. 4521789
        Datum: 15.12.2024
        
        Artikel                  Menge    Preis
        Gartenschlauch 25m       1        29,99€
        Rasendünger 5kg          2        15,99€
        Pflanzerde 40L           3        8,99€
        
        Gesamtbetrag: 88,94€
        MwSt inkl.
        """,
        "expected_category": "Finanzen",
        "expected_subcategory": "Rechnung"
    },
    {
        "name": "Technische Doku klassifizieren",
        "filename": "API_Documentation_v2.md",
        "text": """
        # API Documentation
        
        ## Authentication
        All requests require Bearer token in Authorization header.
        
        ## Endpoints
        
        ### GET /api/users
        Returns list of all users with pagination.
        
        ### POST /api/documents
        Upload a new document. Supports PDF, DOCX, TXT.
        
        ## Rate Limits
        100 requests per minute per API key.
        """,
        "expected_category": "Technologie",
        "expected_subcategory": "Dokumentation"
    },
    {
        "name": "Privates Foto klassifizieren",
        "filename": "IMG_20241220_Barcelona.jpg",
        "text": "Dateiname: IMG_20241220_Barcelona.jpg, EXIF: GPS Barcelona, Datum: 20.12.2024",
        "expected_category": "Privat",
        "expected_subcategory": "Foto"
    },
    {
        "name": "E-Mail klassifizieren",
        "filename": "email_vodafone_vertrag.eml",
        "text": """
        Von: kundenservice@vodafone.de
        An: max.mustermann@gmail.com
        Betreff: Ihre Vertragsbestätigung
        
        Sehr geehrter Herr Mustermann,
        
        hiermit bestätigen wir Ihren Mobilfunkvertrag:
        Tarif: Red XL
        Monatlich: 49,99€
        Laufzeit: 24 Monate
        
        Mit freundlichen Grüßen
        Vodafone Kundenservice
        """,
        "expected_category": "Finanzen",
        "expected_subcategory": "Vertrag"
    },
    {
        "name": "Code-Datei klassifizieren",
        "filename": "data_processor.py",
        "text": """
        import pandas as pd
        from sqlalchemy import create_engine
        
        def process_data(df: pd.DataFrame) -> pd.DataFrame:
            # Clean and transform data
            df = df.dropna()
            df['date'] = pd.to_datetime(df['date'])
            return df.groupby('category').sum()
        
        if __name__ == '__main__':
            engine = create_engine('sqlite:///data.db')
            df = pd.read_sql('SELECT * FROM raw_data', engine)
            result = process_data(df)
            result.to_sql('processed_data', engine)
        """,
        "expected_category": "Technologie",
        "expected_subcategory": "Code"
    }
]

def create_prompt(text: str, filename: str) -> str:
    return f"""Du bist ein Datei-Klassifizierungssystem. Analysiere diese Datei und antworte NUR mit validem JSON.

Dateiname: {filename}
Inhalt (Auszug): {text[:1500]}

WICHTIG: Antworte AUSSCHLIESSLICH mit diesem JSON-Format, keine anderen Texte:
{{
    "category": "Technologie",
    "subcategory": "Dokumentation",
    "entity": "NeuralVault",
    "date": "",
    "confidence": 0.8,
    "meta_description": "Projektdokumentation für ein Datenmanagement-System",
    "tags": ["projekt", "dokumentation"]
}}

Wähle category aus: Finanzen, Arbeit, Privat, Medien, Dokumente, Technologie, Gesundheit, Reisen, Sonstiges
confidence muss zwischen 0.5 und 1.0 liegen (z.B. 0.75)"""

def test_model(model_name: str, test_case: dict) -> dict:
    """Teste ein Modell mit einem Testfall."""
    prompt = create_prompt(test_case["text"], test_case["filename"])
    
    start_time = time.time()
    
    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": model_name,
                "prompt": prompt,
                "stream": False,
                "format": "json"
            },
            timeout=120
        )
        
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            result_text = response.json().get("response", "{}")
            try:
                parsed = json.loads(result_text)
                
                # Bewertung
                category_correct = parsed.get("category", "").lower() == test_case["expected_category"].lower()
                subcategory_match = test_case["expected_subcategory"].lower() in parsed.get("subcategory", "").lower()
                confidence = parsed.get("confidence", 0)
                
                return {
                    "success": True,
                    "time_seconds": elapsed,
                    "category": parsed.get("category"),
                    "subcategory": parsed.get("subcategory"),
                    "confidence": confidence,
                    "meta_description": parsed.get("meta_description", "")[:100],
                    "category_correct": category_correct,
                    "subcategory_match": subcategory_match
                }
            except json.JSONDecodeError:
                return {
                    "success": False,
                    "time_seconds": elapsed,
                    "error": "JSON Parse Error",
                    "raw": result_text[:200]
                }
        else:
            return {
                "success": False,
                "time_seconds": elapsed,
                "error": f"HTTP {response.status_code}"
            }
    except Exception as e:
        return {
            "success": False,
            "time_seconds": time.time() - start_time,
            "error": str(e)
        }

def run_comparison():
    """Führe Vergleichstest durch."""
    models = ["llama3:8b", "qwen3:8b"]
    results = {model: [] for model in models}
    
    print("=" * 70)
    print("LLM VERGLEICHSTEST: Llama3:8b vs Qwen3:8b")
    print("=" * 70)
    print(f"Zeitpunkt: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Testfälle: {len(TEST_CASES)}")
    print()
    
    for test_case in TEST_CASES:
        print(f"\n📋 Test: {test_case['name']}")
        print(f"   Erwartet: {test_case['expected_category']} / {test_case['expected_subcategory']}")
        print("-" * 50)
        
        for model in models:
            print(f"   🤖 {model}...", end=" ", flush=True)
            result = test_model(model, test_case)
            results[model].append(result)
            
            if result["success"]:
                cat_icon = "✅" if result["category_correct"] else "❌"
                sub_icon = "✅" if result["subcategory_match"] else "⚠️"
                print(f"{result['time_seconds']:.1f}s | {cat_icon} {result['category']} | {sub_icon} {result['subcategory']} | Konfidenz: {result['confidence']:.0%}")
            else:
                print(f"❌ Fehler: {result.get('error', 'Unknown')}")
    
    # Zusammenfassung
    print("\n" + "=" * 70)
    print("ZUSAMMENFASSUNG")
    print("=" * 70)
    
    for model in models:
        model_results = results[model]
        successful = [r for r in model_results if r.get("success")]
        
        if successful:
            avg_time = sum(r["time_seconds"] for r in successful) / len(successful)
            accuracy = sum(1 for r in successful if r.get("category_correct")) / len(successful) * 100
            avg_confidence = sum(r.get("confidence", 0) for r in successful) / len(successful)
            error_rate = (len(model_results) - len(successful)) / len(model_results) * 100
            
            print(f"\n🤖 {model}")
            print(f"   Durchschnittliche Zeit: {avg_time:.1f}s")
            print(f"   Kategorie-Genauigkeit: {accuracy:.0f}%")
            print(f"   Durchschn. Konfidenz: {avg_confidence:.0%}")
            print(f"   Fehlerquote: {error_rate:.0f}%")
        else:
            print(f"\n🤖 {model}")
            print(f"   ❌ Alle Tests fehlgeschlagen")
    
    # Gewinner
    print("\n" + "=" * 70)
    llama_results = [r for r in results["llama3:8b"] if r.get("success")]
    qwen_results = [r for r in results["qwen3:8b"] if r.get("success")]
    
    if llama_results and qwen_results:
        llama_acc = sum(1 for r in llama_results if r.get("category_correct")) / len(llama_results)
        qwen_acc = sum(1 for r in qwen_results if r.get("category_correct")) / len(qwen_results)
        
        llama_time = sum(r["time_seconds"] for r in llama_results) / len(llama_results)
        qwen_time = sum(r["time_seconds"] for r in qwen_results) / len(qwen_results)
        
        print("VERGLEICH:")
        print(f"   Genauigkeit: Qwen3 {qwen_acc*100:.0f}% vs Llama3 {llama_acc*100:.0f}% → {'Qwen3 besser' if qwen_acc > llama_acc else 'Llama3 besser' if llama_acc > qwen_acc else 'Gleich'}")
        print(f"   Geschwindigkeit: Qwen3 {qwen_time:.1f}s vs Llama3 {llama_time:.1f}s → {'Qwen3 schneller' if qwen_time < llama_time else 'Llama3 schneller' if llama_time < qwen_time else 'Gleich'}")
        
        speed_diff = ((llama_time - qwen_time) / llama_time) * 100 if llama_time > 0 else 0
        acc_diff = (qwen_acc - llama_acc) * 100
        
        print(f"\n📊 LEISTUNGSZUWACHS QWEN3:")
        print(f"   Genauigkeit: {'+' if acc_diff >= 0 else ''}{acc_diff:.0f}%")
        print(f"   Geschwindigkeit: {'+' if speed_diff >= 0 else ''}{speed_diff:.0f}%")
    
    print("=" * 70)
    
    return results

if __name__ == "__main__":
    run_comparison()
