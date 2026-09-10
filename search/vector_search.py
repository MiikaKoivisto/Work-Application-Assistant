import os
import streamlit as st

from dotenv import load_dotenv
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery

from azure_client import create_embedding

load_dotenv()


def get_setting(name):
    try:
        if name in st.secrets:
            return st.secrets[name]
    except Exception:
        pass

    return os.getenv(name)


search_endpoint = get_setting("AZURE_SEARCH_ENDPOINT")
index_name = get_setting("AZURE_SEARCH_INDEX")
search_api_key = get_setting("AZURE_SEARCH_API_KEY")


if not search_endpoint:
    raise ValueError("AZURE_SEARCH_ENDPOINT is missing.")

if not index_name:
    raise ValueError("AZURE_SEARCH_INDEX is missing.")

if not search_api_key:
    raise ValueError("AZURE_SEARCH_API_KEY is missing.")


credential = AzureKeyCredential(search_api_key)

search_client = SearchClient(
    endpoint=search_endpoint,
    index_name=index_name,
    credential=credential
)


def vector_search(question, top_k=3):
    question_embedding = create_embedding(question)

    vector_query = VectorizedQuery(
        vector=question_embedding,
        k_nearest_neighbors=top_k,
        fields="embedding"
    )

    results = search_client.search(
        search_text=None,
        vector_queries=[vector_query],
        select=[
            "chunk_id",
            "title",
            "product",
            "category",
            "content",
            "source",
            "source_url"
        ],
        top=top_k
    )

    return list(results)


def hybrid_search(question, top_k=3):
    question_embedding = create_embedding(question)

    vector_query = VectorizedQuery(
        vector=question_embedding,
        k_nearest_neighbors=top_k,
        fields="embedding"
    )

    results = search_client.search(
        search_text=question,
        vector_queries=[vector_query],
        select=[
            "chunk_id",
            "title",
            "product",
            "category",
            "content",
            "source",
            "source_url"
        ],
        top=top_k
    )

    return list(results)


if __name__ == "__main__":
    question = (
        "My colleague needs to see what I'm doing on my computer. "
        "How can I show it to them?"
    )

    print(f"\nQuestion: {question}\n")

    results = hybrid_search(question)

    for index, result in enumerate(results, start=1):
        print("=" * 70)
        print(f"Result #{index}")
        print(f"Score: {result['@search.score']}")
        print(f"Product: {result['product']}")
        print(f"Category: {result['category']}")
        print(f"Title: {result['title']}")
        print()
        print(result["content"])
        print()