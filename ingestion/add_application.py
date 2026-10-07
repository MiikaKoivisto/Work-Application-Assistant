import argparse
import json
import sys
from pathlib import Path

from ingestion.document_loader import load_document
from search.build_local_index import build_local_index


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
    print("Work Application Assistant - Company Ingestion")
    print("=" * 48)
    print(f"Company ID: {company_id}")
    print(f"Folder:     {company_folder}")
    print()

    if not company_folder.exists():
        raise FileNotFoundError(
            f"Company folder does not exist: {company_folder}"
        )

    print("1. Validating configuration...")
    config = load_config(company_folder)

    configured_company_id = str(
        config["company_id"]
    ).strip()

    if configured_company_id != company_id:
        raise ValueError(
            f"Folder/company ID mismatch. "
            f"Command used '{company_id}', but "
            f"config.json contains '{configured_company_id}'."
        )

    print("   config.json valid")
    print(
        "   aliases: "
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
            f"   {document['filename']} "
            f"({document['document_type']})"
        )

    print()
    print("3. Rebuilding local FAISS index...")
    build_local_index()

    print()
    print("=" * 48)
    print(
        f"Ingestion completed successfully "
        f"for '{company_id}'."
    )
    print()


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Validate one company application and "
            "rebuild the local FAISS/BM25 retrieval index."
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