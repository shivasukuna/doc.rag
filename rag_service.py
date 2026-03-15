import math
from embedding_service import embed_texts
from vector_store import search
from reranker_service import rerank
from llm_service import generate_answer, generate_answer_stream


FORMAT_RULES = """
Formatting Rules:
- Use clear section headings when explaining concepts.
- Keep paragraphs short (2–4 lines max).
- Use bullet points for lists.
- Add spacing between sections.
- Avoid large unbroken text blocks.
- Structure explanations cleanly.
"""

def build_rag_prompt(query, conversation_context, context):

    prompt = f"""
You are a document-based assistant.

You MUST follow these rules:

1. If DOCUMENT CONTEXT contains relevant information, answer ONLY using that information.
2. Do NOT use outside knowledge.
3. If the answer is not present in DOCUMENT CONTEXT, say:
   "This information is not present in the uploaded documents."

4. Always prioritize DOCUMENT CONTEXT over general knowledge.

{FORMAT_RULES}

CONVERSATION HISTORY:
{conversation_context}

DOCUMENT CONTEXT:
{context}

USER QUESTION:
{query}

ANSWER:
"""

    return prompt
# -----------------------------
# Utility: Sigmoid normalization
# -----------------------------
def sigmoid(x):
    return 1 / (1 + math.exp(-x))


def answer_query(query: str, doc_id=None, history=None):

    conversation_context = ""
    last_assistant_message = None

    if history:
        trimmed_history = history[-10:]

        for msg in trimmed_history:
            role = "User" if msg["role"] == "user" else "Assistant"
            conversation_context += f"{role}: {msg['content']}\n\n"

        for msg in reversed(trimmed_history):
            if msg["role"] == "assistant":
                last_assistant_message = msg["content"]
                break


    FOLLOW_UP_WORD_LIMIT = 3
    is_follow_up = len(query.split()) <= FOLLOW_UP_WORD_LIMIT


    if is_follow_up and last_assistant_message:
        anchored_query = last_assistant_message + " " + query
        query_embedding = embed_texts([anchored_query])[0]
    else:
        query_embedding = embed_texts([query])[0]


    candidates = search(query_embedding, top_k=10)


    if doc_id:
        candidates = [
            item for item in candidates
            if item.get("doc_id") == doc_id
        ]


    best_similarity = candidates[0]["similarity"] if candidates else 0

    MIN_SIMILARITY = 0.65

    if best_similarity < MIN_SIMILARITY:
        candidates = []


    best_chunks = []
    sources_set = set()
    confidence_scores = []


    if candidates:

        candidate_texts = [item["text"] for item in candidates]

        reranked = rerank(query, candidate_texts, top_k=3)

        for text, rerank_score in reranked:
            best_chunks.append(text)


    context = "\n\n".join(best_chunks)

    if not context:
        context = "NO_DOCUMENT_CONTEXT"

    


    prompt = build_rag_prompt(query, conversation_context, context)


    answer = generate_answer(prompt)


    final_confidence = round(
        sum(confidence_scores) / len(confidence_scores),
        3
    ) if confidence_scores else 0.0


    sources = [
        {"file": source, "page": page}
        for source, page in sorted(sources_set, key=lambda x: x[1])
    ]


    return {
        "answer": answer,
        "sources": sources,
        "confidence": final_confidence
    }

def answer_query_stream(query: str, doc_id=None, history=None):

    conversation_context = ""
    last_assistant_message = None


    if history:

        trimmed_history = history[-10:]

        for msg in trimmed_history:
            role = "User" if msg["role"] == "user" else "Assistant"
            conversation_context += f"{role}: {msg['content']}\n\n"

        for msg in reversed(trimmed_history):
            if msg["role"] == "assistant":
                last_assistant_message = msg["content"]
                break


    FOLLOW_UP_WORD_LIMIT = 3
    is_follow_up = len(query.split()) <= FOLLOW_UP_WORD_LIMIT


    if is_follow_up and last_assistant_message:
        anchored_query = last_assistant_message + " " + query
        query_embedding = embed_texts([anchored_query])[0]
    else:
        query_embedding = embed_texts([query])[0]


    candidates = search(query_embedding, top_k=10)
    print("Candidates retrieved:", len(candidates))
    if candidates:
        print("Top similarity:", candidates[0]["similarity"])


    if doc_id:
        candidates = [
            item for item in candidates
            if item.get("doc_id") == doc_id
        ]


    best_similarity = candidates[0]["similarity"] if candidates else 0

    MIN_SIMILARITY = 0.65

    if best_similarity < MIN_SIMILARITY:
        candidates = []


    best_chunks = []


    if candidates:

        candidate_texts = [item["text"] for item in candidates]

        reranked = rerank(query, candidate_texts, top_k=3)

        for text, _ in reranked:
            best_chunks.append(text)

    context = "\n\n".join(best_chunks)

    print("Context length:", len(context))


    if not context:
        context = "NO_DOCUMENT_CONTEXT"


    prompt = build_rag_prompt(query, conversation_context, context)


    for token in generate_answer_stream(prompt):
        yield token
