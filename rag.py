from search.vector_search import hybrid_search
from azure_client import ask_ai


MIN_RELEVANCE_SCORE = 0.02


def detect_document_types(question, company_id=None):
    question_lower = question.lower()

    # Applicant + position comparison
    match_keywords = [
        # English
        "fit",
        "match",
        "suitable",
        "suitability",
        "qualified",
        "qualification",
        "good candidate",
        "why miika",
        "hire miika",
        # Finnish
        "sopii",
        "sopivuus",
        "soveltuu",
        "soveltuvuus",
        "sopiva",
        "pätevä",
        "pätevyys",
        "hyvä hakija",
        "hyvä kandidaatti",
        "miksi miika",
        "palkata miika",
        "vastaa tehtävää",
        "vastaa vaatimuksia",
    ]

    # Applicant projects
    project_keywords = [
        # English
        "project",
        "projects",
        "portfolio",
        "rag",
        "assistant",
        "github",
        # Finnish
        "projekti",
        "projektit",
        "portfolio",
        "avustaja",
    ]

    # Applicant certifications
    certification_keywords = [
        # English
        "certification",
        "certifications",
        "certificate",
        "certificates",
        "credential",
        "credentials",
        # Finnish
        "sertifikaatti",
        "sertifikaatit",
        "todistus",
        "todistukset",
        "pätevyystodistus",
    ]

    # Applicant skills / technologies
    skill_keywords = [
        # English
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
        "automation",
        # Finnish
        "taito",
        "taidot",
        "osaaminen",
        "teknologia",
        "teknologiat",
        "tekninen",
        "rajapinta",
        "rajapinnat",
        "tekoäly",
        "automaatio",
    ]

    # Applicant CV / professional background
    applicant_keywords = [
        # English
        "miika",
        "experience",
        "background",
        "education",
        "work experience",
        "professional experience",
        "previous role",
        "previous job",
        # Finnish
        "kokemus",
        "tausta",
        "koulutus",
        "työkokemus",
        "ammatillinen kokemus",
        "aiempi rooli",
        "aiempi työ",
        "edellinen työ",
    ]

    # Position
    position_keywords = [
        # English
        "position",
        "role",
        "job",
        "responsibilities",
        "requirements",
        "job description",
        # Finnish
        "tehtävä",
        "rooli",
        "työpaikka",
        "vastuut",
        "vaatimukset",
        "työtehtävä",
        "tehtävänkuva",
    ]

    # Company
    company_keywords = [
        # English
        "company",
        "organization",
        "business",
        "employer",
        "about the company",
        # Finnish
        "yritys",
        "organisaatio",
        "liiketoiminta",
        "työnantaja",
        "kerro yrityksestä",
    ]

    # Check more specific intents first
    if any(keyword in question_lower for keyword in match_keywords):
        return [
            "applicant_match",
            "position",
            "applicant_cv",
            "applicant_skills",
            "applicant_projects",
            "applicant_certifications",
        ]

    if any(keyword in question_lower for keyword in project_keywords):
        return ["applicant_projects"]

    if any(keyword in question_lower for keyword in certification_keywords):
        return ["applicant_certifications"]

    if any(keyword in question_lower for keyword in skill_keywords):
        return [
            "applicant_skills",
            "applicant_cv",
            "applicant_projects",
        ]

    if any(keyword in question_lower for keyword in applicant_keywords):
        return [
            "applicant_cv",
            "applicant_skills",
            "applicant_projects",
            "applicant_certifications",
            "applicant_match",
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


def ask_rag(question, company_id, history=None, language="en"):
    if history is None:
        history = []

    language = normalize_language(language)

    # Route using the user's original intent.
    document_types = detect_document_types(
        question,
        company_id=company_id,
    )

    # Rewrite follow-up questions into a standalone retrieval query.
    retrieval_query = rewrite_query(
        question,
        history=history,
        language=language,
    )

    results = hybrid_search(
        retrieval_query,
        company_id=company_id,
        top_k=4,
        document_types=document_types,
    )

    # Remove results that are probably unrelated.
    relevant_results = [
        result
        for result in results
        if result["@search.score"] >= MIN_RELEVANCE_SCORE
    ]

    # Nothing relevant was found.
    if not relevant_results:
        if language == "fi":
            no_results_answer = (
                "En löytänyt hakemuksen tietopohjasta riittävästi "
                "olennaista tietoa vastatakseni tähän kysymykseen."
            )
        else:
            no_results_answer = (
                "I couldn't find enough relevant information "
                "in the application knowledge base to answer that question."
            )

        return {
            "answer": no_results_answer,
            "sources": [],
            "citations": [],
            "retrieved_chunks": [],
            "retrieval_query": retrieval_query,
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
            "content": result["content"],
        })

    context = "\n\n---\n\n".join(context_parts)

    answer_language_instruction = (
        "Answer in Finnish. Use natural, professional Finnish."
        if language == "fi"
        else "Answer in English. Use natural, professional English."
    )

    messages = [
        {
            "role": "system",
            "content": (
                "You are an AI assistant for a job application. "
                "Your purpose is to help recruiters learn about the applicant, "
                "the position, the company, and how the applicant's experience "
                "relates to the position. "

                f"{answer_language_instruction} "

               "Present the applicant in a constructive, recruiter-facing way. "
"For general questions about suitability, fit, qualifications, or why the "
"applicant could be a good candidate, focus on demonstrated strengths, "
"relevant experience, transferable skills, projects, and alignment with "
"the position. "

"Do NOT proactively mention missing qualifications, experience gaps, "
"seniority gaps, weaknesses, shortcomings, or reasons not to hire the "
"applicant in a general suitability answer. The absence of evidence for "
"a qualification is not itself a reason to mention that qualification. "

"Only discuss weaknesses, missing requirements, limitations, or gaps when "
"the user explicitly asks about them, for example by asking what the "
"applicant lacks, what requirements are not met, what concerns there are, "
"or what areas still need development. "

"If the user explicitly asks about shortcomings or missing requirements, "
"answer truthfully using only the retrieved evidence and use neutral, "
"constructive wording. Never invent experience or imply that the applicant "
"has a qualification that is not supported by the context. "

"When answering a general fit question, conclude by summarizing the strongest "
"reasons the applicant is relevant to the position. Do not end the answer "
"with a caveat about missing experience or a hypothetical reason not to "
"hire the applicant."

            ),
        },
        {
            "role": "user",
            "content": f"""
CONTEXT:

{context}

QUESTION:

{question}
""".strip(),
        },
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
                "url": result.get("source_url"),
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
            "content": result["content"],
        })

    return {
        "answer": answer,
        "sources": sources,
        "citations": citations,
        "retrieved_chunks": retrieved_chunks,
        "retrieval_query": retrieval_query,
    }


def rewrite_query(question, history=None, language="en"):
    if not history:
        return question

    language = normalize_language(language)
    recent_history = history[-4:]

    history_text = "\n".join(
        f"{message['role']}: {message['content']}"
        for message in recent_history
    )

    output_language_instruction = (
        "Return the rewritten search query in Finnish."
        if language == "fi"
        else "Return the rewritten search query in English."
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
                f"{output_language_instruction} "
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


def normalize_language(language):
    normalized = str(language or "en").strip().lower()

    if normalized in {"fi", "fin", "finnish", "suomi"}:
        return "fi"

    return "en"
