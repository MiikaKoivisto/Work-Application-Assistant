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


def build_search_filter(
    company_id,
    document_types=None
):
    if not company_id:
        raise ValueError(
            "company_id is required for company-specific search."
        )

    safe_company_id = company_id.replace("'", "''")

    # Allow access to:
    # 1. The recruiter's company-specific documents
    # 2. Miika's global applicant documents

    search_filter = (
        f"(company_id eq '{safe_company_id}' "
        f"or company_id eq 'global')"
    )

    if document_types:
        type_filters = []

        for document_type in document_types:
            safe_type = document_type.replace("'", "''")

            type_filters.append(
                f"document_type eq '{safe_type}'"
            )

        search_filter += (
            " and ("
            + " or ".join(type_filters)
            + ")"
        )

    return search_filter


def vector_search(
    question,
    company_id,
    top_k=3,
    document_types=None
):
    question_embedding = create_embedding(question)

    vector_query = VectorizedQuery(
        vector=question_embedding,
        k_nearest_neighbors=top_k,
        fields="embedding"
    )

    results = search_client.search(
        search_text=None,
        vector_queries=[vector_query],
        filter=build_search_filter(company_id, document_types),
        select=[
            "chunk_id",
            "title",
            "company_id",
            "document_type",
            "content",
            "source",
            "source_url",
            "filename",
            "chunk_number"
        ],
        top=top_k
    )

    return list(results)


def hybrid_search(
    question,
    company_id,
    top_k=3,
    document_types=None
):
    question_embedding = create_embedding(question)

    vector_query = VectorizedQuery(
        vector=question_embedding,
        k_nearest_neighbors=top_k,
        fields="embedding"
    )

    results = search_client.search(
        search_text=question,
        vector_queries=[vector_query],
        filter=build_search_filter(company_id, document_types),
        select=[
            "chunk_id",
            "title",
            "company_id",
            "document_type",
            "content",
            "source",
            "source_url",
            "filename",
            "chunk_number"
        ],
        top=top_k
    )

    return list(results)


if __name__ == "__main__":
    company_id = "company_001"

    question = (
        "How does Miika's experience match the Senior AI Engineer position?"
    )

    print(f"\nCompany: {company_id}")
    print(f"Question: {question}\n")

    results = hybrid_search(
        question,
        company_id=company_id,
        top_k=3
    )

    for index, result in enumerate(results, start=1):
        print("=" * 70)
        print(f"Result #{index}")
        print(f"Score: {result['@search.score']}")
        print(f"Company ID: {result['company_id']}")
        print(f"Document type: {result['document_type']}")
        print(f"Title: {result['title']}")
        print()
        print(result["content"])
        print()