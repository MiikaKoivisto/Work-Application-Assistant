from search.vector_search import hybrid_search
from azure_client import ask_ai


MIN_RELEVANCE_SCORE = 0.02


def ask_rag(question):
    results = hybrid_search(question, top_k=2)

    # Remove results that are probably unrelated
    relevant_results = [
        result
        for result in results
        if result["@search.score"] >= MIN_RELEVANCE_SCORE
    ]

    # Nothing relevant was found
    if not relevant_results:
        return {
            "answer": (
                "I couldn't find relevant information in the "
                "Microsoft 365 support knowledge base."
            ),
            "sources": [],
            "retrieved_chunks": []
        }

    context_parts = []

    for result in relevant_results:
        context_parts.append(
            f"""
Title: {result['title']}
Product: {result['product']}
Category: {result['category']}
Source: {result['source']}

{result['content']}
"""
        )

    context = "\n---\n".join(context_parts)

    messages = [
        {
            "role": "system",
            "content": (
                "You are a Microsoft 365 support assistant. "
                "Answer the user's question using only the provided context. "
                "If the context does not contain enough information, say that "
                "you don't have enough information to answer. "
                "Do not invent instructions or facts."
            )
        },
        {
            "role": "user",
            "content": f"""
CONTEXT:

{context}

QUESTION:

{question}
"""
        }
    ]

    answer = ask_ai(messages)

    # Create unique source list
    sources = []
    seen_sources = set()

    for result in relevant_results:
        source_key = result["source_url"]

        if source_key not in seen_sources:
            sources.append({
                "title": result["title"],
                "product": result["product"],
                "category": result["category"],
                "url": result["source_url"]
            })

            seen_sources.add(source_key)

    # Debug information
    retrieved_chunks = []

    for result in relevant_results:
        retrieved_chunks.append({
            "chunk_id": result["chunk_id"],
            "score": result["@search.score"],
            "title": result["title"],
            "product": result["product"],
            "category": result["category"],
            "content": result["content"]
        })

    return {
        "answer": answer,
        "sources": sources,
        "retrieved_chunks": retrieved_chunks
    }