from ingestion.document_loader import load_all_documents
from ingestion.chunking import chunk_all_documents
from azure_client import create_embedding

documents = load_all_documents()
chunks = chunk_all_documents(documents)

print(f"Loaded {len(documents)} documents.")
print(f"Created {len(chunks)} chunks.\n")

for chunk in chunks:
    print(f"Creating embedding for: {chunk['chunk_id']}")

    embedding = create_embedding(chunk["content"])

    chunk["embedding"] = embedding

    print(f"Vector dimensions: {len(embedding)}")
    print(f"First 5 values: {embedding[:5]}")
    print()

print("All embeddings created successfully.")