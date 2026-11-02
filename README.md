# AI Work Application Assistant

A recruiter-facing **Retrieval-Augmented Generation (RAG)** portfolio project built with **Python, Azure OpenAI, FAISS, BM25, and Streamlit**.

The assistant helps recruiters explore a candidate's professional experience, technical skills, projects, certifications, and suitability for a role. It retrieves relevant information from a document knowledge base and uses an LLM to produce evidence-grounded answers.

> **Project evolution:** The original version used Azure AI Search and company-specific datasets. The newer design focuses on a shared applicant knowledge base, local hybrid retrieval, and job descriptions supplied at runtime rather than requiring a company name at login.

## Overview

A recruiter enters their **first name and access code** to open the assistant. They can ask questions about the candidate and, in the job-context workflow, provide a job advertisement URL or paste the description to make questions more role-specific.

Example questions:

- What experience does Miika have with Python, APIs, and automation?
- Which of Miika's projects are relevant to this role?
- How does Miika's experience relate to the job description?
- What AI technologies has Miika worked with?
- What certifications and training has Miika completed?

The application supports **English and Finnish**.

## Architecture

```text
Recruiter
   |
   v
Streamlit interface
   |-- First name + access code
   |-- Questions and conversation history
   `-- Job advertisement URL or pasted description*
   |
   v
Question intent detection / follow-up query rewriting
   |
   v
Hybrid retrieval over applicant documents
   |-- FAISS semantic vector search
   `-- BM25 keyword search
   |
   v
Relevant document chunks and metadata
   |
   v
Azure OpenAI
   |
   v
Evidence-grounded response
   |
   v
Streamlit: answer, sources, citations, retrieval details
```

*The job-advertisement workflow depends on the version of `app.py` and `rag.py` deployed together. See **Implementation notes** below.*

## Key features

### Retrieval-Augmented Generation

The assistant searches indexed applicant documents before generating an answer. Retrieved passages provide the context for Azure OpenAI responses, reducing reliance on unsupported general model knowledge.

### Hybrid search

The local retrieval pipeline combines **FAISS vector similarity** and **BM25 keyword matching** to support both semantic and exact-term queries. Applicant documents are split into searchable chunks, with metadata retained for source inspection.

### Conversation-aware questions

Follow-up questions can be rewritten into standalone retrieval queries using recent conversation history. This helps resolve references such as “Which of those technologies has Miika used?”

### Job-specific context

The intended workflow accepts a job advertisement URL or pasted job description, allowing recruiters to ask how the candidate's experience relates to a particular role without selecting a predefined company. This is distinct from the earlier company-matching architecture.

### Evidence and retrieval transparency

The interface can expose:

- Source documents and retrieved passages
- Numbered citations and document metadata
- Original and rewritten queries
- Retrieval scores and chunk identifiers

These details help inspect and debug the RAG pipeline.

### Bilingual recruiter interface

The assistant provides English and Finnish UI text and can request answers in the selected language.

### Access-code login

Recruiters enter a first name and an access code. The access code is configured using environment variables or Streamlit secrets; it is not embedded in the source code.

## Engineering challenges and lessons learned

**Retrieval relevance.** Matching a recruiter's question to the most useful evidence is not always straightforward. The project explores combining semantic search with keyword retrieval, intent-based document selection, and relevance thresholds.

**Component integration.** Building a complete application required connecting document ingestion, embeddings, search, LLM calls, conversation state, and the Streamlit interface. Keeping interfaces consistent across modules was an important part of debugging.

**Evaluating AI-generated code.** AI-assisted development can speed up implementation, but generated code still needs review, testing, and correction. A practical lesson from this project was to verify function signatures, imports, and retrieval behavior rather than assuming generated changes are compatible.

**Grounded responses.** Prompt design and evidence presentation were refined to help the assistant provide useful, recruiter-facing answers without inventing unsupported qualifications.

## Technology stack

| Area | Technologies |
| --- | --- |
| Language | Python |
| LLM and embeddings | Azure OpenAI |
| Retrieval | RAG, FAISS, BM25, hybrid search |
| Interface | Streamlit |
| Document processing | Text extraction, chunking, metadata |
| Development | Git, GitHub, virtual environments |

## Project structure

Key files and directories in the newer project:

```text
Work-Application-Assistant/
├── app.py                    # Streamlit interface and session state
├── rag.py                    # RAG orchestration and response generation
├── azure_client.py           # Azure OpenAI client
├── job_fetcher.py            # Job advertisement extraction
├── search/
│   ├── vector_search.py      # Hybrid retrieval
│   └── build_local_index.py  # Local index construction
├── ingestion/
│   └── document_loader.py    # Document loading
├── local_index/              # FAISS index and chunk metadata
├── data/                     # Applicant documents
├── evaluation/               # Evaluation scripts
├── requirements.txt
├── .env.example
└── README.md
```

Some older modules may remain in the repository as the project transitions from the original company-specific architecture.

## Author

**Miika Koivisto**  
Business Information Technology graduate interested in AI engineering, automation, APIs, cloud technologies, and practical software development.

[GitHub repository](https://github.com/MiikaKoivisto/Work-Application-Assistant)
