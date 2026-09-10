from rag import ask_rag


question = (
    "My colleague needs to see what I'm doing on my computer. "
    "How can I show it to them?"
)

result = ask_rag(question)

print("\nQUESTION")
print(question)

print("\nANSWER")
print(result["answer"])

print("\nSOURCES")

for source in result["sources"]:
    print(f"- {source['product']}: {source['title']}")
    print(f"  {source['url']}")