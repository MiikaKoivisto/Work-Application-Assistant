from ingestion.document_loader import load_all_documents
from ingestion.chunking import chunk_all_documents

documents = load_all_documents()

chunks = chunk_all_documents(documents)

print(f"Loaded {len(documents)} documents.")
print(f"Created {len(chunks)} chunks.\n")

for chunk in chunks:
    print("=" * 60)
    print(f"Chunk ID: {chunk['chunk_id']}")
    print(f"Product: {chunk['product']}")
    print(f"Category: {chunk['category']}")
    print(f"Title: {chunk['title']}")
    print(f"Chunk: {chunk['chunk_number']}")
    print()
    print(chunk["content"][:300])
    print()