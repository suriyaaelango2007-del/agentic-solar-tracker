import faiss
import os
import pickle
import numpy as np
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings

load_dotenv()

VECTOR_DIM = 1536
FAULT_INDEX = "rag/fault_faiss.index"
FAULT_META = "rag/fault_metadata.pkl"

embeddings = OpenAIEmbeddings()

if os.path.exists(FAULT_INDEX):
    index = faiss.read_index(FAULT_INDEX)
    with open(FAULT_META, "rb") as f:
        metadata = pickle.load(f)
else:
    index = faiss.IndexFlatL2(VECTOR_DIM)
    metadata = []


def _vec(x):
    return np.array(x, dtype="float32").reshape(1, -1)


def store_fault(text: str, meta: dict):
    vec = embeddings.embed_query(text)
    index.add(_vec(vec))
    metadata.append(meta)

    faiss.write_index(index, FAULT_INDEX)
    with open(FAULT_META, "wb") as f:
        pickle.dump(metadata, f)


def retrieve_faults(query: str, k: int = 3):
    if index.ntotal == 0:
        return []

    vec = embeddings.embed_query(query)
    _, idxs = index.search(_vec(vec), k)

    return [metadata[i] for i in idxs[0] if i < len(metadata)]
