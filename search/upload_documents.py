import os

from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.search.documents import SearchClient

from ingestion.document_loader import load_all_documents
from ingestion.chunking import chunk_all_documents
from azure_client import create_embedding


load_dotenv()

search_endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
index_name = os.getenv("AZURE_SEARCH_INDEX")

credential = DefaultAzureCredential()

search_client = SearchClient(
    endpoint=search_endpoint,
    index_name=index_name,
    credential=credential
)


# 1. Load documents
documents = load_all_documents()

# 2. Split documents into chunks
chunks = chunk_all_documents(documents)

print(f"Loaded {len(documents)} documents.")
print(f"Created {len(chunks)} chunks.\n")


# 3. Create an embedding for every chunk
for chunk in chunks:
    print(f"Creating embedding: {chunk['chunk_id']}")

    chunk["embedding"] = create_embedding(
        chunk["content"]
    )


# 4. Upload chunks to Azure AI Search
print("\nUploading chunks to Azure AI Search...")

results = search_client.upload_documents(
    documents=chunks
)


# 5. Check results
for result in results:
    print(
        f"{result.key}: "
        f"{'SUCCESS' if result.succeeded else 'FAILED'}"
    )

print("\nUpload complete.")