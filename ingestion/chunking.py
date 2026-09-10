def chunk_text(text, chunk_size=800):
    """
    Split text using paragraph boundaries.

    Paragraphs are kept intact whenever possible so that
    chunks do not begin or end in the middle of words.
    """

    paragraphs = [
        paragraph.strip()
        for paragraph in text.split("\n\n")
        if paragraph.strip()
    ]

    chunks = []
    current_chunk = ""

    for paragraph in paragraphs:

        # If the paragraph fits in the current chunk,
        # add it there.
        if len(current_chunk) + len(paragraph) + 2 <= chunk_size:

            if current_chunk:
                current_chunk += "\n\n"

            current_chunk += paragraph

        else:
            # Save the current chunk before starting another.
            if current_chunk:
                chunks.append(current_chunk)

            current_chunk = paragraph

    # Don't forget the final chunk.
    if current_chunk:
        chunks.append(current_chunk)

    return chunks


def chunk_document(document, chunk_size=800):
    text_chunks = chunk_text(
        document["content"],
        chunk_size=chunk_size
    )

    chunks = []

    for index, text in enumerate(text_chunks, start=1):
        chunks.append({
            "chunk_id": (
                f"{document['product'].lower()}-"
                f"{document['category'].lower().replace(' ', '-')}-"
                f"{index}"
            ),
            "chunk_number": index,
            "title": document["title"],
            "product": document["product"],
            "category": document["category"],
            "source": document["source"],
            "source_url": document["source_url"],
            "filename": document["filename"],
            "content": text
        })

    return chunks


def chunk_all_documents(documents, chunk_size=800):
    all_chunks = []

    for document in documents:
        all_chunks.extend(
            chunk_document(
                document,
                chunk_size=chunk_size
            )
        )

    return all_chunks