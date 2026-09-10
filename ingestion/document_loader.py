from pathlib import Path


def load_document(file_path):
    with open(file_path, "r", encoding="utf-8-sig") as file:
        text = file.read()

    if "---" not in text:
        raise ValueError(
            f"Document '{file_path}' is missing the '---' metadata separator."
        )

    metadata_text, content = text.split("---", 1)

    metadata = {}

    for line in metadata_text.strip().splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            metadata[key.strip().lower()] = value.strip()

    return {
        "title": metadata.get("title"),
        "company_id": metadata.get("company_id"),
        "document_type": metadata.get("document_type"),
        "source": metadata.get("source"),
        "source_url": metadata.get("source_url"),
        "content": content.strip(),
    }


def load_all_documents(data_folder="data/private"):
    documents = []

    for file_path in Path(data_folder).rglob("*.txt"):

        # Ignore empty placeholder files
        if file_path.stat().st_size == 0:
            continue

        document = load_document(file_path)

        document["filename"] = file_path.name

        documents.append(document)

    return documents