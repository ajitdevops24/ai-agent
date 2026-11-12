from tools import (
    load_documents,
    create_embedding,
    rank_documents,
    make_prompt,
    ask_ai
)

print("=" * 40)
print("      My DevOps Knowledge Assistant")
print("=" * 40)

# Step 1: read the documents
documents = load_documents()

if not documents:
    print("\nNo .txt files found in the knowledge folder.")
    exit()

# Step 2: turn every document into an embedding (done once, at startup)
print("\nLoading knowledge base...")

document_embeddings = {}

try:
    for filename, content in documents.items():
        document_embeddings[filename] = create_embedding(content)
except Exception as error:
    print("Could not create embeddings. Is Ollama running and is nomic-embed-text pulled?")
    print("Details:", error)
    exit()

print(f"Ready. {len(documents)} documents loaded. Type 'quit' to exit.")

# Step 3: answer questions
while True:

    user_input = input("\nYou : ").strip()

    if user_input == "":
        continue

    if user_input.lower() == "quit":
        print("\nAI  : Goodbye! Have a great day.")
        break

    try:
        # Turn the question into an embedding and rank all documents
        question_embedding = create_embedding(user_input)
        ranked = rank_documents(question_embedding, document_embeddings)

        print("\nSearch scores:")
        for score, filename in ranked:
            print(f"  {score:.2f}  {filename}")

        # Use the best document as context for the model
        best_score, best_file = ranked[0]
        if best_score < 0.40:
            print("\nAI : No relevant document found.")
            continue
        prompt = make_prompt(documents[best_file], user_input)

        print("\nAI :", ask_ai(prompt))
        print(f"\n(Source: {best_file})")

    except Exception as error:
        print("\nSomething went wrong:", error)
