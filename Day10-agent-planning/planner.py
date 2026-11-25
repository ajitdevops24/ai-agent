from openai import OpenAI
from dotenv import load_dotenv
import json
import os

# Load configuration
load_dotenv()

# Create AI client (this talks to Ollama)
client = OpenAI(
    base_url=os.getenv("BASE_URL"),
    api_key=os.getenv("API_KEY")
)

# A plan never has more tasks than this
MAX_TASKS = 3


def get_schema(tool):
    """Get the input schema of a tool (the attribute name differs between FastMCP versions)."""

    schema = getattr(tool, "input_schema", None) or getattr(tool, "inputSchema", None)

    return schema or {}


def describe_tools(tools):
    """Turn the tools found on the server into text the AI can read."""

    lines = []

    for tool in tools:
        arguments = get_schema(tool).get("properties", {})
        lines.append(f"- {tool.name}: {tool.description}\n  Arguments: {json.dumps(arguments)}")

    return "\n".join(lines)


def ask_model(prompt):
    """Send one prompt to the model and return its reply without any <think> part."""

    response = client.chat.completions.create(
        model=os.getenv("MODEL"),
        messages=[{"role": "user", "content": prompt + "\n/no_think"}],
        temperature=0
    )

    return response.choices[0].message.content.split("</think>")[-1].strip()


def extract_json(text):
    """Find the JSON object inside the model's reply."""

    start = text.find("{")
    end = text.rfind("}")

    if start == -1 or end == -1:
        raise ValueError(f"The AI did not return JSON. It said: {text!r}")

    return json.loads(text[start:end + 1])


def make_plan(goal, tools):
    """STEP 1 - PLAN: break the goal into a short list of tasks."""

    prompt = f"""You are a planner. Break the goal into a short list of tasks.

Goal:
{goal}

Available tools:
{describe_tools(tools)}

Rules:
1. Write at most {MAX_TASKS} tasks, in the order they should be done.
2. 2. Write each task as a short sentence in plain words (for example "Read the app log and look for errors"), not as a tool name.
3. Do not add a task for writing the final answer. That happens automatically.
4. Reply with one task per line. No numbers, no explanations.
5. If the goal mentions slowness or errors, include a task to check the latest deployment.
"""

    reply = ask_model(prompt)

    tasks = []

    for line in reply.splitlines():
        text = line.strip().lstrip("-*0123456789.) ").strip()

        if text and not text.endswith(":"):
            tasks.append(text)

    if not tasks:
        raise ValueError("The planner did not return any tasks.")

    return tasks[:MAX_TASKS]


def format_progress(state):
    """Tasks that are done, with what they returned."""

    lines = []

    for number, task in enumerate(state["tasks"], start=1):
        if task["status"] == "done":
            lines.append(f"Task {number} ({task['text']}) returned: {task['result']}")

    return "\n".join(lines) if lines else "Nothing done yet."


def choose_action(state, task, tools):
    """STEP 2 - DECIDE: choose the tool for ONE task. Return (action, arguments)."""

    retry_note = ""

    if task["tries"] > 0:
        retry_note = (
            f"\nA previous attempt at this task failed with: {task['result']}"
            f"\nTry something different."
        )

    prompt = f"""You are an AI agent. Choose the tool for ONE task.

Overall goal:
{state["goal"]}

Results so far:
{format_progress(state)}

Current task:
{task["text"]}{retry_note}

Available tools:
{describe_tools(tools)}

Rules:
1. Choose the one tool that completes the current task.
2. Use the results so far to fill in the arguments (for example, a file name).
3. If no tool is needed, use "none" as the action.
4. Reply with ONLY a JSON object in this format:
{{"action": "tool_name", "arguments": {{"argument_name": "value"}}}}
"""

    plan = extract_json(ask_model(prompt))

    action = plan.get("action")
    arguments = plan.get("arguments") or {}

    if action in (None, "none"):
        return "none", {}

    # Check the plan before it is used
    tool = None

    for candidate in tools:
        if candidate.name == action:
            tool = candidate

    if tool is None:
        raise ValueError(f"The AI chose an unknown tool: {action!r}")

    if not isinstance(arguments, dict):
        raise ValueError("The tool arguments must be a JSON object.")

    allowed = get_schema(tool).get("properties", {})
    unexpected = set(arguments) - set(allowed)

    if unexpected:
        raise ValueError(f"Unsupported arguments for {action}: {', '.join(sorted(unexpected))}")

    return action, arguments


def write_final_answer(state):
    """LAST STEP: turn the finished plan into a short answer."""

    lines = []

    for number, task in enumerate(state["tasks"], start=1):
        result = task["result"] or "not done"
        lines.append(f"Task {number}: {task['text']} [{task['status']}]\n  Result: {result}")

    prompt = f"""The user's goal:
{state["goal"]}

Tasks and results:
{chr(10).join(lines)}

Write a short, clear answer to the goal using ONLY the results above.
If a task failed or was not done, say so.
If something looks wrong (errors, warnings, high usage), say what it is and why.
Do not invent facts."""

    return ask_model(prompt)
