from tools import TOOLS, choose_tool, ask_ai

print("=" * 40)
print("      My First AI Agent")
print("=" * 40)
print("\nI can tell the time, roll a dice, create a password,")
print("or answer questions. Type 'quit' to exit.")

while True:

    user_input = input("\nYou : ").strip()

    if user_input == "":
        continue

    if user_input.lower() == "quit":
        print("\nAI  : Goodbye! Have a great day.")
        break

    try:
        # Step 1 - PLAN: the AI decides which tool is needed
        tool = choose_tool(user_input)
        print(f"\n[Plan] tool chosen: {tool}")

        # Step 2 - ACT: run the tool, or just answer the question
        if tool is None:
            print("\nAI :", ask_ai(user_input))
        else:
            result = TOOLS[tool]()  
            print("\nAI :", result)

    except Exception as error:
        print("\nSomething went wrong:", error)
