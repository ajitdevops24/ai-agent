from fastmcp import Client
from planner import make_plan, choose_action, write_final_answer
import asyncio

# The agent stops after this many steps (one step = one attempt at a task).
# 3 tasks at most, plus 1 spare step for a retry.
MAX_STEPS = 4


def result_to_text(result):
    """Get the text out of the result that the MCP server sends back."""

    blocks = getattr(result, "content", result)

    return "".join(block.text for block in blocks if hasattr(block, "text"))


def is_error(text):
    """True if a result is an error message."""

    return text.startswith("ERROR")


def next_pending_task(state):
    """Return the first task that is not finished yet, or None."""

    for task in state["tasks"]:
        if task["status"] == "pending":
            return task

    return None


def record_attempt(task, text):
    """Save what happened and update the task status. This is the retry rule."""

    task["tries"] += 1
    task["result"] = text

    if not is_error(text):
        task["status"] = "done"
    elif task["tries"] >= 2:
        task["status"] = "failed"
    # otherwise the task stays "pending" and is tried again


def show_plan(state):
    """Print the plan with the status of every task."""

    print("\nPlan:")

    for number, task in enumerate(state["tasks"], start=1):
        print(f"  {number}. [{task['status']}] {task['text']}")


async def run_agent(goal, mcp, tools):
    """Plan first, then work through the tasks one by one."""

    # The state is the agent's notebook: the goal and the plan
    state = {"goal": goal, "tasks": []}

    # PLAN: the AI breaks the goal into a short list of tasks
    for text in make_plan(goal, tools):
        state["tasks"].append(
            {"text": text, "status": "pending", "tries": 0, "result": ""}
        )

    show_plan(state)

    for number in range(1, MAX_STEPS + 1):

        # The CODE picks the next task, not the AI
        task = next_pending_task(state)

        if task is None:
            break

        print(f"\n[Step {number}] task: {task['text']}")

        # DECIDE: the AI chooses the tool for this one task
        try:
            action, arguments = choose_action(state, task, tools)
        except Exception as error:
            # A bad reply from the AI counts as a failed attempt
            record_attempt(task, f"ERROR: bad plan from the AI - {error}")
            print(f"[Step {number}] {task['result']}")
            continue

        print(f"[Step {number}] tool: {action} {arguments}")

        if action == "none":
            task["status"] = "done"
            task["result"] = "No tool needed."
            continue

        # ACT: ask the MCP server to run the tool
        try:
            result = await mcp.call_tool(action, arguments)
            text = result_to_text(result)[:1500]
        except Exception as error:
            text = f"ERROR: tool failed - {error}"

        # UPDATE: write what happened in the plan
        record_attempt(task, text)

        print(f"[Step {number}] result: {text[:300]}")
        print(f"[Step {number}] task status: {task['status']}")

    if next_pending_task(state) is None:
        print("\n[Stop] all tasks are finished")
    else:
        print(f"\n[Stop] reached the limit of {MAX_STEPS} steps")

    show_plan(state)

    print("\nWriting the final answer, this can take a minute on a CPU...")

    return write_final_answer(state)


async def main():

    # Connect to the MCP server (this starts server.py in the background)
    async with Client("server.py") as mcp:

        tools = await mcp.list_tools()

        print("=" * 40)
        print("      My Planning DevOps Agent")
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
