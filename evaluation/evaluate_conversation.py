from rag import ask_rag


CONVERSATION_TESTS = [
    {
        "name": "Etteplan Azure follow-up",
        "company_id": "etteplan",
        "history": [
            {
                "role": "user",
                "content": "What Azure experience does Miika have?"
            },
            {
                "role": "assistant",
                "content": (
                    "Miika has worked with Azure OpenAI, "
                    "Microsoft Foundry and Azure AI Search "
                    "in his AI engineering projects."
                )
            },
        ],
        "question": "How relevant is that for this position?",
        "expected_company_ids": ["etteplan", "global"],
        "expected_document_types": [
            "applicant_match",
            "position",
            "applicant_skills",
            "applicant_projects",
            "applicant_cv",
        ],
    },
    {
        "name": "Etteplan API follow-up",
        "company_id": "etteplan",
        "history": [
            {
                "role": "user",
                "content": "What professional API experience does Miika have?"
            },
            {
                "role": "assistant",
                "content": (
                    "Miika has professional experience developing, "
                    "testing and troubleshooting REST API integrations."
                )
            },
        ],
        "question": "How would that help in this role?",
        "expected_company_ids": ["etteplan", "global"],
        "expected_document_types": [
            "applicant_match",
            "position",
            "applicant_cv",
            "applicant_skills",
        ],
    },
    {
        "name": "Gofore RAG project follow-up",
        "company_id": "gofore",
        "history": [
            {
                "role": "user",
                "content": "What AI projects has Miika built?"
            },
            {
                "role": "assistant",
                "content": (
                    "Miika has built a Microsoft 365 RAG Assistant "
                    "and a Work Application Assistant."
                )
            },
        ],
        "question": "Why are those relevant to this position?",
        "expected_company_ids": ["gofore", "global"],
        "expected_document_types": [
            "applicant_match",
            "position",
            "applicant_projects",
            "applicant_skills",
        ],
    },
]


def run_conversation_evaluation():
    total = len(CONVERSATION_TESTS)
    passed = 0

    print("\nWORK APPLICATION ASSISTANT")
    print("Conversation-Aware RAG Evaluation")
    print("=" * 70)

    for number, test in enumerate(CONVERSATION_TESTS, start=1):
        print(f"\nTest {number}: {test['name']}")
        print(f"Current question: {test['question']}")

        result = ask_rag(
            test["question"],
            company_id=test["company_id"],
            history=test["history"],
        )

        retrieved_chunks = result.get("retrieved_chunks", [])

        if not retrieved_chunks:
            print("FAIL - No chunks retrieved")
            continue

        company_pass = all(
            chunk["company_id"] in test["expected_company_ids"]
            for chunk in retrieved_chunks
        )

        type_pass = any(
            chunk["document_type"] in test["expected_document_types"]
            for chunk in retrieved_chunks
        )

        test_pass = company_pass and type_pass

        if test_pass:
            passed += 1

        for index, chunk in enumerate(retrieved_chunks, start=1):
            print(
                f"  #{index} "
                f"{chunk.get('@search.score', 0):.4f} | "
                f"{chunk['company_id']} | "
                f"{chunk['document_type']} | "
                f"{chunk['title']}"
            )

        print(
            f"Company isolation: "
            f"{'PASS' if company_pass else 'FAIL'}"
        )

        print(
            f"Relevant document type: "
            f"{'PASS' if type_pass else 'FAIL'}"
        )

        print(
            f"Conversation test: "
            f"{'PASS' if test_pass else 'FAIL'}"
        )

    accuracy = passed / total * 100 if total else 0

    print("\n" + "=" * 70)
    print("FINAL METRICS")
    print("=" * 70)

    print(
        f"Conversation-aware retrieval: "
        f"{passed}/{total} ({accuracy:.1f}%)"
    )


if __name__ == "__main__":
    run_conversation_evaluation()