from search.vector_search import hybrid_search


TEST_CASES = [
    {
        "question": "How do I share my screen with a colleague?",
        "expected_product": "Teams",
        "expected_category": "Screen Sharing",
    },
    {
        "question": "How can I join a Teams meeting from an invitation?",
        "expected_product": "Teams",
        "expected_category": "Joining Meetings",
    },
    {
        "question": "How can I reduce the number of Teams notifications?",
        "expected_product": "Teams",
        "expected_category": "Notifications",
    },
    {
        "question": "How do I schedule an online meeting?",
        "expected_product": "Teams",
        "expected_category": "Meetings",
    },
    {
        "question": "How do I tell people automatically that I am away from work?",
        "expected_product": "Outlook",
        "expected_category": "Automatic Replies",
    },
    {
        "question": "How can I add my contact information to the bottom of emails?",
        "expected_product": "Outlook",
        "expected_category": "Email Signatures",
    },
    {
        "question": "How can I automatically move emails from someone into a folder?",
        "expected_product": "Outlook",
        "expected_category": "Inbox Rules",
    },
    {
        "question": "How can I find an old email from a specific person?",
        "expected_product": "Outlook",
        "expected_category": "Email Search",
    },
    {
        "question": "How can I share a OneDrive file with another person?",
        "expected_product": "OneDrive",
        "expected_category": "File Sharing",
    },
    {
        "question": "Why are my OneDrive files not updating?",
        "expected_product": "OneDrive",
        "expected_category": "Sync Troubleshooting",
    },
    {
        "question": "How can I recover a file I accidentally deleted?",
        "expected_product": "OneDrive",
        "expected_category": "File Recovery",
    },
    {
        "question": "How can I access my OneDrive files from my computer?",
        "expected_product": "OneDrive",
        "expected_category": "File Synchronization",
    },
]


def is_correct(result, test):
    return (
        result["product"] == test["expected_product"]
        and result["category"] == test["expected_category"]
    )


def evaluate():
    top1_correct = 0
    top2_correct = 0

    total = len(TEST_CASES)

    print("\nRAG RETRIEVAL EVALUATION")
    print("=" * 70)

    for index, test in enumerate(TEST_CASES, start=1):

        results = hybrid_search(
            test["question"],
            top_k=2
        )

        top1_pass = is_correct(results[0], test)

        top2_pass = any(
            is_correct(result, test)
            for result in results
        )

        if top1_pass:
            top1_correct += 1

        if top2_pass:
            top2_correct += 1

        print(f"\nTest #{index}")
        print(f"Question: {test['question']}")

        print(
            f"Expected: "
            f"{test['expected_product']} / "
            f"{test['expected_category']}"
        )

        print("\nRetrieved results:")

        for rank, result in enumerate(results, start=1):

            print(
                f"  #{rank}: "
                f"{result['product']} / "
                f"{result['category']} "
                f"(score: {result['@search.score']:.4f})"
            )

        print(
            f"\nTop-1: "
            f"{'PASS' if top1_pass else 'FAIL'}"
        )

        print(
            f"Top-2: "
            f"{'PASS' if top2_pass else 'FAIL'}"
        )

    top1_accuracy = top1_correct / total * 100
    top2_accuracy = top2_correct / total * 100

    print("\n" + "=" * 70)
    print("EVALUATION RESULTS")
    print("=" * 70)

    print(
        f"Top-1 Accuracy: "
        f"{top1_correct}/{total} "
        f"({top1_accuracy:.1f}%)"
    )

    print(
        f"Top-2 Accuracy: "
        f"{top2_correct}/{total} "
        f"({top2_accuracy:.1f}%)"
    )


if __name__ == "__main__":
    evaluate()