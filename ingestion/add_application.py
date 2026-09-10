import argparse
import json
import os
import sys
import time
from pathlib import Path

from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from dotenv import load_dotenv

from azure_client import create_embedding
from ingestion.chunking import chunk_all_documents
from ingestion.document_loader import load_document


load_dotenv()


REQUIRED_FILES = (
    "company_info.txt",
    "position_info.txt",
    "applicant_match.txt",
)

EXPECTED_DOCUMENT_TYPES = {
    "company_info.txt": "company",
    "position_info.txt": "position",
    "applicant_match.txt": "applicant_match",
}


def get_search_client():
    search_endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
    index_name = os.getenv("AZURE_SEARCH_INDEX")
    search_api_key = os.getenv("AZURE_SEARCH_API_KEY")

    if not search_endpoint:
        raise ValueError("AZURE_SEARCH_ENDPOINT is missing.")

    if not index_name:
        raise ValueError("AZURE_SEARCH_INDEX is missing.")

    if not search_api_key:
        raise ValueError("AZURE_SEARCH_API_KEY is missing.")

    return SearchClient(
        endpoint=search_endpoint,
        index_name=index_name,
        credential=AzureKeyCredential(search_api_key),
    )


def load_config(company_folder):
    config_path = company_folder / "config.json"

    if not config_path.exists():
        raise FileNotFoundError(
            f"Missing required file: {config_path}"
        )

    try:
        with config_path.open("r", encoding="utf-8-sig") as file:
            config = json.load(file)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Invalid JSON in '{config_path}': {exc}"
        ) from exc

    company_id = str(config.get("company_id", "")).strip()
    aliases = config.get("aliases")

    if not company_id:
        raise ValueError(
            f"'{config_path}' is missing a non-empty 'company_id'."
        )

    if not isinstance(aliases, list) or not any(
        str(alias).strip() for alias in aliases
    ):
        raise ValueError(
            f"'{config_path}' must contain a non-empty 'aliases' list."
        )

    return config


def validate_and_load_documents(company_folder, company_id):
    documents = []

    for filename in REQUIRED_FILES:
        file_path = company_folder / filename

        if not file_path.exists():
            raise FileNotFoundError(
                f"Missing required file: {file_path}"
            )

        if file_path.stat().st_size == 0:
            raise ValueError(
                f"Required file is empty: {file_path}"
            )

        document = load_document(file_path)
        document["filename"] = filename

        required_metadata = (
            "title",
            "company_id",
            "document_type",
        )

        missing_metadata = [
            field
            for field in required_metadata
            if not document.get(field)
        ]

        if missing_metadata:
            raise ValueError(
                f"'{file_path}' is missing required metadata: "
                + ", ".join(missing_metadata)
            )

        document_company_id = document["company_id"].strip()

        if document_company_id != company_id:
            raise ValueError(
                f"COMPANY_ID mismatch in '{file_path}'. "
                f"Expected '{company_id}', "
                f"found '{document_company_id}'."
            )

        expected_type = EXPECTED_DOCUMENT_TYPES[filename]
        actual_type = document["document_type"].strip()

        if actual_type != expected_type:
            raise ValueError(
                f"DOCUMENT_TYPE mismatch in '{file_path}'. "
                f"Expected '{expected_type}', "
                f"found '{actual_type}'."
            )

        if not document.get("content", "").strip():
            raise ValueError(
                f"'{file_path}' does not contain document content."
            )

        documents.append(document)

    return documents


def create_embeddings(chunks):
    total = len(chunks)

    for index, chunk in enumerate(chunks, start=1):
        print(
            f"  [{index}/{total}] "
            f"Embedding {chunk['chunk_id']}"
        )

        chunk["embedding"] = create_embedding(
            chunk["content"]
        )

    return chunks


def get_existing_company_chunk_ids(search_client, company_id):
    safe_company_id = company_id.replace("'", "''")

    results = search_client.search(
        search_text="*",
        filter=f"company_id eq '{safe_company_id}'",
        select=["chunk_id"],
        top=1000,
    )

    return [
        result["chunk_id"]
        for result in results
    ]


def delete_existing_company_chunks(
    search_client,
    company_id,
):
    chunk_ids = get_existing_company_chunk_ids(
        search_client,
        company_id,
    )

    if not chunk_ids:
        return 0

    documents_to_delete = [
        {"chunk_id": chunk_id}
        for chunk_id in chunk_ids
    ]

    results = search_client.delete_documents(
        documents=documents_to_delete
    )

    failed = [
        result.key
        for result in results
        if not result.succeeded
    ]

    if failed:
        raise RuntimeError(
            "Failed to delete existing chunks: "
            + ", ".join(failed)
        )

    return len(chunk_ids)


def upload_chunks(search_client, chunks):
    results = search_client.upload_documents(
        documents=chunks
    )

    failed = [
        result.key
        for result in results
        if not result.succeeded
    ]

    if failed:
        raise RuntimeError(
            "Failed to upload chunks: "
            + ", ".join(failed)
        )

    return len(results)


def verify_company(
    search_client,
    company_id,
    retries=6,
    delay_seconds=2,
):
    safe_company_id = company_id.replace("'", "''")

    for attempt in range(1, retries + 1):

        results = list(
            search_client.search(
                search_text="*",
                filter=f"company_id eq '{safe_company_id}'",
                select=[
                    "chunk_id",
                    "company_id",
                    "document_type",
                ],
                top=1000,
            )
        )

        if results:
            wrong_company = [
                result["chunk_id"]
                for result in results
                if result.get("company_id") != company_id
            ]

            if wrong_company:
                raise RuntimeError(
                    "Verification failed: unexpected "
                    "company IDs were returned."
                )

            document_types = {
                result.get("document_type")
                for result in results
            }

            missing_types = (
                set(EXPECTED_DOCUMENT_TYPES.values())
                - document_types
            )

            if missing_types:
                raise RuntimeError(
                    "Verification failed: missing "
                    "document types: "
                    + ", ".join(sorted(missing_types))
                )

            return len(results)

        if attempt < retries:
            print(
                f"   Index not ready yet. "
                f"Retrying in {delay_seconds}s..."
            )
            time.sleep(delay_seconds)

    raise RuntimeError(
        f"Verification failed: no indexed documents "
        f"were found for '{company_id}' after "
        f"{retries} attempts."
    )


def ingest_application(company_id):
    project_root = Path(__file__).resolve().parents[1]
    company_folder = (
        project_root
        / "data"
        / "private"
        / "companies"
        / company_id
    )

    print()
    print("Work Application Assistant — Company Ingestion")
    print("=" * 48)
    print(f"Company ID: {company_id}")
    print(f"Folder:     {company_folder}")
    print()

    if not company_folder.exists():
        raise FileNotFoundError(
            f"Company folder does not exist: "
            f"{company_folder}"
        )

    print("1. Validating configuration...")
    config = load_config(company_folder)

    configured_company_id = (
        str(config["company_id"]).strip()
    )

    if configured_company_id != company_id:
        raise ValueError(
            f"Folder/company ID mismatch. "
            f"Command used '{company_id}', but "
            f"config.json contains "
            f"'{configured_company_id}'."
        )

    print("   ✓ config.json valid")
    print(
        "   ✓ aliases: "
        + ", ".join(config["aliases"])
    )

    print()
    print("2. Validating company documents...")
    documents = validate_and_load_documents(
        company_folder,
        company_id,
    )

    for document in documents:
        print(
            f"   ✓ {document['filename']} "
            f"({document['document_type']})"
        )

    print()
    print("3. Creating chunks...")
    chunks = chunk_all_documents(documents)

    if not chunks:
        raise RuntimeError(
            "No chunks were created."
        )

    print(f"   ✓ {len(chunks)} chunks created")

    print()
    print("4. Creating embeddings...")
    create_embeddings(chunks)
    print(
        f"   ✓ {len(chunks)} embeddings created"
    )

    print()
    print("5. Connecting to Azure AI Search...")
    search_client = get_search_client()
    print("   ✓ connected")

    print()
    print(
        f"6. Replacing existing '{company_id}' data..."
    )
    deleted_count = delete_existing_company_chunks(
        search_client,
        company_id,
    )
    print(
        f"   ✓ {deleted_count} old chunks removed"
    )

    print()
    print("7. Uploading new chunks...")
    uploaded_count = upload_chunks(
        search_client,
        chunks,
    )
    print(
        f"   ✓ {uploaded_count} chunks uploaded"
    )

    print()
    print("8. Verifying indexed data...")
    indexed_count = verify_company(
        search_client,
        company_id,
    )
    print(
        f"   ✓ {indexed_count} company chunks found"
    )
    print(
        "   ✓ required document types found"
    )
    print(
        "   ✓ company-scoped verification passed"
    )

    print()
    print("=" * 48)
    print(
        f"✓ Ingestion completed successfully "
        f"for '{company_id}'."
    )
    print()


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Validate, embed and upload one company "
            "application to Azure AI Search."
        )
    )

    parser.add_argument(
        "company_id",
        help=(
            "Company folder / stable company ID, "
            "for example: gofore"
        ),
    )

    args = parser.parse_args()

    company_id = args.company_id.strip().lower()

    try:
        ingest_application(company_id)
    except Exception as exc:
        print()
        print("=" * 48)
        print(f"ERROR: {exc}")
        print("=" * 48)
        print()
        sys.exit(1)


if __name__ == "__main__":
    main()
