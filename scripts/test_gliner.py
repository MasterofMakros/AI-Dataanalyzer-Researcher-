
import time

# German PII Test Data
TEXT = """
Vertraulicher Bericht.
Mitarbeiter: Herr Dr. Stefan Müller hat am 28.12.2025 die Zugangskarte verloren.
Seine Kontoverbindung ist DE45 1001 0010 1234 5678 90 bei der Sparkasse Berlin.
Bitte sofort sperren. Geheimhaltungsstufe: INTERN.
Projekt: Operation "Roter Adler".
"""

# Labels we want to zero-shot detect
LABELS = ["person", "iban", "date", "classification", "project"]

def main() -> None:
    from gliner import GLiNER

    print("🚀 Loading GLiNER Model (urchade/gliner_small-v2.1)...")
    start_load = time.time()
    try:
        model = GLiNER.from_pretrained("urchade/gliner_small-v2.1")
    except Exception as e:
        print(f"Failed to load small model, trying base: {e}")
        model = GLiNER.from_pretrained("urchade/gliner_base")

    print(f"✅ Model Loaded in {time.time() - start_load:.2f}s")

    print(f"\n📄 Analyzing Text:\n{TEXT}")

    start_pred = time.time()
    entities = model.predict_entities(TEXT, LABELS)
    end_pred = time.time()

    print(f"\n🎯 Results ({end_pred - start_pred:.4f}s):")
    for entity in entities:
        print(f"   - [{entity['label'].upper()}] {entity['text']} (Score: {entity['score']:.2f})")

    # Verification Logic
    found_labels = [e['label'] for e in entities]
    if "person" in found_labels and "iban" in found_labels:
        print("\n✅ SUCCESS: Detected Critical PII (Person + IBAN).")
    else:
        print("\n⚠️ WARNING: Missed some PII.")


if __name__ == "__main__":
    main()
