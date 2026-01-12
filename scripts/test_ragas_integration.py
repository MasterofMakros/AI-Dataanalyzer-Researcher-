"""
Test Ragas Integration with Local Ollama (Qwen 2.5)
"""

def main() -> None:
    from ragas import evaluate
    from ragas.metrics import (
        faithfulness,
        answer_relevancy,
        context_precision,
        context_recall,
    )
    from datasets import Dataset
    from langchain_community.chat_models import ChatOllama
    from langchain_community.embeddings import OllamaEmbeddings

    # 1. Konfiguration für lokales LLM + Embeddings
    # Ragas nutzt standardmäßig OpenAI. Wir überschreiben das mit LangChain Wrappern.

    llm = ChatOllama(model="qwen3:8b", temperature=0, base_url="http://localhost:11435")
    embeddings = OllamaEmbeddings(model="nomic-embed-text", base_url="http://localhost:11435")

    # 2. Test-Datensatz
    # Ragas benötigt: question, answer, contexts, ground_truth (optional für einige Metriken)
    data_samples = {
        "question": ["Was ist das Neural Vault Projekt?"],
        "answer": ["Das Neural Vault Projekt ist ein lokales Archiv-System mit KI-gestützter Organisation."],
        "contexts": [
            [
                "Neural Vault ist ein Projekt zur Transformation eines passiven 10TB-Archivs in ein aktives, "
                "durchsuchbares System mittels lokaler KI auf einem Ryzen AI Node."
            ]
        ],
        "ground_truth": ["Neural Vault transformiert ein 10TB Archiv in ein aktives System mittels lokaler KI."],
    }

    dataset = Dataset.from_dict(data_samples)

    # 3. Evaluation
    # Wir übergeben explizit das llm und embeddings an die Metriken oder die evaluate Funktion
    # Hinweis: Ragas API ändert sich häufig, wir prüfen die aktuelle Methode.

    print("Starte Ragas Evaluation mit lokalem Qwen 2.5...")

    try:
        results = evaluate(
            dataset,
            metrics=[
                faithfulness,
                answer_relevancy,
                context_precision,
                context_recall,
            ],
            llm=llm,
            embeddings=embeddings,
        )

        print("\nErgebnisse:")
        print(results)
    except Exception as e:
        print(f"\nFehler bei der Evaluation: {e}")
        # Fallback für Debugging
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
