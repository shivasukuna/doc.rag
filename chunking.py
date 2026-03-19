def chunk_text(text, doc_id=None, source=None, page=None, chunk_size=400, overlap=100):
    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size

        chunk = text[start:end]

        chunks.append({
            "text": chunk,
            "doc_id": doc_id,
            "source": source,
            "page": page
        })

        start += chunk_size - overlap

    return chunks