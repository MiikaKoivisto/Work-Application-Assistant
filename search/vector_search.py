import json
import re
from pathlib import Path

import faiss
import numpy as np
from rank_bm25 import BM25Okapi

from azure_client import create_embedding


INDEX_FOLDER = Path("local_index")
FAISS_INDEX_PATH = INDEX_FOLDER / "vectors.faiss"
CHUNKS_PATH = INDEX_FOLDER / "chunks.json"


# ---------------------------------------------------------
# Load local index
# ---------------------------------------------------------

if not FAISS_INDEX_PATH.exists():
    raise FileNotFoundError(
        f"FAISS index not found at {FAISS_INDEX_PATH}. "
        "Run: python -m search.build_local_index"
    )

if not CHUNKS_PATH.exists():
    raise FileNotFoundError(
        f"Chunk metadata not found at {CHUNKS_PATH}. "
        "Run: python -m search.build_local_index"
    )


faiss_index = faiss.read_index(str(FAISS_INDEX_PATH))

with open(CHUNKS_PATH, "r", encoding="utf-8") as file:
    chunks = json.load(file)


if faiss_index.ntotal != len(chunks):
    raise ValueError(
        "FAISS index and chunks.json contain different numbers of chunks."
    )


# ---------------------------------------------------------
# BM25 keyword index
# ---------------------------------------------------------

def tokenize(text):
    return re.findall(r"\w+", text.lower(), flags=re.UNICODE)


tokenized_corpus = [
    tokenize(chunk["content"])
    for chunk in chunks
]

bm25 = BM25Okapi(tokenized_corpus)


# ---------------------------------------------------------
# Access filtering
# ---------------------------------------------------------

def chunk_is_allowed(chunk, company_id, document_types=None):
    """
    A recruiter may access:
    1. Global applicant documents
    2. Documents belonging to their own company

    Optional document_types further restrict the search.
    """

    if not company_id:
        raise ValueError(
            "company_id is required for company-specific search."
        )

    allowed_company = (
        chunk["company_id"] == company_id
        or chunk["company_id"] == "global"
    )

    if not allowed_company:
        return False

    if document_types:
        if chunk["document_type"] not in document_types:
            return False

    return True


# ---------------------------------------------------------
# Vector search
# ---------------------------------------------------------

def vector_search(
    question,
    company_id,
    top_k=3,
    document_types=None
):
    question_embedding = create_embedding(question)

    query_vector = np.array(
        [question_embedding],
        dtype="float32"
    )

    faiss.normalize_L2(query_vector)

    # Search the complete local index.
    # Filtering is applied before results are returned.
    search_k = faiss_index.ntotal

    scores, indices = faiss_index.search(
        query_vector,
        search_k
    )

    results = []

    for score, index in zip(scores[0], indices[0]):

        if index < 0:
            continue

        chunk = chunks[index]

        if not chunk_is_allowed(
            chunk,
            company_id,
            document_types
        ):
            continue

        result = dict(chunk)

        # Keep the same key expected by rag.py
        result["@search.score"] = float(score)

        results.append(result)

        if len(results) >= top_k:
            break

    return results


# ---------------------------------------------------------
# Hybrid FAISS + BM25 search
# ---------------------------------------------------------

def hybrid_search(
    question,
    company_id,
    top_k=3,
    document_types=None
):
    question_embedding = create_embedding(question)

    query_vector = np.array(
        [question_embedding],
        dtype="float32"
    )

    faiss.normalize_L2(query_vector)

    # ---------- FAISS ----------

    vector_scores, vector_indices = faiss_index.search(
        query_vector,
        faiss_index.ntotal
    )

    vector_ranking = []

    for index in vector_indices[0]:

        if index < 0:
            continue

        chunk = chunks[index]

        if chunk_is_allowed(
            chunk,
            company_id,
            document_types
        ):
            vector_ranking.append(index)

    # ---------- BM25 ----------

    query_tokens = tokenize(question)

    keyword_scores = bm25.get_scores(query_tokens)

    keyword_indices = np.argsort(keyword_scores)[::-1]

    keyword_ranking = []

    for index in keyword_indices:

        index = int(index)
        chunk = chunks[index]

        if chunk_is_allowed(
            chunk,
            company_id,
            document_types
        ):
            keyword_ranking.append(index)

    # ---------- Reciprocal Rank Fusion ----------

    rrf_scores = {}

    # Standard RRF constant
    rrf_k = 60

    for rank, index in enumerate(vector_ranking, start=1):
        rrf_scores[index] = (
            rrf_scores.get(index, 0.0)
            + 1.0 / (rrf_k + rank)
        )

    for rank, index in enumerate(keyword_ranking, start=1):
        rrf_scores[index] = (
            rrf_scores.get(index, 0.0)
            + 1.0 / (rrf_k + rank)
        )

    ranked_indices = sorted(
        rrf_scores,
        key=rrf_scores.get,
        reverse=True
    )

    # Normalize scores so the best result is close to 1.0.
    # This also keeps rag.py's existing relevance threshold useful.
    if ranked_indices:
        max_score = rrf_scores[ranked_indices[0]]
    else:
        max_score = 1.0

    results = []

    for index in ranked_indices[:top_k]:

        result = dict(chunks[index])

        result["@search.score"] = float(
            rrf_scores[index] / max_score
        )

        results.append(result)

    return results


# ---------------------------------------------------------
# Manual test
# ---------------------------------------------------------

if __name__ == "__main__":

    company_id = "luovi"

    question = (
        "How does Miika's experience match this position?"
    )

    print(f"\nCompany: {company_id}")
    print(f"Question: {question}\n")

    results = hybrid_search(
        question,
        company_id=company_id,
        top_k=4
    )

    for index, result in enumerate(results, start=1):

        print("=" * 70)
        print(f"Result #{index}")
        print(f"Score: {result['@search.score']:.4f}")
        print(f"Company ID: {result['company_id']}")
        print(f"Document type: {result['document_type']}")
        print(f"Title: {result['title']}")
        print()
        print(result["content"][:500])
        print()