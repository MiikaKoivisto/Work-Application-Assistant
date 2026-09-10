# Microsoft 365 RAG Assistant

A Retrieval-Augmented Generation (RAG) application for answering Microsoft 365 support questions using Azure OpenAI, Azure AI Search, vector embeddings, hybrid retrieval, and Streamlit.

The project demonstrates an end-to-end RAG pipeline built in Python without relying on a high-level RAG framework.

## Features

- Microsoft 365 support question answering
- Azure OpenAI / Microsoft Foundry integration
- Azure AI Search vector database
- Hybrid keyword + vector retrieval
- OpenAI text embeddings
- Document ingestion and chunking pipeline
- Metadata-aware document indexing
- Relevance filtering for out-of-domain questions
- Grounded LLM responses
- Source citations
- Retrieval debug interface
- Automated retrieval evaluation
- Streamlit chat interface

## Architecture

```text
Microsoft 365 Support Documentation
                |
                v
        Document Loader
                |
                v
        Paragraph Chunking
                |
                v
       Embedding Generation
     text-embedding-3-small
                |
                v
        Azure AI Search
       Vector Search Index
                |
                v
          User Question
                |
                v
        Query Embedding
                |
                v
          Hybrid Search
      Keyword + Vector Search
                |
                v
        Relevance Filtering
                |
                v
        Retrieved Context
                |
                v
     Azure OpenAI / Foundry
                |
                v
        Grounded Answer
                |
                v
       Answer + Sources
                |
                v
          Streamlit UI

          