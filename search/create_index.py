import os

from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SearchField,
    SearchFieldDataType,
    SimpleField,
    SearchableField,
    VectorSearch,
    HnswAlgorithmConfiguration,
    VectorSearchProfile
)

load_dotenv()

search_endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
index_name = os.getenv("AZURE_SEARCH_INDEX")

credential = DefaultAzureCredential()

index_client = SearchIndexClient(
    endpoint=search_endpoint,
    credential=credential
)


fields = [
    SimpleField(
        name="chunk_id",
        type=SearchFieldDataType.String,
        key=True
    ),

    SearchableField(
        name="content",
        type=SearchFieldDataType.String
    ),

    SearchableField(
        name="title",
        type=SearchFieldDataType.String
    ),

    SimpleField(
        name="product",
        type=SearchFieldDataType.String,
        filterable=True
    ),

    SimpleField(
        name="category",
        type=SearchFieldDataType.String,
        filterable=True
    ),

    SimpleField(
        name="source",
        type=SearchFieldDataType.String
    ),

    SimpleField(
        name="source_url",
        type=SearchFieldDataType.String
    ),

    SimpleField(
        name="filename",
        type=SearchFieldDataType.String
    ),

    SimpleField(
        name="chunk_number",
        type=SearchFieldDataType.Int32
    ),

    SearchField(
        name="embedding",
        type=SearchFieldDataType.Collection(
            SearchFieldDataType.Single
        ),
        searchable=True,
        vector_search_dimensions=1536,
        vector_search_profile_name="rag-vector-profile"
    )
]


vector_search = VectorSearch(
    algorithms=[
        HnswAlgorithmConfiguration(
            name="rag-hnsw"
        )
    ],
    profiles=[
        VectorSearchProfile(
            name="rag-vector-profile",
            algorithm_configuration_name="rag-hnsw"
        )
    ]
)


index = SearchIndex(
    name=index_name,
    fields=fields,
    vector_search=vector_search
)


# Delete the existing index so we start with clean data
existing_indexes = [
    existing_index.name
    for existing_index in index_client.list_indexes()
]

if index_name in existing_indexes:
    print(f"Deleting existing index '{index_name}'...")
    index_client.delete_index(index_name)

print(f"Creating index '{index_name}'...")

result = index_client.create_or_update_index(index)

print(f"Index '{result.name}' created successfully.")