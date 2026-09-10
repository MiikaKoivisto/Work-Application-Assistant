# AI Work Application Assistant

A recruiter-facing Retrieval-Augmented Generation (RAG) application built with Azure OpenAI, Azure AI Search, Python, and Streamlit.

The application provides an interactive way for recruiters to explore an applicant's professional experience, technical skills, projects, and suitability for a specific open position.

Each company receives its own isolated application context while shared applicant information is retrieved from a global knowledge base.

---

## Overview

The AI Work Application Assistant was created as a portfolio project to demonstrate practical AI engineering concepts in a real-world use case.

When a recruiter opens the application, they enter their name and company. The application identifies the relevant job application and dynamically restricts retrieval to:

- The selected company's information
- The specific open position
- Applicant-to-position matching information
- Global applicant experience, skills, certifications, and projects

The assistant then uses Retrieval-Augmented Generation to answer questions using only the retrieved application data.

Example questions:

- What does the company do?
- What are the main requirements for the position?
- How does Miika fit the position?
- What relevant AI projects has Miika built?
- What experience does Miika have with APIs and integrations?
- What are the main gaps between Miika's experience and the position?

---

## Architecture

```text
Recruiter
    │
    ▼
Streamlit UI
    │
    ├── Recruiter name
    └── Company name
            │
            ▼
      Company Matcher
            │
      Alias normalization
            │
            ▼
      Stable company_id
            │
            ▼
Conversation-aware Query Rewriting
            │
            ▼
       Hybrid Retrieval
      Azure AI Search
       ┌────┴─────┐
       │          │
   Keyword      Vector
    Search       Search
       │          │
       └────┬─────┘
            │
            ▼
      Metadata Filtering
            │
    company_id = selected company
              OR
    company_id = global
            │
            ▼
      Retrieved Evidence
            │
            ▼
        Azure OpenAI
            │
      Grounded Generation
            │
            ▼
 Answer + Inline Citations
            │
            ▼
        Streamlit UI
```

---

## Key Features

### Retrieval-Augmented Generation

The assistant retrieves relevant information from Azure AI Search before generating an answer.

The language model is instructed to answer from the retrieved evidence instead of relying on unsupported model knowledge.

### Hybrid Search

Retrieval combines:

- Vector similarity search
- Keyword search
- Azure AI Search filtering

Embeddings are generated using an Azure OpenAI embedding model.

### Company-Aware Retrieval

Each job application is assigned a stable `company_id`.

For example:

```text
company-x
company-y
company-z
```

Recruiter input is normalized and matched against configurable company aliases.

```json
{
  "company_id": "company-x",
  "aliases": [
    "Company X",
    "Company X Oyj",
    "Company X Plc"
  ]
}
```

This allows different versions of a company name to resolve to the same application context.

### Metadata Isolation

Company-specific retrieval is restricted using Azure AI Search metadata filters.

Conceptually:

```text
company_id = active_company
OR
company_id = global
```

This means the assistant can retrieve global applicant information while preventing another company's application data from entering the retrieval context.

### Conversation-Aware Retrieval

Follow-up questions such as:

```text
What technologies does the position require?

Which of those does Miika already know?
```

require conversation context.

The application rewrites follow-up questions into standalone retrieval queries before searching the knowledge base.

This improves retrieval without sending the entire conversation directly into the search query.

### Evidence and Citations

Retrieved chunks are converted into numbered evidence blocks.

Generated answers can reference those blocks using inline citations:

```text
Miika has experience developing and testing REST APIs [1]
and has built RAG applications using Azure AI technologies [2].
```

The Streamlit interface allows the recruiter to inspect:

- Evidence
- Sources
- Original question
- Rewritten retrieval query
- Retrieved chunks
- Retrieval scores
- Document types
- Company IDs
- Chunk IDs

This makes the RAG pipeline more transparent and easier to debug.

---

## Automated Application Ingestion

A major goal of the project is making new job applications easy to add without modifying application code.

A new application can be initialized with:

```bash
python -m ingestion.new_application company-x --name "Company X"
```

This creates:

```text
data/private/companies/company-x/
├── config.json
├── company_info.txt
├── position_info.txt
└── applicant_match.txt
```

After the documents are completed, the application can be indexed with:

```bash
python -m ingestion.add_application company-x
```

The ingestion pipeline automatically performs:

```text
Configuration validation
        ↓
Document validation
        ↓
Text chunking
        ↓
Embedding generation
        ↓
Existing company data removal
        ↓
Azure AI Search upload
        ↓
Index verification
```

The verification stage includes retry logic to account for indexing delay in Azure AI Search.

---

## Knowledge Base Structure

Private application information is organized as:

```text
data/private/

├── applicant/
│   ├── cv.txt
│   ├── skills.txt
│   ├── certifications.txt
│   └── projects.txt
│
└── companies/
    └── company-x/
        ├── config.json
        ├── company_info.txt
        ├── position_info.txt
        └── applicant_match.txt
```

Applicant documents use:

```text
COMPANY_ID: global
```

while application-specific documents use their corresponding company ID.

Documents also contain metadata such as:

```text
TITLE
COMPANY_ID
DOCUMENT_TYPE
SOURCE
SOURCE_URL
```

This metadata is preserved during chunking and stored in Azure AI Search.

---

## Document Types

The knowledge base separates information by purpose.

| Document Type | Purpose |
|---|---|
| `company` | Information about the company |
| `position` | Job description and requirements |
| `applicant_match` | Applicant-to-position analysis |
| `applicant_cv` | Professional experience |
| `applicant_skills` | Technical skills |
| `applicant_projects` | AI and software projects |
| `applicant_certifications` | Verified certifications |

Document types can also be used to narrow retrieval depending on the user's question.

---

## RAG Pipeline

For each recruiter question, the application performs the following process:

1. Determine the active company.
2. Analyze the intent of the question.
3. Rewrite conversation-dependent questions when necessary.
4. Generate an embedding for the retrieval query.
5. Perform hybrid search in Azure AI Search.
6. Apply company and document metadata filters.
7. Retrieve the most relevant chunks.
8. Convert retrieved chunks into numbered evidence.
9. Send the evidence and question to Azure OpenAI.
10. Generate a grounded answer with citations.
11. Display the answer, sources, evidence, and technical retrieval details.

---

## Evaluation

The project includes automated retrieval evaluation.

The evaluation suite tests areas including:

- Company information retrieval
- Position retrieval
- Applicant-position matching
- Technical skill retrieval
- AI project retrieval
- Professional experience retrieval
- Global applicant data retrieval
- Company isolation
- Cross-company leakage
- Conversation-aware retrieval

Cross-company tests deliberately query information associated with another application while a different company is active.

This helps verify that metadata filtering prevents unrelated company data from entering the retrieved context.

Run the retrieval evaluation with:

```bash
python -m evaluation.evaluate_retrieval
```

Conversation-aware retrieval can be evaluated with:

```bash
python -m evaluation.evaluate_conversation
```

---

## Technology Stack

### AI

- Azure OpenAI
- Large Language Models
- Text embeddings
- Retrieval-Augmented Generation
- Prompt engineering
- Conversation-aware query rewriting

### Search

- Azure AI Search
- Vector search
- Keyword search
- Hybrid retrieval
- HNSW vector indexing
- Metadata filtering

### Application

- Python
- Streamlit

### Development

- Git
- GitHub
- Python virtual environments
- Environment-based configuration
- Automated ingestion
- Retrieval evaluation

---

## Project Structure

```text
Work-Application-Assistant/
│
├── app.py
├── azure_client.py
├── company_matcher.py
├── rag.py
│
├── ingestion/
│   ├── add_application.py
│   ├── new_application.py
│   ├── chunking.py
│   └── document_loader.py
│
├── search/
│   ├── create_index.py
│   ├── upload_documents.py
│   └── vector_search.py
│
├── evaluation/
│   ├── evaluate_retrieval.py
│   └── evaluate_conversation.py
│
├── data/
│   └── private/
│
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

The exact structure may evolve as the project develops.

---

## Environment Configuration

Create a `.env` file based on `.env.example`.

Example:

```env
AZURE_OPENAI_ENDPOINT=
AZURE_OPENAI_API_KEY=

MODEL_DEPLOYMENT=
EMBEDDING_DEPLOYMENT=

AZURE_SEARCH_ENDPOINT=
AZURE_SEARCH_INDEX=
AZURE_SEARCH_API_KEY=
```

Never commit real credentials to Git.

---

## Installation

Clone the repository:

```bash
git clone https://github.com/MiikaKoivisto/Work-Application-Assistant.git
cd Work-Application-Assistant
```

Create and activate a virtual environment:

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Configure the required Azure environment variables and run:

```bash
streamlit run app.py
```

---

## Privacy

Real job-application data is intentionally excluded from the public repository.

The following directory is ignored by Git:

```text
data/private/
```

This prevents company-specific application material and private applicant data from being published to GitHub.

Public code demonstrates the architecture and implementation without requiring real application data to be exposed.

Secrets are also excluded:

```text
.env
.streamlit/secrets.toml
```

---

## Design Goals

This project was designed to demonstrate practical AI engineering rather than only provide a conversational UI.

The implementation focuses on:

- Grounded LLM responses
- Retrieval quality
- Data isolation
- Transparent evidence
- Automated ingestion
- Conversation-aware retrieval
- Evaluation
- Maintainable project structure
- Secure handling of private application data

---

## Future Development

Potential improvements include:

- Semantic reranking
- More advanced intent classification
- Automated citation evaluation
- Improved retrieval metrics
- Additional application datasets
- Automated document extraction
- PDF ingestion
- Deployment improvements
- Expanded RAG evaluation
- Agentic retrieval experiments

---

## Author

**Miika Koivisto**

Business Information Technology graduate focused on AI engineering, automation, integrations, APIs, cloud technologies, and practical business-oriented software development.
