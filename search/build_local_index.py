import json
from pathlib import Path

import faiss
import numpy as np

from ingestion.document_loader import load_all_documents
from ingestion.chunking import chunk_all_documents
from azure_client import create_embedding


INDEX_FOLDER = Path("local_index")
FAISS_INDEX_PATH = INDEX_FOLDER / "vectors.faiss"
CHUNKS_PATH = INDEX_FOLDER / "chunks.json"


def build_local_index():
    INDEX_FOLDER.mkdir(parents=True, exist_ok=True)

    # 1. Load existing documents
    documents = load_all_documents()

    # 2. Use the existing chunking pipeline
    chunks = chunk_all_documents(documents)

    print(f"Loaded {len(documents)} documents.")
    print(f"Created {len(chunks)} chunks.\n")

    if not chunks:
        raise ValueError("No document chunks were created.")

    # 3. Create an embedding for each chunk
    embeddings = []

    for chunk in chunks:
        print(f"Creating embedding: {chunk['chunk_id']}")

        embedding = create_embedding(chunk["content"])
        embeddings.append(embedding)

    # 4. Convert embeddings to a FAISS-compatible NumPy array
    vectors = np.array(embeddings, dtype="float32")

    # Normalize vectors so inner product acts as cosine similarity
    faiss.normalize_L2(vectors)

    # 5. Create the FAISS vector index
    dimension = vectors.shape[1]
    index = faiss.IndexFlatIP(dimension)

    index.add(vectors)

    # 6. Save the vector index
    faiss.write_index(index, str(FAISS_INDEX_PATH))

    # 7. Save chunk text + metadata separately
    with open(CHUNKS_PATH, "w", encoding="utf-8") as file:
        json.dump(
            chunks,
            file,
            ensure_ascii=False,
            indent=2
        )

    print("\nLocal index created successfully.")
    print(f"FAISS vectors: {index.ntotal}")
    print(f"Vector dimensions: {dimension}")
    print(f"FAISS index: {FAISS_INDEX_PATH}")
    print(f"Chunk metadata: {CHUNKS_PATH}")


if __name__ == "__main__":
    build_local_index()