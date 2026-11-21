from fastmcp import Client
from planner import plan_next_step, write_final_answer
import asyncio

# The agent stops after this many steps, so it can never run forever
MAX_STEPS = 3


def result_to_text(result):
    """Get the text out of the result that the MCP server sends back."""

    blocks = getattr(result, "content", result)

    return "".join(block.text for block in blocks if hasattr(block, "text"))


def already_done(state, action, arguments):
    """True if the agent already did exactly this step."""

    for step in state["steps"]:
        if step["action"] == action and step["arguments"] == arguments:
            return True

    return False

async def run_agent(goal, mcp, tools):
    """Plan, act and remember, again and again, until the goal is done."""

    # The state is the agent's notebook: the goal and every step so far
    state = {"goal": goal, "steps": []}

    stop_reason = f"reached the limit of {MAX_STEPS} steps"

    for number in range(1, MAX_STEPS + 1):

        # THINK: the AI chooses the next step, using the notebook
        action, arguments = plan_next_step(state, tools)
        print(f"\n[Step {number}] plan: {action} {arguments}")

        if action == "FINISH":
            stop_reason = "the planner has enough information"
            break

        # Safety: never repeat the same step
        if already_done(state, action, arguments):
            stop_reason = "the planner repeated a step"
            break

        # ACT: ask the MCP server to run the tool
        try:
            result = await mcp.call_tool(action, arguments)
            text = result_to_text(result)[:1500]
        except Exception as error:
            text = f"Tool error: {error}"

        print(f"[Step {number}] result: {text[:300]}")

        # REMEMBER: write the result in the notebook
        state["steps"].append(
            {"action": action, "arguments": arguments, "result": text}
        )

    print(f"\n[Stop] {stop_reason}")

    # Last step: turn the notebook into an answer
    return write_final_answer(state)


async def main():

    # Connect to the MCP server (this starts server.py in the background)
    async with Client("server.py") as mcp:

        tools = await mcp.list_tools()

        print("=" * 40)
        print("      My Autonomous DevOps Agent")
        print("=" * 40)
        print("\nTools found on the MCP server:")

        for tool in tools:
            print(f"  - {tool.name}: {tool.description}")

        print("\nGive me a goal. Type 'quit' to exit.")

        while True:

            goal = (await asyncio.to_thread(input, "\nGoal : ")).strip()

            if goal == "":
                continue

            if goal.lower() == "quit":
                print("\nAI  : Goodbye! Have a great day.")
                break

            try:
                answer = await run_agent(goal, mcp, tools)
                print("\nFinal answer:\n")
                print(answer)
            except Exception as error:
                print("\nSomething went wrong:", error)


if __name__ == "__main__":
    asyncio.run(main())
