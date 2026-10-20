
from pathlib import Path
from pypdf import PdfReader


def load_document(file_path):
    file_path = Path(file_path)

    if file_path.suffix.lower() == ".pdf":
        return load_pdf_document(file_path)

    if file_path.suffix.lower() == ".txt":
        return load_text_document(file_path)

    raise ValueError(f"Unsupported file type: {file_path.suffix}")


def load_pdf_document(file_path):
    reader = PdfReader(str(file_path))

    pages = []

    for page in reader.pages:
        text = page.extract_text()
        if text:
            pages.append(text)

    content = "\n\n".join(pages).strip()

    if not content:
        raise ValueError(
            f"No extractable text found in PDF: {file_path}"
        )

    # Identify the language from the filename.
    filename = file_path.stem.lower()

    if filename.endswith("_fi"):
        language = "fi"
    elif filename.endswith("_en"):
        language = "en"
    else:
        language = "unknown"

    return {
        "title": file_path.stem,
        "company_id": "global",
        "document_type": "applicant_cv",
        "source": file_path.name,
        "source_url": None,
        "language": language,
        "content": content,
    }


def load_text_document(file_path):
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
        "language": metadata.get("language", "unknown"),
        "content": content.strip(),
    }


def load_all_documents(data_folder="data/private"):
    documents = []

    data_folder = Path(data_folder)

    for file_path in sorted(data_folder.rglob("*")):
        if not file_path.is_file():
            continue

        if file_path.suffix.lower() not in (".txt", ".pdf"):
            continue

        # Ignore empty placeholder files.
        if file_path.stat().st_size == 0:
            continue

        document = load_document(file_path)
        document["filename"] = file_path.name

        documents.append(document)

    return documents
