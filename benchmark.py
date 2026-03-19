from embedding_service import embed_texts
from vector_store import search
from reranker_service import rerank

# -----------------------------
# Define Evaluation Queries
# -----------------------------
test_queries = [
    {
        "query": "How does redstone work?",
        "expected_keywords": ["redstone"]
    },
    {
        "query": "How do you craft tools?",
        "expected_keywords": ["craft", "tool"]
    },
    {
        "query": "What are hostile mobs?",
        "expected_keywords": ["mob", "hostile"]
    },
    {
        "query": "Difference between survival and creative mode?",
        "expected_keywords": ["survival", "creative"]
    },
    {
        "query": "How does farming work?",
        "expected_keywords": ["farm", "crop"]
    }
]


def contains_expected(text, expected_keywords):
    text = text.lower()
    return any(keyword in text for keyword in expected_keywords)


def compute_mrr(results, expected_keywords):
    for rank, text in enumerate(results, start=1):
        if contains_expected(text, expected_keywords):
            return 1 / rank
    return 0


def evaluate():
    print("\n========== STRONG BENCHMARK ==========\n")

    p1_without = 0
    p1_with = 0
    mrr_without = 0
    mrr_with = 0

    total = len(test_queries)

    for test in test_queries:
        query = test["query"]
        expected_keywords = test["expected_keywords"]

        print(f"\nQuery: {query}")

        query_embedding = embed_texts([query])[0]

        # -------- WITHOUT RERANKER --------
        candidates = search(query_embedding, top_k=8)
        candidate_texts = [item["text"] for item in candidates]

        # Precision@1
        if contains_expected(candidate_texts[0], expected_keywords):
            p1_without += 1

        # MRR
        mrr_without += compute_mrr(candidate_texts, expected_keywords)

        # -------- WITH RERANKER --------
        reranked = rerank(query, candidate_texts, top_k=8)

        if contains_expected(reranked[0], expected_keywords):
            p1_with += 1

        mrr_with += compute_mrr(reranked, expected_keywords)

    print("\n========== RESULTS ==========")
    print(f"Total Queries: {total}")

    print("\nWITHOUT Reranker:")
    print(f"Precision@1: {p1_without}/{total} = {p1_without/total:.2f}")
    print(f"MRR: {mrr_without/total:.2f}")

    print("\nWITH Reranker:")
    print(f"Precision@1: {p1_with}/{total} = {p1_with/total:.2f}")
    print(f"MRR: {mrr_with/total:.2f}")

    improvement_p1 = (p1_with - p1_without)
    improvement_mrr = (mrr_with - mrr_without)

    print("\nImprovement:")
    print(f"Precision@1 change: {improvement_p1}")
    print(f"MRR change: {improvement_mrr:.2f}")

    print("\n================================\n")


if __name__ == "__main__":
    evaluate()
