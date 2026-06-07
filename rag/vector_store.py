import faiss
import os
import pickle
import numpy as np
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings

load_dotenv()

VECTOR_DIM = 1536
INDEX_FILE = "rag/faiss.index"
META_FILE = "rag/metadata.pkl"

embeddings = OpenAIEmbeddings()


# Load or create FAISS index
if os.path.exists(INDEX_FILE):
    index = faiss.read_index(INDEX_FILE)
    with open(META_FILE, "rb") as f:
        metadata = pickle.load(f)
else:
    index = faiss.IndexFlatL2(VECTOR_DIM)
    metadata = []


def _to_faiss_vector(vector):
    """
    Convert list embedding to FAISS-compatible numpy array
    """
    return np.array(vector, dtype="float32").reshape(1, -1)


def add_memory(text: str, meta: dict):
    print("[FAISS] add_memory() called")

    vector = embeddings.embed_query(text)
    vector_np = _to_faiss_vector(vector)

    index.add(vector_np)
    metadata.append(meta)

    faiss.write_index(index, INDEX_FILE)
    with open(META_FILE, "wb") as f:
        pickle.dump(metadata, f)

    print("[FAISS] Memory written to disk")


def query_memory(query: str, k: int = 3):
    if index.ntotal == 0:
        return []

    vector = embeddings.embed_query(query)
    vector_np = _to_faiss_vector(vector)

    distances, indices = index.search(vector_np, k)

    results = []
    for idx in indices[0]:
        if idx < len(metadata):
            results.append(metadata[idx])

    return results
