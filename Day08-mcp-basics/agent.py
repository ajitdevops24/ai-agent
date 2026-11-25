from openai import OpenAI
from dotenv import load_dotenv
from fastmcp import Client
import asyncio
import json
import os

# Load configuration
load_dotenv()

# Create AI client (this talks to Ollama)
client = OpenAI(
    base_url=os.getenv("BASE_URL"),
    api_key=os.getenv("API_KEY")
)


def describe_tools(tools):
    """Describe each server tool and its arguments for the planner."""

    lines = []

    for tool in tools:
        schema = tool.input_schema
        lines.append(
            f"- {tool.name}: {tool.description}\n"
            f"  Input schema: {json.dumps(schema)}"
        )

    return "\n".join(lines)


def choose_tool(user_request, tools):
    """Ask the AI which tool and arguments are needed, or return no tool."""

    planner_prompt = f"""You are a planner. Choose the right tool for the user request.

Available tools:
{describe_tools(tools)}

Return only a JSON object in this format:
{{"tool": "tool_name", "arguments": {{"argument_name": "value"}}}}

If no tool is needed, return:
{{"tool": null, "arguments": {{}}}}

Use only a listed tool and its arguments. Match argument types from its input schema.

User request: {user_request}
/no_think"""
    # "/no_think" makes qwen3 skip its thinking part, which is faster.

    response = client.chat.completions.create(
        model=os.getenv("MODEL"),
        messages=[{"role": "user", "content": planner_prompt}],
        temperature=0
    )

    reply = response.choices[0].message.content

    if reply is None:
        raise ValueError("The model returned an empty tool plan.")

    plan = json.loads(reply)
    if not isinstance(plan, dict):
        raise ValueError("The model's tool plan must be a JSON object.")

    tool_name = plan.get("tool")
    arguments = plan.get("arguments", {})

    if tool_name is None:
        return None, {}
    if not isinstance(tool_name, str) or not any(tool.name == tool_name for tool in tools):
        raise ValueError(f"The model selected an unknown tool: {tool_name!r}")
    if not isinstance(arguments, dict):
        raise ValueError("The model's tool arguments must be a JSON object.")

    selected_tool = next(tool for tool in tools if tool.name == tool_name)
    schema = selected_tool.input_schema
    allowed_arguments = schema.get("properties", {}) if isinstance(schema, dict) else {}
    unexpected_arguments = arguments.keys() - allowed_arguments.keys()
    if unexpected_arguments:
        raise ValueError(
            f"The model returned unsupported arguments for {tool_name}: "
            f"{', '.join(sorted(unexpected_arguments))}"
        )

    return tool_name, arguments


def ask_ai(question):
    """Normal answer from the model, when no tool is needed."""

    response = client.chat.completions.create(
        model=os.getenv("MODEL"),
        messages=[{"role": "user", "content": question + " /no_think"}]
    )

    return response.choices[0].message.content.strip()


def result_to_text(result):
    """Get the text out of the result that the MCP server sends back."""

    blocks = getattr(result, "content", result)

    return "".join(block.text for block in blocks if hasattr(block, "text"))


async def main():

    # Step 1: connect to the MCP server (this starts server.py in the background)
    async with Client(Path(__file__).resolve().with_name("server.py")) as mcp:

        # Step 2: discover the tools the server offers
        tools = await mcp.list_tools()

        print("=" * 40)
        print("      My First MCP Agent")
        print("=" * 40)
        print("\nTools found on the MCP server:")

        for tool in tools:
            print(f"  - {tool.name}: {tool.description}")

        print("\nType 'quit' to exit.")

        while True:

            # input() waits for the keyboard; to_thread keeps the connection alive meanwhile
            user_input = (await asyncio.to_thread(input, "\nYou : ")).strip()

            if user_input == "":
                continue

            if user_input.lower() == "quit":
                print("\nAI  : Goodbye! Have a great day.")
                break

            try:
                # Step 3 - PLAN: the AI picks a tool from the discovered list
                tool_name, arguments = choose_tool(user_input, tools)
                print(f"\n[Plan] tool chosen: {tool_name}, arguments: {arguments}")

                # Step 4 - ACT: ask the MCP server to run it, or answer normally
                if tool_name is None:
                    print("\nAI :", ask_ai(user_input))
                else:
                    result = await mcp.call_tool(tool_name, arguments)
                    print("\nAI :", result_to_text(result))

            except Exception as error:
                print("\nSomething went wrong:", error)


if __name__ == "__main__":
    asyncio.run(main())
