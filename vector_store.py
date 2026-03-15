import faiss
import numpy as np
import os
import pickle

INDEX_FILE = "faiss.index"
CHUNKS_FILE = "chunks.pkl"

# ---------------------------------
# Initialize
# ---------------------------------
dimension = 384  # must match embedding size
index = None
chunks = []


def initialize_index():
    global index, chunks

    if os.path.exists(INDEX_FILE):
        index = faiss.read_index(INDEX_FILE)
    else:
        index = faiss.IndexFlatIP(dimension)

    if os.path.exists(CHUNKS_FILE):
        with open(CHUNKS_FILE, "rb") as f:
            chunks = pickle.load(f)
    else:
        chunks = []


# Call on import
initialize_index()


# ---------------------------------
# Add Embeddings
# ---------------------------------
def add_embeddings(embeddings, metadata_list):
    global index, chunks

    vectors = np.array(embeddings).astype("float32")
    faiss.normalize_L2(vectors)

    index.add(vectors)

    chunks.extend(metadata_list)

    persist()


# ---------------------------------
# Search
# ---------------------------------
def search(query_vector, top_k=5):
    global index, chunks

    if index.ntotal == 0:
        return []

    query_vector = np.array([query_vector]).astype("float32")
    faiss.normalize_L2(query_vector)

    scores, indices = index.search(query_vector, top_k)

    results = []

    for score, idx in zip(scores[0], indices[0]):
        if idx < len(chunks):
            result = chunks[idx].copy()
            result["similarity"] = float(score)
            results.append(result)

    print("FAISS vectors:", index.ntotal)
    print("Total chunks:", len(chunks))

    return results


def rebuild_index_excluding_doc(doc_id):
    global index, chunks

    # Filter chunks
    new_chunks = [
        chunk for chunk in chunks
        if chunk["doc_id"] != doc_id
    ]

    # Recreate index
    index = faiss.IndexFlatIP(dimension)

    if new_chunks:
        vectors = []

        for chunk in new_chunks:
            vectors.append(chunk["embedding"])

        vectors = np.array(vectors).astype("float32")
        index.add(vectors)

    chunks = new_chunks

    persist()


# ---------------------------------
# Persist to Disk
# ---------------------------------
def persist():
    global index, chunks

    faiss.write_index(index, INDEX_FILE)

    with open(CHUNKS_FILE, "wb") as f:
        pickle.dump(chunks, f)

# ---------------------------------
# Delete Document
# ---------------------------------
def delete_document_embeddings(doc_id: str):
    global index, chunks

    before = len(chunks)

    # keep only chunks that are NOT this document
    new_chunks = [
        chunk for chunk in chunks
        if chunk["doc_id"] != doc_id
    ]

    removed = before - len(new_chunks)

    if removed == 0:
        print(f"[VECTOR STORE] No chunks found for doc_id={doc_id}")
        return 0

    # rebuild FAISS index
    index = faiss.IndexFlatIP(dimension)

    if new_chunks:
        vectors = np.array(
            [chunk["embedding"] for chunk in new_chunks]
        ).astype("float32")

        faiss.normalize_L2(vectors)

        index.add(vectors)

    chunks[:] = new_chunks

    persist()

    print(f"[VECTOR STORE] Removed {removed} chunks for doc_id={doc_id}")

    return removed