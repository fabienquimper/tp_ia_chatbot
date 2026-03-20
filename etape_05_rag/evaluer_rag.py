"""
Étape 05 — Évaluation du RAG
Mesure le Hit Rate et la qualité des réponses sur un jeu de questions.
"""
import os, json, time
from dotenv import load_dotenv
import openai
import chromadb
from chromadb.utils import embedding_functions

load_dotenv()

API_KEY = os.environ.get("OPENAI_API_KEY", "sk-changeme")
MODEL = os.environ.get("MODEL", "gpt-4o-mini")
CHROMA_PATH = os.environ.get("CHROMA_PATH", "./chroma_db")
QUESTIONS_FILE = "questions_eval.json"
COLLECTION_NAME = "techcorp_docs"

client = openai.OpenAI(api_key=API_KEY)

def load_collection():
    chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
    ef = embedding_functions.DefaultEmbeddingFunction()
    return chroma_client.get_collection(name=COLLECTION_NAME, embedding_function=ef)

def retrieve(collection, query, n=3):
    results = collection.query(query_texts=[query], n_results=n)
    return results["documents"][0], [m["source"] for m in results["metadatas"][0]]

def ask_rag(collection, question: str) -> tuple[str, list[str]]:
    docs, sources = retrieve(collection, question)
    context = "\n\n".join(docs)
    system = f"""Tu es l'assistant TechCorp. Réponds en te basant uniquement sur ce contexte.
Si la réponse n'est pas dans le contexte, réponds "NON_TROUVE".
Contexte : {context}"""
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": question}
        ]
    )
    return response.choices[0].message.content, sources

def evaluate():
    print("=== Évaluation du RAG — Étape 05 ===\n")

    with open(QUESTIONS_FILE, "r", encoding="utf-8") as f:
        questions = json.load(f)

    try:
        collection = load_collection()
    except Exception as e:
        print(f"✗ Erreur ChromaDB : {e}")
        print("  Lancez d'abord : python indexer.py")
        return

    results = []
    hits = 0

    for i, qa in enumerate(questions):
        q = qa["question"]
        expected_kws = [kw.lower() for kw in qa["expected_keywords"]]
        print(f"[{i+1}/{len(questions)}] {q}")

        try:
            answer, sources = ask_rag(collection, q)
            answer_lower = answer.lower()
            found_kws = [kw for kw in expected_kws if kw in answer_lower]
            hit = len(found_kws) >= max(1, len(expected_kws) // 2)
            if hit:
                hits += 1

            results.append({
                "question": q,
                "answer": answer,
                "sources": sources,
                "expected_keywords": qa["expected_keywords"],
                "found_keywords": found_kws,
                "hit": hit,
                "category": qa.get("category", "general")
            })

            status = "✓" if hit else "✗"
            print(f"  {status} Mots-clés trouvés: {found_kws}")
            print(f"  Sources: {sources}")
        except Exception as e:
            print(f"  ✗ Erreur : {e}")
            results.append({"question": q, "hit": False, "error": str(e)})

    hit_rate = hits / len(questions) * 100
    print(f"\n{'='*50}")
    print(f"RÉSULTATS :")
    print(f"  Hit Rate : {hits}/{len(questions)} = {hit_rate:.1f}%")
    print(f"  Objectif : > 80%")
    print(f"  Statut   : {'✓ ATTEINT' if hit_rate >= 80 else '✗ À AMÉLIORER'}")

    # Résultats par catégorie
    categories = {}
    for r in results:
        cat = r.get("category", "general")
        if cat not in categories:
            categories[cat] = {"hits": 0, "total": 0}
        categories[cat]["total"] += 1
        if r.get("hit"):
            categories[cat]["hits"] += 1

    print(f"\nPar catégorie :")
    for cat, stats in categories.items():
        rate = stats["hits"] / stats["total"] * 100
        print(f"  {cat:15s} : {stats['hits']}/{stats['total']} = {rate:.0f}%")

    with open("eval_results.json", "w", encoding="utf-8") as f:
        json.dump({"hit_rate": hit_rate, "results": results}, f, ensure_ascii=False, indent=2)
    print(f"\nRésultats sauvegardés dans eval_results.json")

if __name__ == "__main__":
    evaluate()
