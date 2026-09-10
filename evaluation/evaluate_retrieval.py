from search.vector_search import hybrid_search


TEST_CASES = [

    {
        "name": "Etteplan company information",
        "question": "Tell me about Etteplan.",
        "company_id": "etteplan",
        "document_types": ["company"],
        "expected_top1_types": ["company"],
        "allowed_company_ids": ["etteplan"],
    },
    {
        "name": "Etteplan position information",
        "question": "Tell me about the AI Developer position.",
        "company_id": "etteplan",
        "document_types": ["position"],
        "expected_top1_types": ["position"],
        "allowed_company_ids": ["etteplan"],
    },
    {
        "name": "Etteplan applicant-position match",
        "question": "How does Miika fit the Etteplan AI Developer position?",
        "company_id": "etteplan",
        "document_types": [
            "applicant_match",
            "position",
            "applicant_cv",
            "applicant_skills",
            "applicant_projects",
            "applicant_certifications",
        ],
        "expected_top1_types": ["applicant_match"],
        "allowed_company_ids": ["etteplan", "global"],
    },

    {
        "name": "Company information",
        "question": "Tell me about the company.",
        "company_id": "gofore",
        "document_types": ["company"],
        "expected_top1_types": ["company"],
        "allowed_company_ids": ["gofore"],
    },
    {
        "name": "Position information",
        "question": "Tell me about the position.",
        "company_id": "gofore",
        "document_types": ["position"],
        "expected_top1_types": ["position"],
        "allowed_company_ids": ["gofore"],
    },
    {
        "name": "Applicant-position match",
        "question": "How does Miika fit the position?",
        "company_id": "gofore",
        "document_types": [
            "applicant_match",
            "position",
            "applicant_cv",
            "applicant_skills",
            "applicant_projects",
            "applicant_certifications",
        ],
        "expected_top1_types": ["applicant_match"],
        "allowed_company_ids": ["gofore", "global"],
    },
    {
        "name": "AI projects",
        "question": "What AI projects has Miika built?",
        "company_id": "gofore",
        "document_types": ["applicant_projects"],
        "expected_top1_types": ["applicant_projects"],
        "allowed_company_ids": ["global"],
    },
    {
        "name": "Technical skills",
        "question": "What technical skills does Miika have?",
        "company_id": "gofore",
        "document_types": [
            "applicant_skills",
            "applicant_cv",
            "applicant_projects",
        ],
        "expected_top1_types": [
            "applicant_skills",
            "applicant_cv",
        ],
        "allowed_company_ids": ["global"],
    },
    {
        "name": "Professional background",
        "question": "What is Miika's professional background?",
        "company_id": "gofore",
        "document_types": [
            "applicant_cv",
            "applicant_skills",
            "applicant_projects",
            "applicant_certifications",
            "applicant_match",
        ],
        "expected_top1_types": ["applicant_cv"],
        "allowed_company_ids": ["gofore", "global"],
    },
]

ISOLATION_TESTS = [
    {
        "name": "Gofore cannot retrieve Etteplan",
        "question": "Tell me about Etteplan and the AI Developer position.",
        "company_id": "gofore",
        "forbidden_company_id": "etteplan",
    },
    {
        "name": "Etteplan cannot retrieve Gofore",
        "question": "Tell me about Gofore and the Senior AI Engineer position.",
        "company_id": "etteplan",
        "forbidden_company_id": "gofore",
    },
]

def run_cross_company_isolation_tests():
    print("\n" + "=" * 70)
    print("CROSS-COMPANY ISOLATION")
    print("=" * 70)

    passed = 0

    for number, test in enumerate(ISOLATION_TESTS, start=1):
        print(f"\nIsolation Test {number}: {test['name']}")
        print(f"Question: {test['question']}")

        results = hybrid_search(
            test["question"],
            company_id=test["company_id"],
            top_k=10,
        )

        isolation_pass = all(
            result["company_id"] != test["forbidden_company_id"]
            for result in results
        )

        if isolation_pass:
            passed += 1

        for index, result in enumerate(results, start=1):
            print(
                f"  #{index} "
                f"{result['@search.score']:.4f} | "
                f"{result['company_id']} | "
                f"{result['document_type']} | "
                f"{result['title']}"
            )

        print(
            f"Foreign-company isolation: "
            f"{'PASS' if isolation_pass else 'FAIL'}"
        )

    total = len(ISOLATION_TESTS)
    accuracy = passed / total * 100 if total else 0

    print("\n" + "-" * 70)
    print(
        f"Cross-company isolation: "
        f"{passed}/{total} ({accuracy:.1f}%)"
    )


def run_evaluation():
    total = len(TEST_CASES)
    top1_correct = 0
    topk_correct = 0
    isolation_correct = 0
    global_tests = 0
    global_correct = 0

    print("\nWORK APPLICATION ASSISTANT")
    print("RAG Retrieval Evaluation")
    print("=" * 70)

    for number, test in enumerate(TEST_CASES, start=1):
        print(f"\nTest {number}: {test['name']}")
        print(f"Question: {test['question']}")

        results = hybrid_search(
            test["question"],
            company_id=test["company_id"],
            top_k=4,
            document_types=test["document_types"],
        )

        if not results:
            print("FAIL - No results returned")
            continue

        top_result = results[0]

        top1_pass = (
            top_result["document_type"]
            in test["expected_top1_types"]
        )

        if top1_pass:
            top1_correct += 1

        topk_pass = any(
            result["document_type"]
            in test["expected_top1_types"]
            for result in results
        )

        if topk_pass:
            topk_correct += 1

        isolation_pass = all(
            result["company_id"]
            in test["allowed_company_ids"]
            for result in results
        )

        if isolation_pass:
            isolation_correct += 1

        expects_global = "global" in test["allowed_company_ids"]
        global_pass = None

        if expects_global:
            global_tests += 1

            global_pass = any(
                result["company_id"] == "global"
                for result in results
            )

            if global_pass:
                global_correct += 1

        for index, result in enumerate(results, start=1):
            print(
                f"  #{index} "
                f"{result['@search.score']:.4f} | "
                f"{result['company_id']} | "
                f"{result['document_type']} | "
                f"{result['title']}"
            )

        print(
            f"Top-1 routing: "
            f"{'PASS' if top1_pass else 'FAIL'}"
        )

        print(
            f"Top-{len(results)} retrieval: "
            f"{'PASS' if topk_pass else 'FAIL'}"
        )

        print(
            f"Company isolation: "
            f"{'PASS' if isolation_pass else 'FAIL'}"
        )

        if global_pass is not None:
            print(
                f"Global retrieval: "
                f"{'PASS' if global_pass else 'FAIL'}"
            )

    print("\n" + "=" * 70)
    print("FINAL METRICS")
    print("=" * 70)

    top1_accuracy = (
        top1_correct / total * 100
        if total else 0
    )

    topk_accuracy = (
        topk_correct / total * 100
        if total else 0
    )

    isolation_accuracy = (
        isolation_correct / total * 100
        if total else 0
    )

    global_accuracy = (
        global_correct / global_tests * 100
        if global_tests else 0
    )

    print(
        f"Top-1 routing accuracy: "
        f"{top1_correct}/{total} "
        f"({top1_accuracy:.1f}%)"
    )

    print(
        f"Top-k retrieval accuracy: "
        f"{topk_correct}/{total} "
        f"({topk_accuracy:.1f}%)"
    )

    print(
        f"Company isolation: "
        f"{isolation_correct}/{total} "
        f"({isolation_accuracy:.1f}%)"
    )

    print(
        f"Global applicant retrieval: "
        f"{global_correct}/{global_tests} "
        f"({global_accuracy:.1f}%)"
    )


if __name__ == "__main__":
    run_evaluation()
    run_cross_company_isolation_tests()