import math
from typing import Any, Dict, List, Optional

from embedding_service import embed_texts
from vector_store import search
from reranker_service import rerank
from llm_service import generate_answer, generate_answer_stream


from bm25_service import bm25_search


FORMAT_RULES = """
Formatting Rules:
- Use clear section headings when explaining concepts.
- Keep paragraphs long and detailed.
- Use bullet points for lists.
- Add spacing between sections.
- Avoid large unbroken text blocks.
- Structure explanations cleanly.
- Avoid using Emojis
"""

NO_CONTEXT_FALLBACK = (
    "I could not find relevant information in the uploaded document "
    "to answer this question."
)


def build_rag_prompt(query, conversation_context, context):
    return f"""
You are a STRICT document-grounded assistant.

CRITICAL RULES:
- You MUST answer ONLY using the DOCUMENT CONTEXT.
- You are NOT allowed to use any outside knowledge.
- If the answer is not present in the DOCUMENT CONTEXT, say:
  "The document does not contain enough information to answer this."

- Do NOT guess.
- Do NOT add external knowledge.
- Do NOT complete missing details.

However:
- You may rephrase the document for clarity.
- You may simplify explanations.

{FORMAT_RULES}

CONVERSATION HISTORY:
{conversation_context}

DOCUMENT CONTEXT:
{context}

USER QUESTION:
{query}

ANSWER:
"""


def sigmoid(x: float) -> float:
    return 1 / (1 + math.exp(-x))


def build_chat_prompt(query, conversation_context):
    return f"""
You are a helpful AI assistant.

Instructions:
- Answer naturally and conversationally.
- Do not rely on document context.
- Maintain conversation flow.

{FORMAT_RULES}

CONVERSATION HISTORY:
{conversation_context}

USER MESSAGE:
{query}

ANSWER:
"""


def _build_conversation_context(history: Optional[List[Dict[str, str]]]) -> str:
    if not history:
        return ""

    trimmed_history = history[-10:]
    lines = []

    for msg in trimmed_history:
        role = "User" if msg.get("role") == "user" else "Assistant"
        content = msg.get("content", "").strip()
        if content:
            lines.append(f"{role}: {content}")

    return "\n\n".join(lines)


def _build_retrieval_query(query: str, history: Optional[List[Dict[str, str]]]) -> str:
    """
    For very short follow-up queries like:
    - 'explain more'
    - 'why'
    - 'how'
    - 'example?'

    anchor using recent USER turns only, not assistant text.
    """
    if not history:
        return query

    FOLLOW_UP_WORD_LIMIT = 3
    is_follow_up = len(query.split()) <= FOLLOW_UP_WORD_LIMIT

    if not is_follow_up:
        return query

    recent_user_messages = [
        msg.get("content", "").strip()
        for msg in history[-6:]
        if msg.get("role") == "user" and msg.get("content", "").strip()
    ]

    if not recent_user_messages:
        return query

    # Keep it compact: include only last 1–2 user turns
    anchor_parts = recent_user_messages[-2:]
    anchored_query = " ".join(anchor_parts + [query]).strip()
    return anchored_query


def _normalize_vector_similarity(similarity: float) -> float:
    """
    Assumes similarity is cosine-like in range roughly [0,1].
    Clamp for safety.
    """
    return max(0.0, min(1.0, similarity))


def _normalize_rerank_score(score: float) -> float:
    """
    Reranker score ranges vary by model.
    Sigmoid gives a stable 0..1 normalization.
    """
    return sigmoid(score)




def _retrieve_context(
    query: str,
    doc_id: Optional[str] = None,
    history: Optional[List[Dict[str, str]]] = None,
    search_top_k: int = 20,
    final_top_k: int = 3,
) -> Dict[str, Any]:

    conversation_context = _build_conversation_context(history)
    retrieval_query = _build_retrieval_query(query, history)

    # -----------------------------
    # EMBEDDING
    # -----------------------------
    query_embedding = embed_texts([retrieval_query])[0]

    # -----------------------------
    # DENSE SEARCH (FAISS)
    # -----------------------------
    dense_candidates = search(query_embedding, top_k=search_top_k) or []

    if doc_id:
        dense_candidates = [
            item for item in dense_candidates
            if item.get("doc_id") == doc_id
        ]

    for item in dense_candidates:
        sim = float(item.get("similarity", 0.0))
        item["hybrid_score"] = 0.6 * max(0.0, min(1.0, sim))

    # -----------------------------
    # BM25 SEARCH (KEYWORD)
    # -----------------------------
    bm25_candidates = bm25_search(query, doc_id=doc_id, top_k=search_top_k)

    for item in bm25_candidates:
        item["hybrid_score"] = 0.4 * float(item.get("score", 0.0))

    # -----------------------------
    # MERGE + DEDUP
    # -----------------------------
    all_candidates = dense_candidates + bm25_candidates

    if not all_candidates:
        return {
            "conversation_context": conversation_context,
            "context": "NO_DOCUMENT_CONTEXT",
            "sources": [],
            "confidence": 0.0,
            "chunks": [],
        }

    seen = set()
    unique_candidates = []

    for item in all_candidates:
        key = item["text"]
        if key not in seen:
            seen.add(key)
            unique_candidates.append(item)

    # -----------------------------
    # SORT BY HYBRID SCORE
    # -----------------------------
    unique_candidates.sort(
        key=lambda x: x.get("hybrid_score", 0.0),
        reverse=True
    )

    candidates = unique_candidates[:search_top_k]

    # -----------------------------
    # RERANK (FINAL SELECTION)
    # -----------------------------
    candidate_texts = [item["text"] for item in candidates]

    reranked = rerank(
        query,
        candidate_texts,
        top_k=min(final_top_k, len(candidate_texts))
    )

    # -----------------------------
    # MAP TEXT → ORIGINAL ITEMS
    # -----------------------------
    text_to_items: Dict[str, List[Dict[str, Any]]] = {}
    for item in candidates:
        text_to_items.setdefault(item["text"], []).append(item)

    best_chunks: List[str] = []
    confidence_scores: List[float] = []
    sources_set = set()
    selected_chunks = []

    for text, rerank_score in reranked:
        item_list = text_to_items.get(text, [])
        if not item_list:
            continue

        item = item_list.pop(0)
        best_chunks.append(text)
        selected_chunks.append(item)

        # -----------------------------
        # CONFIDENCE CALCULATION
        # -----------------------------
        hybrid_score = float(item.get("hybrid_score", 0.0))
        rerank_conf = _normalize_rerank_score(float(rerank_score))

        combined_conf = 0.5 * hybrid_score + 0.5 * rerank_conf
        confidence_scores.append(combined_conf)

        # -----------------------------
        # SOURCE TRACKING
        # -----------------------------
        source_file = item.get("source") or item.get("file")
        source_page = item.get("page")

        if source_file is not None and source_page is not None:
            sources_set.add((source_file, source_page))
        elif source_file is not None:
            sources_set.add((source_file, -1))

    # -----------------------------
    # FINAL CONTEXT
    # -----------------------------
    context = "\n\n".join(best_chunks).strip()

    if not context:
        context = "NO_DOCUMENT_CONTEXT"

    final_confidence = (
        round(sum(confidence_scores) / len(confidence_scores), 3)
        if confidence_scores else 0.0
    )

    sources = [
        {"file": source, "page": None if page == -1 else page}
        for source, page in sorted(sources_set)
    ]

    return {
        "conversation_context": conversation_context,
        "context": context,
        "sources": sources,
        "confidence": final_confidence,
        "chunks": selected_chunks,
    }


def answer_query(query: str, doc_id=None, history=None):
    retrieval = _retrieve_context(query=query, doc_id=doc_id, history=history)

    print("\n========== RAG DEBUG ==========")
    print("Query:", query)
    print("Context preview:", retrieval["context"][:200])
    print("Confidence:", retrieval["confidence"])
    print("Sources:", retrieval["sources"])
    print("================================\n")

    # 🔥 If context weak → CHAT
    if retrieval["confidence"]  == "NO_DOCUMENT_CONTEXT":

        prompt = build_chat_prompt(
            query=query,
            conversation_context=retrieval["conversation_context"]
        )

        answer = generate_answer(prompt)

        return {
            "answer": answer,
            "sources": [],
            "confidence": retrieval["confidence"],
        }

    # 🔥 Strong context → STRICT RAG
    prompt = build_rag_prompt(
        query=query,
        conversation_context=retrieval["conversation_context"],
        context=retrieval["context"],
    )

    answer = generate_answer(prompt)

    return {
        "answer": answer,
        "sources": retrieval["sources"],
        "confidence": retrieval["confidence"],
    }

def answer_query_stream(query: str, doc_id=None, history=None):
    retrieval = _retrieve_context(query=query, doc_id=doc_id, history=history)

    print("\n========== RAG DEBUG ==========")
    print("Query:", query)
    print("Context preview:", retrieval["context"][:200])
    print("Confidence:", retrieval["confidence"])
    print("Sources:", retrieval["sources"])
    print("================================\n")

    if retrieval["confidence"] == "NO_DOCUMENT_CONTEXT":

        prompt = build_chat_prompt(
            query=query,
            conversation_context=retrieval["conversation_context"]
        )

    else:
        prompt = build_rag_prompt(
            query=query,
            conversation_context=retrieval["conversation_context"],
            context=retrieval["context"],
        )

    for token in generate_answer_stream(prompt):
        yield token