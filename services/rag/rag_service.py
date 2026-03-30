import os
import ollama
import chromadb
from sentence_transformers import SentenceTransformer

BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
DB_PATH    = os.path.join(BASE_DIR, "chroma_db")

embedder   = SentenceTransformer("all-MiniLM-L6-v2")
chroma     = chromadb.PersistentClient(path=DB_PATH)
collection = chroma.get_or_create_collection("saturday_docs")

OLLAMA_MODEL = "llama3.2:1b"

# ── Chunk text ────────────────────────────────────────────────
def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50):
    words  = text.split()
    chunks = []
    i      = 0
    while i < len(words):
        chunk = " ".join(words[i:i + chunk_size])
        chunks.append(chunk)
        i += chunk_size - overlap
    return chunks

# ── Add document ──────────────────────────────────────────────
def add_document(doc_id: str, text: str, metadata: dict = {}):
    chunks     = chunk_text(text)
    ids        = [f"{doc_id}_chunk_{i}" for i in range(len(chunks))]
    embeddings = embedder.encode(chunks).tolist()
    collection.upsert(
        ids        = ids,
        documents  = chunks,
        embeddings = embeddings,
        metadatas  = [{"source": doc_id, **metadata}] * len(chunks)
    )
    return len(chunks)

# ── Add text file ─────────────────────────────────────────────
def add_text_file(filepath: str):
    with open(filepath, "r", encoding="utf-8") as f:
        text = f.read()
    doc_id = os.path.basename(filepath)
    return add_document(doc_id, text, {"type": "text_file"})

# ── Add PDF ───────────────────────────────────────────────────
def add_pdf(filepath: str):
    import PyPDF2
    text = ""
    with open(filepath, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted + "\n"
    if not text.strip():
        return {"error": "Could not extract text from PDF. Try a text-based PDF."}
    doc_id = os.path.basename(filepath)
    return add_document(doc_id, text, {"type": "pdf"})

# ── Search ────────────────────────────────────────────────────
def search(query: str, n_results: int = 3):
    embedding = embedder.encode([query]).tolist()
    results   = collection.query(
        query_embeddings = embedding,
        n_results        = n_results
    )
    return results.get("documents", [[]])[0]

# ── Ask using RAG + Ollama ────────────────────────────────────
def ask(query: str) -> str:
    relevant_chunks = search(query)
    if not relevant_chunks:
        return "I don't have any documents to answer from. Upload your CV with `!rag add` (attach the file)."

    context = "\n\n".join(relevant_chunks)
    prompt  = (
        f"You are Saturday, a personal assistant. "
        f"Answer the question using ONLY the context below.\n"
        f"If the answer is not in the context, say 'I don't know'.\n\n"
        f"Context:\n{context}\n\n"
        f"Question: {query}\n\n"
        f"Answer concisely in 2-3 sentences."
    )
    response = ollama.chat(
        model    = OLLAMA_MODEL,
        messages = [{"role": "user", "content": prompt}]
    )
    return response["message"]["content"]

# ── List documents ────────────────────────────────────────────
def list_documents():
    results = collection.get()
    sources = set()
    for meta in results.get("metadatas", []):
        if meta:
            sources.add(meta.get("source", "unknown"))
    return list(sources)

# ── Delete document ───────────────────────────────────────────
def delete_document(doc_id: str):
    results      = collection.get()
    ids_to_delete = [
        id_ for id_, meta in zip(results["ids"], results["metadatas"])
        if meta and meta.get("source") == doc_id
    ]
    if ids_to_delete:
        collection.delete(ids=ids_to_delete)
        return True
    return False