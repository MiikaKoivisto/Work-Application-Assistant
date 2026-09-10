from pathlib import Path


def load_document(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        text = file.read()

    metadata_text, content = text.split("---", 1)

    metadata = {}

    for line in metadata_text.strip().splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            metadata[key.strip().lower()] = value.strip()

    return {
        "title": metadata.get("title"),
        "product": metadata.get("product"),
        "category": metadata.get("category"),
        "source": metadata.get("source"),
        "source_url": metadata.get("source_url"),
        "content": content.strip()
    }


def load_all_documents(data_folder="data"):
    documents = []

    for file_path in Path(data_folder).rglob("*.txt"):
        document = load_document(file_path)

        document["filename"] = file_path.name

        documents.append(document)

    return documents