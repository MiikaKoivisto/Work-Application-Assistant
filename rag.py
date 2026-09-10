from search.vector_search import hybrid_search
from azure_client import ask_ai


MIN_RELEVANCE_SCORE = 0.02


def detect_document_types(question, company_id=None):
    question_lower = question.lower()

    # Applicant + position comparison
    match_keywords = [
        "fit",
        "match",
        "suitable",
        "suitability",
        "qualified",
        "qualification",
        "good candidate",
        "why miika",
        "hire miika"
    ]

    # Applicant projects
    project_keywords = [
        "project",
        "projects",
        "portfolio",
        "rag",
        "assistant",
        "github"
    ]

    # Applicant certifications
    certification_keywords = [
        "certification",
        "certifications",
        "certificate",
        "certificates",
        "credential",
        "credentials"
    ]

    # Applicant skills / technologies
    skill_keywords = [
        "skill",
        "skills",
        "technology",
        "technologies",
        "technical",
        "python",
        "javascript",
        "api",
        "apis",
        "power automate",
        "power apps",
        "azure",
        "ai",
        "automation"
    ]

    # Applicant CV / professional background
    applicant_keywords = [
        "miika",
        "experience",
        "background",
        "education",
        "work experience",
        "professional experience",
        "previous role",
        "previous job"
    ]

    # Position
    position_keywords = [
        "position",
        "role",
        "job",
        "responsibilities",
        "requirements",
        "job description"
    ]

    # Company
    company_keywords = [
        "company",
        "organization",
        "business",
        "employer",
        "about the company",
    ]

    # Check more specific intents first
    if any(keyword in question_lower for keyword in match_keywords):
        return [
            "applicant_match",
            "position",
            "applicant_cv",
            "applicant_skills",
            "applicant_projects",
            "applicant_certifications"
        ]

    if any(keyword in question_lower for keyword in project_keywords):
        return ["applicant_projects"]

    if any(keyword in question_lower for keyword in certification_keywords):
        return ["applicant_certifications"]

    if any(keyword in question_lower for keyword in skill_keywords):
        return [
            "applicant_skills",
            "applicant_cv",
            "applicant_projects"
        ]

    if any(keyword in question_lower for keyword in applicant_keywords):
        return [
            "applicant_cv",
            "applicant_skills",
            "applicant_projects",
            "applicant_certifications",
            "applicant_match"
        ]

    if any(keyword in question_lower for keyword in position_keywords):
        return ["position"]

    # Active company name can be treated as company intent,
    # but only after more specific applicant/position intents.
    if company_id:
        company_name = company_id.lower().replace("_", " ")

        if company_name in question_lower:
            return ["company"]

    if any(keyword in question_lower for keyword in company_keywords):
        return ["company"]

    # Unknown intent: search all documents available to this recruiter
    return None


def ask_rag(question, company_id, history=None):
    if history is None:
        history = []

    # Route using the user's original intent.
    document_types = detect_document_types(
        question,
        company_id=company_id
    )

    # Rewrite follow-up questions into a standalone retrieval query.
    retrieval_query = rewrite_query(
        question,
        history=history
    )

    results = hybrid_search(
        retrieval_query,
        company_id=company_id,
        top_k=4,
        document_types=document_types
    )

    # Remove results that are probably unrelated.
    relevant_results = [
        result
        for result in results
        if result["@search.score"] >= MIN_RELEVANCE_SCORE
    ]

    # Nothing relevant was found.
    if not relevant_results:
        return {
            "answer": (
                "I couldn't find enough relevant information "
                "in the application knowledge base to answer that question."
            ),
            "sources": [],
            "citations": [],
            "retrieved_chunks": [],
            "retrieval_query": retrieval_query
        }

    # Build numbered evidence blocks.
    # The numbering is also returned to the UI so [1], [2], etc.
    # can be mapped back to the exact retrieved chunks.
    context_parts = []
    citations = []

    for citation_number, result in enumerate(relevant_results, start=1):
        context_parts.append(
            f"""
[EVIDENCE {citation_number}]
Title: {result['title']}
Company ID: {result['company_id']}
Document type: {result['document_type']}
Source: {result['source']}
Source URL: {result.get('source_url') or 'Not available'}
Chunk ID: {result['chunk_id']}

{result['content']}
""".strip()
        )

        citations.append({
            "citation_number": citation_number,
            "chunk_id": result["chunk_id"],
            "title": result["title"],
            "company_id": result["company_id"],
            "document_type": result["document_type"],
            "source": result["source"],
            "url": result.get("source_url"),
            "content": result["content"]
        })

    context = "\n\n---\n\n".join(context_parts)

    messages = [
        {
            "role": "system",
            "content": (
                "You are an AI assistant for a job application. "
                "Your purpose is to help recruiters learn about the applicant, "
                "the position, the company, and how the applicant's experience "
                "relates to the position. "

                "Answer using only the information provided in the retrieved "
                "context. Do not invent qualifications, professional experience, "
                "skills, certifications, responsibilities, or achievements. "

                "Clearly distinguish between professional experience, personal "
                "projects, independent learning, and areas the applicant is "
                "currently developing. "

                "Every factual claim that comes from the retrieved context must "
                "include an inline citation using the evidence number, for example "
                "[1] or [2]. Use only citation numbers that appear in the provided "
                "context. Place citations immediately after the claim they support. "
                "If one claim is supported by multiple evidence blocks, cite each "
                "relevant block, for example [1][3]. "
                "Do not create a separate references list in the answer. "

                "If the context does not contain enough information to answer "
                "the question, say so clearly. "

                "Be professional, concise, and factual. "
                "Do not exaggerate the applicant's suitability for the position."
            )
        },
        {
            "role": "user",
            "content": f"""
CONTEXT:

{context}

QUESTION:

{question}
""".strip()
        }
    ]

    answer = ask_ai(messages)

    # Create unique source list for the existing Sources expander.
    sources = []
    seen_sources = set()

    for result in relevant_results:
        source_key = (
            result.get("source_url")
            or result["title"]
        )

        if source_key not in seen_sources:
            sources.append({
                "title": result["title"],
                "company_id": result["company_id"],
                "document_type": result["document_type"],
                "source": result["source"],
                "url": result.get("source_url")
            })

            seen_sources.add(source_key)

    # Debug information.
    retrieved_chunks = []

    for citation_number, result in enumerate(relevant_results, start=1):
        retrieved_chunks.append({
            "citation_number": citation_number,
            "chunk_id": result["chunk_id"],
            "score": result["@search.score"],
            "title": result["title"],
            "company_id": result["company_id"],
            "document_type": result["document_type"],
            "content": result["content"]
        })

    return {
        "answer": answer,
        "sources": sources,
        "citations": citations,
        "retrieved_chunks": retrieved_chunks,
        "retrieval_query": retrieval_query
    }


def rewrite_query(question, history=None):
    if not history:
        return question

    recent_history = history[-4:]

    history_text = "\n".join(
        f"{message['role']}: {message['content']}"
        for message in recent_history
    )

    messages = [
        {
            "role": "system",
            "content": (
                "Rewrite the user's current question into a standalone "
                "search query for a RAG retrieval system.\n\n"
                "Use the conversation history only to resolve references "
                "such as 'that', 'those', 'it', 'this role', or similar "
                "follow-up language.\n\n"
                "Preserve the user's original intent. "
                "Do not answer the question. "
                "Do not invent information. "
                "Return only the rewritten search query."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Conversation history:\n{history_text}\n\n"
                f"Current question:\n{question}"
            ),
        },
    ]

    return ask_ai(messages).strip()
