from rank_bm25 import BM25Okapi
import re

# -----------------------------
# GLOBAL STORAGE
# -----------------------------
bm25_indices = {}   # doc_id -> BM25 index
bm25_metadata = {}  # doc_id -> list of chunks


# -----------------------------
# TOKENIZER (🔥 CRITICAL FIX)
# -----------------------------
def tokenize(text: str):
    # Lowercase + remove punctuation + split cleanly
    return re.findall(r"\w+", text.lower())


# -----------------------------
# BUILD INDEX
# -----------------------------
def build_bm25_index(doc_id, chunks):

    tokenized_corpus = [
        tokenize(chunk["text"]) for chunk in chunks
    ]

    bm25_indices[doc_id] = BM25Okapi(tokenized_corpus)
    bm25_metadata[doc_id] = chunks

    print(f"[BM25] Built index for doc_id={doc_id}, chunks={len(chunks)}")


# -----------------------------
# DELETE INDEX
# -----------------------------
def delete_bm25_index(doc_id):
    bm25_indices.pop(doc_id, None)
    bm25_metadata.pop(doc_id, None)
    print(f"[BM25] Deleted index for doc_id={doc_id}")


# -----------------------------
# SEARCH
# -----------------------------
def bm25_search(query, doc_id=None, top_k=10):

    tokenized_query = tokenize(query)

    results = []

    # -----------------------------
    # SINGLE DOCUMENT
    # -----------------------------
    if doc_id:
        index = bm25_indices.get(doc_id)
        metadata = bm25_metadata.get(doc_id)

        if not index:
            return []

        scores = index.get_scores(tokenized_query)

        max_score = max(scores) if scores.any() else 1

        for i, score in enumerate(scores):
            item = metadata[i]

            normalized_score = float(score) / max_score if max_score > 0 else 0

            results.append({
                "text": item["text"],
                "score": normalized_score,   # 🔥 normalized
                "source": item.get("source"),
                "page": item.get("page"),
                "doc_id": doc_id
            })

    # -----------------------------
    # MULTI DOCUMENT
    # -----------------------------
    else:
        for d_id, index in bm25_indices.items():
            metadata = bm25_metadata[d_id]

            scores = index.get_scores(tokenized_query)
            max_score = max(scores) if scores.any() else 1

            for i, score in enumerate(scores):
                item = metadata[i]

                normalized_score = float(score) / max_score if max_score > 0 else 0

                results.append({
                    "text": item["text"],
                    "score": normalized_score,
                    "source": item.get("source"),
                    "page": item.get("page"),
                    "doc_id": d_id
                })

    # -----------------------------
    # SORT + DEBUG
    # -----------------------------
    results.sort(key=lambda x: x["score"], reverse=True)

    print(f"[BM25] Query: {query}")
    print(f"[BM25] Top matches: {[r['text'][:50] for r in results[:3]]}")

    return results[:top_k]