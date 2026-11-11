
from tools import read_file, make_prompt, ask_ai

print("=" * 40)
print("      My AI Document Assistant")
print("=" * 40)
print("\nCommands:")
print("  summarize <file>")
print("  explain <file>")
print("  ask <file> <question>")
print("  quit")

while True:

    user_input = input("\nYou : ").strip()

    if user_input == "":
        continue

    if user_input.lower() == "quit":
        print("\nAI  : Goodbye! Have a great day.")
        break

    # Split into: command, filename, question
    words = user_input.split(maxsplit=2)
    command = words[0].lower()

    # Check the command
    if command not in ("summarize", "explain", "ask"):
        print("\nI didn't understand. Use: summarize, explain, ask or quit.")
        continue

    # Check the arguments
    if command == "ask" and len(words) < 3:
        print("\nUsage: ask <file> <question>")
        continue

    if command != "ask" and len(words) != 2:
        print(f"\nUsage: {command} <file>")
        continue

    # Read the file
    content = read_file(words[1])

    if content is None:
        print("\nFile not found in the data folder:", words[1])
        continue

    # Build the prompt and ask the model
    question = words[2] if command == "ask" else ""
    prompt = make_prompt(command, content, question)

    print("\nAI :", ask_ai(prompt))
